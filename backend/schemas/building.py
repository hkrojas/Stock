from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from .product import Product


class AssignBuildingsRequest(BaseModel):
    admin_id: int
    building_ids: List[int]


class BuildingAdmin(BaseModel):
    id: int
    username: str
    name: Optional[str] = None
    role: str
    model_config = ConfigDict(from_attributes=True)


class BuildingBase(BaseModel):
    name: str
    address: Optional[str] = None
    departments_count: int = 0
    imagen_frontis: Optional[str] = None

class BuildingCreate(BuildingBase):
    admin_id: Optional[int] = None

class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    departments_count: Optional[int] = None
    admin_id: Optional[int] = None
    imagen_frontis: Optional[str] = None

class Building(BuildingBase):
    id: int
    admin_id: Optional[int] = None
    admin: Optional[BuildingAdmin] = None
    active_orders_count: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class BuildingInventory(BaseModel):
    id: int
    building_id: int
    product_id: int
    quantity: int
    last_updated: datetime
    product: Product
    model_config = ConfigDict(from_attributes=True)
