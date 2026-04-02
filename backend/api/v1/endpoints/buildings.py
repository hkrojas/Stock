from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend import models, schemas
from backend.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.building.Building])
def read_buildings(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve buildings. Admin sees only their own; superadmin/manager sees all."""
    if current_user.role in ("superadmin", "manager"):
        buildings = db.query(models.Building).offset(skip).limit(limit).all()
    else:
        buildings = db.query(models.Building).filter(models.Building.admin_id == current_user.id).all()
    return buildings


@router.get("/unassigned", response_model=List[schemas.building.Building])
def read_unassigned_buildings(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """List buildings that have no admin assigned."""
    buildings = db.query(models.Building).filter(models.Building.admin_id == None).all()
    return buildings


@router.get("/{id}", response_model=schemas.building.Building)
def read_building(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get a single building by ID."""
    building = db.query(models.Building).filter(models.Building.id == id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    if current_user.role not in ("superadmin", "manager") and building.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return building


@router.post("/", response_model=schemas.building.Building)
def create_building(
    *,
    db: Session = Depends(deps.get_db),
    building_in: schemas.building.BuildingCreate,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Create a new building."""
    existing = db.query(models.Building).filter(models.Building.name == building_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Building '{building_in.name}' already exists")

    building = models.Building(**building_in.model_dump())
    db.add(building)
    db.commit()
    db.refresh(building)
    return building


@router.put("/{id}", response_model=schemas.building.Building)
def update_building(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    building_in: schemas.building.BuildingUpdate,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Update building details."""
    building = db.query(models.Building).filter(models.Building.id == id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    if building_in.name is not None:
        conflict = db.query(models.Building).filter(
            models.Building.name == building_in.name,
            models.Building.id != id
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail=f"Name '{building_in.name}' already taken")
        building.name = building_in.name

    update_data = building_in.model_dump(exclude_unset=True, exclude={"name"})
    for field, value in update_data.items():
        setattr(building, field, value)

    db.commit()
    db.refresh(building)
    return building


@router.delete("/{id}")
def delete_building(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Delete a building (only if it has no orders)."""
    building = db.query(models.Building).filter(models.Building.id == id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    has_orders = db.query(models.Order).filter(models.Order.building_id == id).first()
    if has_orders:
        raise HTTPException(status_code=400, detail="Cannot delete building with associated orders")

    db.delete(building)
    db.commit()
    return {"message": f"Building '{building.name}' deleted"}


@router.post("/assign")
def assign_buildings(
    *,
    db: Session = Depends(deps.get_db),
    payload: schemas.building.AssignBuildingsRequest,
    current_user: models.User = Depends(deps.get_current_active_management),
) -> Any:
    """Assign one or more buildings to an admin user."""
    admin_id = payload.admin_id
    building_ids = payload.building_ids
    admin = db.query(models.User).filter(models.User.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    assigned_names = []
    for b_id in building_ids:
        building = db.query(models.Building).filter(models.Building.id == b_id).first()
        if building:
            building.admin_id = admin.id
            assigned_names.append(building.name)

    if not assigned_names:
        raise HTTPException(status_code=400, detail="No valid buildings specified")

    db.commit()
    return {"message": f"Assigned to {admin.username}: {', '.join(assigned_names)}"}


@router.get("/{id}/inventory", response_model=List[schemas.building.BuildingInventory])
def read_building_inventory(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get inventory for a specific building."""
    if current_user.role not in ("superadmin", "manager"):
        building = db.query(models.Building).filter(
            models.Building.id == id,
            models.Building.admin_id == current_user.id
        ).first()
        if not building:
            raise HTTPException(status_code=403, detail="Not enough privileges to view this building's inventory")

    inventory = db.query(models.BuildingInventory).filter(models.BuildingInventory.building_id == id).all()
    return inventory
