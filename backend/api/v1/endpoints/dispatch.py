import io
from datetime import datetime, timezone
from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload
from backend import models, schemas
from backend.api import deps

router = APIRouter()


@router.get("/pending-orders", response_model=List[schemas.order.OrderDetail])
def read_pending_orders(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """List all submitted orders ready for consolidation."""
    orders = db.query(models.Order).filter(models.Order.status == "submitted").all()
    return orders


@router.post("/consolidate")
def consolidate_orders(
    *,
    db: Session = Depends(deps.get_db),
    order_ids: List[int] = Body(...),
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Consolidate multiple submitted orders into a DispatchBatch."""
    orders = db.query(models.Order).filter(
        models.Order.id.in_(order_ids),
        models.Order.status == "submitted"
    ).all()

    if not orders:
        raise HTTPException(status_code=400, detail="No valid submitted orders found")

    batch = models.DispatchBatch(created_by_id=current_user.id, status="pending")
    db.add(batch)
    db.flush()

    product_totals = {}
    for order in orders:
        batch.orders.append(order)
        order.status = "processing"
        for item in order.items:
            product_totals[item.product_id] = product_totals.get(item.product_id, 0) + item.quantity

    for product_id, total in product_totals.items():
        db.add(models.DispatchBatchItem(
            batch_id=batch.id,
            product_id=product_id,
            total_quantity=total
        ))

    db.commit()
    db.refresh(batch)
    return {"batch_id": batch.id, "orders_count": len(orders)}


@router.get("/history", response_model=schemas.dispatch.DispatchHistoryResponse)
def get_history(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Historial: dispatched batches and all non-draft orders."""
    batches = db.query(models.DispatchBatch).filter(
        models.DispatchBatch.status == "dispatched"
    ).order_by(models.DispatchBatch.created_at.desc()).all()

    orders = db.query(models.Order).filter(
        models.Order.status != "draft"
    ).order_by(models.Order.created_at.desc()).all()

    return {"batches": batches, "orders": orders}


@router.get("/batch/{id}", response_model=schemas.dispatch.DispatchBatchDetail)
def get_batch_detail(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Get full detail of a dispatch batch."""
    batch = db.query(models.DispatchBatch).filter(models.DispatchBatch.id == id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.get("/batch/{id}/picking")
def get_picking_list(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Get the picking list for a pending batch."""
    batch = db.query(models.DispatchBatch).filter(models.DispatchBatch.id == id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {
        "batch_id": batch.id,
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product.name,
                "sku": item.product.sku,
                "unit": item.product.unit,
                "total_quantity": item.total_quantity,
                "stock_actual": item.product.stock_actual,
            }
            for item in batch.items
        ],
    }


@router.post("/batch/{id}/confirm")
def confirm_dispatch(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Confirm dispatch: validate stock, deduct from central, mark orders dispatched."""
    batch = db.query(models.DispatchBatch).options(
        selectinload(models.DispatchBatch.items),
        selectinload(models.DispatchBatch.orders),
    ).filter(models.DispatchBatch.id == id).first()
    if not batch or batch.status != "pending":
        raise HTTPException(status_code=400, detail="Invalid batch or status")

    product_ids = [item.product_id for item in batch.items]
    products = db.query(models.Product).filter(
        models.Product.id.in_(product_ids)
    ).with_for_update().all() if product_ids else []
    products_by_id = {product.id: product for product in products}

    stock_errors = []
    product_updates = []
    inventory_movements = []
    for item in batch.items:
        product = products_by_id.get(item.product_id)
        if product and product.stock_actual < item.total_quantity:
            stock_errors.append(
                f"{product.name}: disponible {product.stock_actual}, requerido {item.total_quantity}"
            )
    if stock_errors:
        raise HTTPException(status_code=400, detail="Stock insuficiente: " + " | ".join(stock_errors))

    for item in batch.items:
        product = products_by_id.get(item.product_id)
        if not product:
            continue
        new_stock = product.stock_actual - item.total_quantity
        product_updates.append({"id": product.id, "stock_actual": new_stock})
        inventory_movements.append(
            {
                "product_id": product.id,
                "quantity": item.total_quantity,
                "movement_type": "out",
                "reference_id": batch.id,
                "created_by_id": current_user.id,
                "created_at": datetime.now(timezone.utc),
            }
        )

    if product_updates:
        db.bulk_update_mappings(models.Product, product_updates)
    if inventory_movements:
        db.bulk_insert_mappings(models.InventoryMovement, inventory_movements)

    batch.status = "dispatched"
    order_ids = [order.id for order in batch.orders]
    if order_ids:
        db.query(models.Order).filter(models.Order.id.in_(order_ids)).update(
            {models.Order.status: "dispatched"},
            synchronize_session=False,
        )

    db.commit()
    return {"message": "Dispatch confirmed and stock updated"}


@router.post("/batch/{id}/reject-order/{order_id}")
def reject_order(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    order_id: int,
    rejection_note: str = "",
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Return an order from a pending batch back to submitted with a rejection note."""
    batch = db.query(models.DispatchBatch).filter(models.DispatchBatch.id == id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.status != "pending":
        raise HTTPException(status_code=400, detail="Can only reject orders from pending batches")

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order not in batch.orders:
        raise HTTPException(status_code=400, detail="Order does not belong to this batch")

    order.rejection_note = rejection_note or "El manager rechazó este pedido sin especificar motivo."
    order.status = "submitted"
    batch.orders.remove(order)

    db.flush()
    for bi in list(batch.items):
        db.delete(bi)

    product_totals = {}
    for o in batch.orders:
        for item in o.items:
            product_totals[item.product_id] = product_totals.get(item.product_id, 0) + item.quantity

    for product_id, total in product_totals.items():
        db.add(models.DispatchBatchItem(batch_id=batch.id, product_id=product_id, total_quantity=total))

    db.commit()
    return {"message": f"Order #{order_id} returned to admin with rejection note"}


@router.get("/batch/{id}/export/consolidated")
def export_batch_consolidated(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Export consolidated picking list as PDF."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    batch = db.query(models.DispatchBatch).filter(models.DispatchBatch.id == id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"Consolidado de Productos - Lote #{id}", styles["Heading1"]),
        Spacer(1, 12),
    ]

    data = [["SKU", "Producto", "Unidad", "Cantidad Total"]]
    for item in batch.items:
        data.append([
            item.product.sku or "N/A",
            Paragraph(item.product.name, styles["Normal"]),
            item.product.unit,
            str(item.total_quantity),
        ])

    table = Table(data, colWidths=[80, 250, 80, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    doc.build(elements)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=consolidado_lote_{id}.pdf"},
    )


@router.get("/batch/{id}/export/buildings")
def export_batch_buildings(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Export per-building picking list as PDF."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    batch = db.query(models.DispatchBatch).filter(models.DispatchBatch.id == id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"Distribución por Edificios - Lote #{id}", styles["Heading1"]),
        Spacer(1, 12),
    ]

    data = [["Edificio", "SKU", "Producto", "Unidad", "Cant.", "Precio", "Total"]]
    for order in batch.orders:
        building_name = order.building.name
        for item in order.items:
            price = item.precio_unitario if item.precio_unitario is not None else item.product.precio
            name = item.nombre_producto_snapshot or item.product.name
            total = item.quantity * price
            data.append([
                Paragraph(building_name, styles["Normal"]),
                item.product.sku or "N/A",
                Paragraph(name, styles["Normal"]),
                item.product.unit,
                str(item.quantity),
                f"S/{price:.2f}",
                f"S/{total:.2f}",
            ])

    table = Table(data, colWidths=[100, 50, 180, 50, 40, 50, 60])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.steelblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (2, 1), (2, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    doc.build(elements)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=distribucion_edificios_lote_{id}.pdf"},
    )


@router.get("/purchases/", response_model=List[schemas.dispatch.PurchaseDetail])
def list_purchases(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """List all purchases."""
    return db.query(models.Purchase).order_by(models.Purchase.purchase_date.desc()).all()


@router.post("/purchases/", response_model=schemas.dispatch.PurchaseDetail)
def create_purchase(
    *,
    db: Session = Depends(deps.get_db),
    purchase_in: schemas.dispatch.PurchaseCreate,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Create a new purchase and update central stock."""
    purchase = models.Purchase(
        supplier=purchase_in.supplier,
        invoice_number=purchase_in.invoice_number,
        purchase_date=purchase_in.purchase_date,
        notes=purchase_in.notes,
        created_by_id=current_user.id,
    )
    db.add(purchase)
    db.flush()

    total_amount = 0.0
    for item_in in purchase_in.items:
        if item_in.quantity <= 0:
            continue
        product = db.query(models.Product).filter(models.Product.id == item_in.product_id).first()
        if not product:
            continue

        db.add(models.PurchaseItem(
            purchase_id=purchase.id,
            product_id=product.id,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
        ))
        product.stock_actual += item_in.quantity
        db.add(models.InventoryMovement(
            product_id=product.id,
            quantity=item_in.quantity,
            movement_type="in",
            reference_id=purchase.id,
            created_by_id=current_user.id,
        ))
        total_amount += item_in.quantity * item_in.unit_price

    purchase.total_amount = total_amount
    db.commit()
    db.refresh(purchase)
    return purchase


@router.get("/purchases/{id}", response_model=schemas.dispatch.PurchaseDetail)
def get_purchase(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Get purchase detail."""
    purchase = db.query(models.Purchase).filter(models.Purchase.id == id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase
