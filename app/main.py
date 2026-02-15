from fastapi import FastAPI, HTTPException
from datetime import datetime
from pydantic import BaseModel
import random, string

app = FastAPI()

class ProductCreate(BaseModel):
    product_name: str | None = None
    price: float | None = None
    product_code: str | None = None
    img: str | None = None
    description_text: str | None = None

class Product(ProductCreate):
    id: int
    created_at: datetime
    updated_at: datetime

@app.get("/")
def read_root():
    return { "msg": "Hello!", "v": "0.4" }

from datetime import datetime

products = [
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
]

@app.get("/products")
def read_products():
    return products

@app.get("/products/{product_id}")
def read_product(product_id: int):
    return {"id": product_id, "name": products[product_id]}

@app.post("/products", response_model=Product)
def create_product(product: ProductCreate):
    current_id = 5

    new_product = {
        "id": current_id,
        **product.dict(),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    products.append(new_product)
    current_id += 1

    return new_product

@app.put("/products/{product_id}", response_model=Product)
def update_product(product: ProductCreate, product_id: int):
     for idx, excisting_product in enumerate(products):
        if excisting_product["id"] == product_id:

            updated_product = {
                "id": product_id,
                **product.dict(),
                "created_at": excisting_product["created_at"],
                "updated_at": datetime.now()
            }
            products[idx] = updated_product
            
            return updated_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            products.remove(product)
            return {"message": "Product removed", "id": product_id}
        
    raise HTTPException(status_code=404, detail="Product not found")


def generate_sku(name:str):
    prefix = name.replace(" ", "")[:3].upper().ljust(3, "-")

    digits = ''.join(random.choices(string.digits, k=6))

    sku = f"{prefix}{digits}"

    return sku