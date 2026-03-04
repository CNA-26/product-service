from sqlmodel import SQLModel
from typing import Optional, List
from datetime import datetime

#input
class ProductCreate(SQLModel):
    product_name: Optional[str] = None
    price: Optional[float] = None
    description_text: Optional[str] = None
    category_id: int

#quantity
class ProductQuantity(ProductCreate):
    quantity: int | None = None

#image input
class ImageCreate(SQLModel):
    product_id: int

#skickas i get-endpoints
class ProductRead(SQLModel):
    id: int
    product_name: Optional[str]
    price: Optional[float]
    description_text: Optional[str]
    product_code: str
    created_at: datetime
    updated_at: datetime
    image_urls: List[str] = []
    category: Optional[str] = None 

    class Config:
        from_attributes = True