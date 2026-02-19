import os
from fastapi import FastAPI, HTTPException, Depends
from datetime import datetime
import random, string
from dotenv import load_dotenv
from typing import Optional, List
from sqlmodel import SQLModel, Field, create_engine, Session, select
from sqlalchemy import Column, DateTime, func

load_dotenv("../.env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set!")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)
from app.auth import verify_admin

app = FastAPI()

def generate_sku(name:str):
    prefix = name.replace(" ", "")[:3].upper().ljust(3, "-")

    digits = ''.join(random.choices(string.digits, k=6))

    sku = f"{prefix}{digits}"

    return sku

#input
class ProductCreate(SQLModel):
    __tablename__ = "products"

    product_name: Optional[str] = None
    price: Optional[float] = None
    img: Optional[str] = None
    description_text: Optional[str] = None

#output
class Product(ProductCreate, table=True):
    id: int = Field(default=None, primary_key=True)
    product_code: str = Field(index=True, unique=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/")
def read_root():
    return { "msg": "Hello!", "v": "0.4" }

""" products = [
    {
        "id": 1,
        "product_name": "Monstera Deliciosa",
        "price": 29.99,
        "product_code": "PLACEHOLDER001",
        "img": "monstera.jpg",
        "description_text": "A popular tropical plant with large, glossy leaves. Easy to care for and perfect for bright indoor spaces.",
        "created_at": datetime(2025, 1, 10, 9, 30),
        "updated_at": datetime(2025, 1, 15, 14, 45),
    },
    {
        "id": 2,
        "product_name": "Snake Plant",
        "price": 19.99,
        "product_code": "PLACEHOLDER002",
        "img": "snake_plant.jpg",
        "description_text": "A hardy, low-maintenance plant known for improving air quality. Thrives in low light.",
        "created_at": datetime(2025, 1, 12, 11, 0),
        "updated_at": datetime(2025, 1, 12, 11, 0),
    },
    {
        "id": 3,
        "product_name": "Fiddle Leaf Fig",
        "price": 49.99,
        "product_code": "PLACEHOLDER003",
        "img": "fiddle_leaf_fig.jpg",
        "description_text": "A statement plant with large, violin-shaped leaves. Prefers bright, indirect light.",
        "created_at": datetime(2025, 1, 18, 16, 20),
        "updated_at": datetime(2025, 1, 20, 10, 5),
    },
    {
        "id": 4,
        "product_name": "Pothos Golden",
        "price": 14.99,
        "product_code": "PLACEHOLDER004",
        "img": "golden_pothos.jpg",
        "description_text": "A fast-growing trailing plant that’s perfect for shelves or hanging baskets.",
        "created_at": datetime(2025, 1, 22, 13, 10),
        "updated_at": datetime(2025, 1, 22, 13, 10),
    }
] """

@app.get("/products", response_model=List[Product])
def read_products():
    with Session(engine) as session:
        products = session.exec(select(Product)).all()
        return products

@app.get("/products/{product_id}", response_model=Product)
def read_product(product_id: int):
    with Session(engine) as session:
        db_product = session.get(Product, product_id)
        return db_product

@app.post("/products", response_model=Product)
def create_product(
    product: ProductCreate,
    user: dict = Depends(verify_admin)
    ):
    SKU = generate_sku(product.product_name)
    db_product = Product(**product.model_dump(), product_code=SKU)
    try:
        with Session(engine) as session:
            session.add(db_product)
            session.commit()
            session.refresh(db_product)
            return db_product
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/products/{product_id}", response_model=Product)
def update_product(
    product: ProductCreate, 
    product_id: int,
    user: dict = Depends(verify_admin)
    ):
     with Session(engine) as session:
            db_product = session.get(Product, product_id)

            if not db_product:
                raise HTTPException(status_code=404, detail="not found")
            
            for key, value in product.model_dump(exclude_unset=True).items():
                setattr(db_product, key, value)
                session.add(db_product)
                session.commit()
                session.refresh(db_product)
                return db_product

@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    user: dict = Depends(verify_admin)
    ):
    with Session(engine) as session:
            db_product = session.get(Product, product_id)

            if not db_product:
                raise HTTPException(status_code=404, detail="not found")

            session.delete(db_product)
            session.commit()
            return {"message": "Product removed", "id": product_id}