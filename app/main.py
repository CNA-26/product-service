import os
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import random, string
from dotenv import load_dotenv
from typing import Optional, List
from sqlmodel import SQLModel, Field, create_engine, Session, select, Relationship
from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import selectinload
import httpx
from uuid import uuid4
from app.auth import verify_admin

load_dotenv("../.env")

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set!")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

IMAGE_URL = os.environ.get("IMAGE_URL")

if not IMAGE_URL:
    raise ValueError("Cannot get image URL")
    
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "products")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = FastAPI()

app.mount("/uploads", StaticFiles(directory=os.path.join(BASE_DIR, "uploads")), name="uploads")

origins = [
    "http://localhost:5174/",
    "https://admin-frontend-cna26-admin-frontend.2.rahtiapp.fi/",
    "https://store-frontend-git-store-frontend.2.rahtiapp.fi/",
    "https://inventory-service-cna26-inventoryservice.2.rahtiapp.fi/",
    "https://order-service-git-order-service.2.rahtiapp.fi/",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_sku(name:str):
    prefix = name.replace(" ", "")[:3].upper().ljust(3, "-")
    digits = ''.join(random.choices(string.digits, k=6))

    sku = f"{prefix}{digits}"
    return sku

#input
class ProductCreate(SQLModel):
    product_name: Optional[str] = None
    price: Optional[float] = None
    description_text: Optional[str] = None

#image input
class ImageCreate(SQLModel):
    product_id: int

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
    images: List["ProductImage"] = Relationship(back_populates="product")

    @property
    def image_urls(self) -> List[str]:
        return [f"{IMAGE_URL}/{img.image}" for img in self.images]
    
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

    class Config:
        from_attributes = True

#för images databasen
class ProductImage(SQLModel, table=True):
    __tablename__ = "images"

    id: int = Field(default=None, primary_key=True)

    product_id: int = Field(foreign_key="products.id")
    image: str

    product: Optional[Product] = Relationship(back_populates="images")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/products", response_model=List[ProductRead])
def read_products():
    with Session(engine) as session:
        products = session.exec(select(Product).options(selectinload(Product.images))).all()
        return [
            ProductRead(
                id=p.id,
                product_name=p.product_name,
                price=p.price,
                description_text=p.description_text,
                product_code=p.product_code,
                created_at=p.created_at,
                updated_at=p.updated_at,
                image_urls=[f"{IMAGE_URL}/{img.image}" for img in p.images]
            )
            for p in products
        ]

@app.get("/products/{product_id}", response_model=ProductRead)
def read_product(product_id: int):
    with Session(engine) as session:
        db_product = session.get(Product, product_id)
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        return ProductRead(
            id=db_product.id,
            product_name=db_product.product_name,
            price=db_product.price,
            description_text=db_product.description_text,
            product_code=db_product.product_code,
            created_at=db_product.created_at,
            updated_at=db_product.updated_at,
            image_urls=[f"{IMAGE_URL}/{img.image}" for img in db_product.images]
        )

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
    
@app.post("/products/{product_id}/image")
async def upload_image(product_id: int, image: UploadFile = File(...)):
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if image.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid file type")
    
        filename = f"{uuid4()}.{image.filename.split('.')[-1]}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        try:
            await image.seek(0)
            content = await image.read()

            with open(file_path, "wb") as f:
                f.write(content)

            product_image = ProductImage(product_id=product.id, image=filename)
            session.add(product_image)
            session.commit()
            session.refresh(product_image)

            return product_image  
        except Exception as e:
            print(f"FEL VID SPARANDE: {e}")
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