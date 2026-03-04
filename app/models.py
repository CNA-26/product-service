import os
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, func
from app.schemas import ProductCreate

IMAGE_URL = os.environ.get("IMAGE_URL")

#category table
class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)

    products: List["Product"] = Relationship(back_populates="category")

#output
class Product(ProductCreate, table=True):
    __tablename__ = "products"

    id: int = Field(default=None, primary_key=True)
    product_code: str = Field(index=True, unique=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )
    category_id: int = Field(foreign_key="categories.id")
    category: Optional[Category] = Relationship(back_populates="products")
    images: List["ProductImage"] = Relationship(back_populates="product")

    @property
    def image_urls(self) -> List[str]:
        return [f"{IMAGE_URL}/{img.image}" for img in self.images]
    
#för images databasen
class ProductImage(SQLModel, table=True):
    __tablename__ = "images"

    id: int = Field(default=None, primary_key=True)

    product_id: int = Field(foreign_key="products.id")
    image: str

    product: Optional[Product] = Relationship(back_populates="images")
