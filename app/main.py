import os
from fastapi import FastAPI, HTTPException, Depends
from datetime import datetime
import random, string
from dotenv import load_dotenv
from typing import Optional, List
from sqlmodel import SQLModel, Field, create_engine, Session, select
from sqlalchemy import Column, DateTime, func
import httpx

load_dotenv("../.env")

DATABASE_URL = os.environ.get("DATABASE_URL")

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
    product_name: Optional[str] = None
    price: Optional[float] = None
    img: Optional[str] = None
    description_text: Optional[str] = None

#quantity
class ProductQuantity(ProductCreate):
    quantity: int | None = None

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

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

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
async def create_product(
    product: ProductQuantity,
    user: dict = Depends(verify_admin)
    ):
    SKU = generate_sku(product.product_name)

    db_product = Product(**product.model_dump(exclude={"quantity"}), product_code=SKU)

    try:
        with Session(engine) as session:
            session.add(db_product)
            session.commit()
            session.refresh(db_product)

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                "https://inventory-service-cna26-inventoryservice.2.rahtiapp.fi/api/products",
                json={
                    "sku": SKU,
                    "quantity": product.quantity or 0
                }
            )
        response.raise_for_status()

        return db_product
        
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Inventory service failed")
    
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