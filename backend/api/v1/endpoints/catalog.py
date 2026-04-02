import csv
import io
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend import models, schemas
from backend.api import deps
from backend.services.scraper import ScraperService

router = APIRouter()


@router.get("/", response_model=List[schemas.product.Product])
def read_products(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve active products."""
    products = db.query(models.Product).filter(models.Product.is_active == True).offset(skip).limit(limit).all()
    return products


@router.get("/all", response_model=List[schemas.product.Product])
def read_all_products(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_management),
    skip: int = 0,
    limit: int = 50,
    q: str = None,
) -> Any:
    """Retrieve all products including inactive (management only)."""
    query = db.query(models.Product)
    if q:
        query = query.filter(
            (models.Product.name.ilike(f"%{q}%")) | 
            (models.Product.sku.ilike(f"%{q}%"))
        )
    products = query.order_by(models.Product.name).offset(skip).limit(limit).all()
    return products


@router.get("/{id}", response_model=schemas.product.Product)
def read_product(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
) -> Any:
    """Get product by ID."""
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=schemas.product.Product)
def create_product(
    *,
    db: Session = Depends(deps.get_db),
    product_in: schemas.product.ProductCreate,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Create new product."""
    product = models.Product(**product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{id}", response_model=schemas.product.Product)
def update_product(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    product_in: schemas.product.ProductUpdate,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Update product details."""
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.patch("/{id}/toggle", response_model=schemas.product.Product)
def toggle_product(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Toggle product active/inactive status."""
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_active = not product.is_active
    db.commit()
    db.refresh(product)
    return product


@router.post("/import-csv")
async def import_csv(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Import products from a CSV file. Creates or updates products."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    file_bytes = await file.read()
    try:
        decoded_text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded_text = file_bytes.decode("cp1252", errors="replace")

    stream = io.StringIO(decoded_text)
    sample = stream.read(1024)
    stream.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(stream, dialect=dialect)
    created_count = 0
    updated_count = 0
    error_rows = []

    new_upload = models.CsvUpload(filename=file.filename)
    db.add(new_upload)
    db.flush()

    for row_num, row in enumerate(reader, start=2):
        try:
            sku = row.get("sku", "").strip()
            nombre = row.get("nombre", "").strip()
            unidad = row.get("unidad_medida", "").strip()
            precio_str = row.get("precio", "0").strip()
            descripcion = row.get("descripcion", "").strip()
            categoria = row.get("categoria", "General").strip()
            imagen_url = row.get("imagen_url", "").strip()
            stock_str = row.get("stock_actual", "0").strip()

            if not nombre:
                error_rows.append(f"Fila {row_num}: nombre vacío")
                continue

            precio = float(precio_str) if precio_str else 0.0
            stock = int(stock_str) if stock_str else 0

            product = None
            if sku:
                product = db.query(models.Product).filter(models.Product.sku == sku).first()
            if not product:
                product = db.query(models.Product).filter(models.Product.name == nombre).first()

            if product:
                if sku:
                    product.sku = sku
                product.name = nombre
                if unidad:
                    product.unit = unidad
                product.precio = precio
                if descripcion:
                    product.description = descripcion
                if categoria:
                    product.categoria = categoria
                if imagen_url:
                    product.imagen_url = imagen_url
                if stock > 0:
                    product.stock_actual = stock
                updated_count += 1
            else:
                new_product = models.Product(
                    sku=sku if sku else None,
                    name=nombre,
                    unit=unidad if unidad else "Unidad",
                    categoria=categoria if categoria else "General",
                    precio=precio,
                    description=descripcion if descripcion else None,
                    imagen_url=imagen_url if imagen_url else "/static/img/default-product.png",
                    stock_actual=stock,
                    source_csv_id=new_upload.id,
                )
                db.add(new_product)
                created_count += 1
        except Exception as e:
            error_rows.append(f"Fila {row_num}: {str(e)}")
            continue

    new_upload.products_created = created_count
    new_upload.products_updated = updated_count
    db.commit()

    return {
        "id": new_upload.id,
        "filename": new_upload.filename,
        "products_created": created_count,
        "products_updated": updated_count,
        "errors": error_rows[:10],
    }


@router.delete("/uploads/{id}")
def delete_csv_upload(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Delete a CSV upload batch. Products with history are soft-deleted."""
    upload = db.query(models.CsvUpload).filter(models.CsvUpload.id == id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    products = db.query(models.Product).filter(models.Product.source_csv_id == id).all()
    deleted_count = 0
    soft_deleted_count = 0

    for p in products:
        has_orders = db.query(models.OrderItem).filter(models.OrderItem.product_id == p.id).first()
        has_movements = db.query(models.InventoryMovement).filter(models.InventoryMovement.product_id == p.id).first()
        if has_orders or has_movements:
            p.is_active = False
            soft_deleted_count += 1
        else:
            db.delete(p)
            deleted_count += 1

    db.delete(upload)
    db.commit()
    return {
        "message": f"Batch deleted. {deleted_count} hard-deleted, {soft_deleted_count} soft-deleted."
    }


@router.post("/preview", response_model=Any)
async def preview_product(
    *,
    url: str,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Scrape product details for preview."""
    details = await ScraperService.get_product_details(url)
    if "error" in details:
        raise HTTPException(status_code=400, detail=details["error"])
    return details


@router.put("/{id}/sync", response_model=schemas.product.Product)
async def sync_product(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Sync existing product with its source URL."""
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not product.source_url:
        raise HTTPException(status_code=400, detail="Product has no source URL")

    details = await ScraperService.get_product_details(product.source_url)
    if "error" in details:
        raise HTTPException(status_code=400, detail=details["error"])

    product.name = details.get("name", product.name)
    product.precio = details.get("price", product.precio)
    product.description = details.get("description", product.description)
    product.imagen_url = details.get("image_url", product.imagen_url)
    product.last_synced_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(product)
    return product
