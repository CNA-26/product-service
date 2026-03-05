import os
import httpx
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import engine
from app.models import Product, ProductImage
from app.schemas import ProductCreate, ProductRead, ProductQuantity
from app.utils import generate_sku
from app.auth import verify_admin

router = APIRouter()

IMAGE_URL = os.environ.get("IMAGE_URL")   
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "products")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.get("/", response_model=List[ProductRead])
def read_products():
    with Session(engine) as session:
        products = session.exec(select(Product).options(selectinload(Product.images), selectinload(Product.category))).all()
        return [
            ProductRead(
                id=p.id,
                product_name=p.product_name,
                price=p.price,
                description_text=p.description_text,
                product_code=p.product_code,
                created_at=p.created_at,
                updated_at=p.updated_at,
                category=p.category.name if p.category else None,
                image_urls=[f"{IMAGE_URL}/{img.image}" for img in p.images]
            )
            for p in products
        ]

@router.get("/{product_id}", response_model=ProductRead)
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
            category=db_product.category.name if db_product.category else None,
            image_urls=[f"{IMAGE_URL}/{img.image}" for img in db_product.images]
        )

@router.post("/", response_model=Product)
async def create_product(
    product: ProductQuantity,
    user: dict = Depends(verify_admin)
    ):
    
    token = user["raw_token"]
    
    with Session(engine) as session:
        for _ in range(5):
            SKU = generate_sku(product.product_name)
            db_product = Product(**product.model_dump(exclude={"quantity"}), product_code=SKU)
            session.add(db_product)

            try:
                session.flush()

                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        "https://inventory-service-cna26-inventoryservice.2.rahtiapp.fi/api/products",
                        json={"sku": SKU,"quantity": product.quantity or 0},
                        headers={"Authorization": f"Bearer {token}"}
                    )
                response.raise_for_status()

                session.commit()
                session.refresh(db_product)
                return db_product
        
            except httpx.HTTPStatusError as e:
                session.rollback()
                if e.response.status_code == 409:
                    continue
                raise HTTPException(status_code=502, detail="Inventory service failed")
            
        raise HTTPException(status_code=500, detail="Could not generate unique SKU")
    
@router.post("/{product_id}/image")
async def upload_image(product_id: int, image: UploadFile = File(...), user: dict = Depends(verify_admin)):
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


@router.put("/{product_id}", response_model=Product)
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

@router.delete("/{product_id}")
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
