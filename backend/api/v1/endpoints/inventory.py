from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend import models, schemas
from backend.api import deps

router = APIRouter()


def _assert_inventory_ownership(inv: models.BuildingInventory, current_user: models.User):
    if current_user.role in ("superadmin", "manager"):
        return
    my_building_ids = {b.id for b in current_user.assigned_buildings}
    if inv.building_id not in my_building_ids:
        raise HTTPException(status_code=403, detail="Not enough privileges for this inventory item")


@router.get("/", response_model=List[schemas.inventory.BuildingInventoryItem])
def list_inventory(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    building_id: int | None = None,
) -> Any:
    """List building inventory items visible to the current user."""
    query = db.query(models.BuildingInventory)
    if current_user.role in ("superadmin", "manager"):
        if building_id:
            query = query.filter(models.BuildingInventory.building_id == building_id)
    else:
        my_building_ids = [b.id for b in current_user.assigned_buildings]
        query = query.filter(models.BuildingInventory.building_id.in_(my_building_ids))
        if building_id:
            query = query.filter(models.BuildingInventory.building_id == building_id)

    return query.order_by(models.BuildingInventory.last_updated.desc()).all()


@router.get("/{id}", response_model=schemas.inventory.BuildingInventoryItem)
def get_inventory_item(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get a single building inventory item."""
    inv = db.query(models.BuildingInventory).filter(models.BuildingInventory.id == id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    _assert_inventory_ownership(inv, current_user)
    return inv


@router.post("/", response_model=schemas.inventory.BuildingInventoryItem)
def add_inventory_item(
    *,
    db: Session = Depends(deps.get_db),
    inv_in: schemas.inventory.AddInventoryRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Add a product to a building's local inventory."""
    if current_user.role not in ("superadmin", "manager"):
        my_building_ids = {b.id for b in current_user.assigned_buildings}
        if inv_in.building_id not in my_building_ids:
            raise HTTPException(status_code=403, detail="Not enough privileges for this building")

    if inv_in.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    existing = db.query(models.BuildingInventory).filter_by(
        building_id=inv_in.building_id,
        product_id=inv_in.product_id
    ).first()

    if existing:
        existing.quantity += inv_in.quantity
        db.commit()
        db.refresh(existing)
        return existing

    new_inv = models.BuildingInventory(
        building_id=inv_in.building_id,
        product_id=inv_in.product_id,
        quantity=inv_in.quantity
    )
    db.add(new_inv)
    db.commit()
    db.refresh(new_inv)
    return new_inv


@router.post("/{id}/consume", response_model=schemas.inventory.BuildingInventoryItem)
def consume_inventory(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    consume_in: schemas.inventory.ConsumeInventoryRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Report consumption of a building inventory item."""
    inv = db.query(models.BuildingInventory).filter(models.BuildingInventory.id == id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    _assert_inventory_ownership(inv, current_user)

    quantity = max(1, consume_in.quantity)
    quantity = min(quantity, inv.quantity)

    if inv.quantity > 0:
        inv.quantity -= quantity
        db.add(models.ConsumptionLog(
            building_id=inv.building_id,
            product_id=inv.product_id,
            reported_by_id=current_user.id,
            quantity_consumed=quantity
        ))
        db.commit()
        db.refresh(inv)

    return inv


@router.post("/{id}/adjust", response_model=schemas.inventory.BuildingInventoryItem)
def adjust_inventory(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    adjust_in: schemas.inventory.AdjustInventoryRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Manually set the quantity of a building inventory item."""
    inv = db.query(models.BuildingInventory).filter(models.BuildingInventory.id == id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    _assert_inventory_ownership(inv, current_user)

    if adjust_in.quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")

    inv.quantity = adjust_in.quantity
    db.commit()
    db.refresh(inv)
    return inv
