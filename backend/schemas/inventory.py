from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from .building import Building
from .product import Product


class BuildingInventoryItem(BaseModel):
    id: int
    building_id: int
    product_id: int
    quantity: int
    last_updated: datetime
    product: Product
    building: Optional[Building] = None
    model_config = ConfigDict(from_attributes=True)


class AddInventoryRequest(BaseModel):
    building_id: int
    product_id: int
    quantity: int = 1


class ConsumeInventoryRequest(BaseModel):
    quantity: int


class AdjustInventoryRequest(BaseModel):
    quantity: int
    note: Optional[str] = None
