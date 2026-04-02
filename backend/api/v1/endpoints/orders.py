from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, selectinload
from backend import models, schemas
from backend.api import deps

router = APIRouter()


def _assert_order_ownership(order: models.Order, current_user: models.User):
    """Raise 403 if the current user has no right to touch this order."""
    if current_user.role in ("superadmin", "manager"):
        return
    my_building_ids = {b.id for b in current_user.assigned_buildings}
    if order.building_id not in my_building_ids:
        raise HTTPException(status_code=403, detail="Not enough privileges for this order")


@router.get("/", response_model=List[schemas.order.OrderDetail])
def read_orders(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    building_id: Optional[int] = None,
) -> Any:
    """List orders. Admin sees their buildings; superadmin/manager sees all."""
    if current_user.role in ("superadmin", "manager"):
        query = db.query(models.Order).options(
            selectinload(models.Order.items).joinedload(models.OrderItem.product),
            joinedload(models.Order.building),
            joinedload(models.Order.created_by),
        )
    else:
        my_building_ids = [b.id for b in current_user.assigned_buildings]
        query = db.query(models.Order).options(
            selectinload(models.Order.items).joinedload(models.OrderItem.product),
            joinedload(models.Order.building),
            joinedload(models.Order.created_by),
        ).filter(models.Order.building_id.in_(my_building_ids))

    if status:
        query = query.filter(models.Order.status == status)
    if building_id:
        query = query.filter(models.Order.building_id == building_id)

    return query.order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/consumption-report", response_model=List[schemas.order.ConsumptionReportRow])
def consumption_report(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    building_id: Optional[int] = None,
) -> Any:
    """Consumption logs grouped by building and product."""
    if current_user.role in ("superadmin", "manager"):
        building_ids = [b.id for b in db.query(models.Building).all()]
    else:
        building_ids = [b.id for b in current_user.assigned_buildings]

    q = db.query(
        models.Building.name.label("building_name"),
        models.Product.name.label("product_name"),
        models.Product.unit.label("unit"),
        models.Product.imagen_url.label("imagen_url"),
        func.sum(models.ConsumptionLog.quantity_consumed).label("total_consumed"),
        func.count(models.ConsumptionLog.id).label("events"),
        func.max(models.ConsumptionLog.reported_at).label("last_reported"),
    ).join(models.Building, models.ConsumptionLog.building_id == models.Building.id
    ).join(models.Product, models.ConsumptionLog.product_id == models.Product.id
    ).filter(models.ConsumptionLog.building_id.in_(building_ids))

    if building_id and building_id in building_ids:
        q = q.filter(models.ConsumptionLog.building_id == building_id)

    rows = q.group_by(
        models.Building.name, models.Product.name, models.Product.unit, models.Product.imagen_url
    ).order_by(func.sum(models.ConsumptionLog.quantity_consumed).desc()).all()

    return [
        schemas.order.ConsumptionReportRow(
            building_name=r.building_name,
            product_name=r.product_name,
            unit=r.unit,
            imagen_url=r.imagen_url,
            total_consumed=r.total_consumed,
            events=r.events,
            last_reported=r.last_reported,
        )
        for r in rows
    ]


@router.get("/{id}", response_model=schemas.order.OrderDetail)
def read_order(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get full order details."""
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _assert_order_ownership(order, current_user)
    return order


@router.post("/", response_model=schemas.order.Order)
def create_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: schemas.order.OrderCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new draft order for a building."""
    if current_user.role not in ("superadmin", "manager"):
        building = db.query(models.Building).filter(
            models.Building.id == order_in.building_id,
            models.Building.admin_id == current_user.id
        ).first()
        if not building:
            raise HTTPException(status_code=403, detail="Not enough privileges for this building")

    existing_draft = db.query(models.Order).filter(
        models.Order.building_id == order_in.building_id,
        models.Order.status == "draft"
    ).first()
    if existing_draft:
        return existing_draft

    order = models.Order(
        building_id=order_in.building_id,
        created_by_id=current_user.id,
        status="draft"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{id}/items", response_model=schemas.order.OrderItem)
def add_order_item(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    item_in: schemas.order.OrderItemCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Add item to order (draft only). Snapshots product name and price."""
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "draft":
        raise HTTPException(status_code=400, detail="Order is not in draft status")
    _assert_order_ownership(order, current_user)

    product = db.query(models.Product).filter(models.Product.id == item_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing_item = db.query(models.OrderItem).filter(
        models.OrderItem.order_id == id,
        models.OrderItem.product_id == item_in.product_id
    ).first()

    if existing_item:
        existing_item.quantity += item_in.quantity
        existing_item.precio_unitario = product.precio or 0.0
        existing_item.nombre_producto_snapshot = product.name
        db.commit()
        db.refresh(existing_item)
        return existing_item

    new_item = models.OrderItem(
        order_id=id,
        product_id=product.id,
        quantity=item_in.quantity,
        nombre_producto_snapshot=product.name,
        precio_unitario=product.precio or 0.0,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.delete("/{id}/items/{item_id}")
def remove_order_item(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    item_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Remove an item from a draft order."""
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "draft":
        raise HTTPException(status_code=400, detail="Order is not in draft status")
    _assert_order_ownership(order, current_user)

    item = db.query(models.OrderItem).filter(
        models.OrderItem.id == item_id,
        models.OrderItem.order_id == id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item removed"}


@router.post("/{id}/items/{item_id}/update", response_model=schemas.order.OrderItem)
def update_order_item(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    item_id: int,
    item_in: schemas.order.OrderItemUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Update quantity of an existing item in a draft order."""
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "draft":
        raise HTTPException(status_code=400, detail="Order is not in draft status")
    _assert_order_ownership(order, current_user)

    item = db.query(models.OrderItem).filter(
        models.OrderItem.id == item_id,
        models.OrderItem.order_id == id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item_in.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    item.quantity = item_in.quantity
    db.commit()
    db.refresh(item)
    return item


@router.post("/{id}/submit", response_model=schemas.order.Order)
def submit_order(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Submit the order (draft → submitted)."""
    order = db.query(models.Order).filter(models.Order.id == id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft orders can be submitted")
    if not order.items:
        raise HTTPException(status_code=400, detail="Cannot submit empty order")
    _assert_order_ownership(order, current_user)

    order.status = "submitted"
    db.commit()
    db.refresh(order)
    return order


@router.post("/{id}/reopen", response_model=schemas.order.Order)
def reopen_order(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Reopen a submitted order back to draft."""
    order = db.query(models.Order).filter(models.Order.id == id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "submitted":
        raise HTTPException(status_code=400, detail="Only submitted orders can be reopened")
    _assert_order_ownership(order, current_user)

    order.status = "draft"
    db.commit()
    db.refresh(order)
    return order


@router.post("/{id}/cancel", response_model=schemas.order.Order)
def cancel_order(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Cancel a draft or submitted order."""
    order = db.query(models.Order).filter(models.Order.id == id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in ("draft", "submitted"):
        raise HTTPException(status_code=400, detail="Only draft or submitted orders can be cancelled")
    _assert_order_ownership(order, current_user)

    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return order


@router.post("/{id}/receive", response_model=schemas.order.Order)
def receive_order(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Confirm receipt of a dispatched order and update building inventory."""
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "dispatched":
        raise HTTPException(status_code=400, detail="Order is not in dispatched status")
    _assert_order_ownership(order, current_user)

    order.status = "delivered"

    for item in order.items:
        local_inv = db.query(models.BuildingInventory).filter_by(
            building_id=order.building_id,
            product_id=item.product_id
        ).first()
        if local_inv:
            local_inv.quantity += item.quantity
        else:
            db.add(models.BuildingInventory(
                building_id=order.building_id,
                product_id=item.product_id,
                quantity=item.quantity
            ))

    db.commit()
    db.refresh(order)
    return order
