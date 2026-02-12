from fastapi import FastAPI, HTTPException
from datetime import datetime
from pydantic import BaseModel

app = FastAPI()

class ProductCreate(BaseModel):
    ProductName: str | None = None
    Price: float | None = None
    ProductCode: str | None = None
    Img: str | None = None
    DescriptionText: str | None = None

class Product(ProductCreate):
    Id: int
    CreatedAt: datetime
    UpdatedAt: datetime

@app.get("/")
def read_root():
    return { "msg": "Hello!", "v": "0.4" }

from datetime import datetime

products = [
    {
        "Id": 1,
        "ProductName": "Monstera Deliciosa",
        "Price": 29.99,
        "ProductCode": "PLACEHOLDER001",
        "Img": "monstera.jpg",
        "DescriptionText": "A popular tropical plant with large, glossy leaves. Easy to care for and perfect for bright indoor spaces.",
        "CreatedAt": datetime(2025, 1, 10, 9, 30),
        "UpdatedAt": datetime(2025, 1, 15, 14, 45),
    },
    {
        "Id": 2,
        "ProductName": "Snake Plant",
        "Price": 19.99,
        "ProductCode": "PLACEHOLDER002",
        "Img": "snake_plant.jpg",
        "DescriptionText": "A hardy, low-maintenance plant known for improving air quality. Thrives in low light.",
        "CreatedAt": datetime(2025, 1, 12, 11, 0),
        "UpdatedAt": datetime(2025, 1, 12, 11, 0),
    },
    {
        "Id": 3,
        "ProductName": "Fiddle Leaf Fig",
        "Price": 49.99,
        "ProductCode": "PLACEHOLDER003",
        "Img": "fiddle_leaf_fig.jpg",
        "DescriptionText": "A statement plant with large, violin-shaped leaves. Prefers bright, indirect light.",
        "CreatedAt": datetime(2025, 1, 18, 16, 20),
        "UpdatedAt": datetime(2025, 1, 20, 10, 5),
    },
    {
        "Id": 4,
        "ProductName": "Pothos Golden",
        "Price": 14.99,
        "ProductCode": "PLACEHOLDER004",
        "Img": "golden_pothos.jpg",
        "DescriptionText": "A fast-growing trailing plant that’s perfect for shelves or hanging baskets.",
        "CreatedAt": datetime(2025, 1, 22, 13, 10),
        "UpdatedAt": datetime(2025, 1, 22, 13, 10),
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
        "Id": current_id,
        **product.dict(),
        "CreatedAt": datetime.now(),
        "UpdatedAt": datetime.now()
    }

    products.append(new_product)
    current_id += 1

    return new_product

@app.put("/products/{product_id}", response_model=Product)
def update_product(product: ProductCreate, product_id: int):
     for idx, excisting_product in enumerate(products):
        if excisting_product["Id"] == product_id:

            updated_product = {
                "Id": product_id,
                **product.dict(),
                "CreatedAt": excisting_product["CreatedAt"],
                "UpdatedAt": datetime.now()
            }
            products[idx] = updated_product
            
            return updated_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    for product in products:
        if product["Id"] == product_id:
            products.remove(product)
            return {"message": "Product removed", "id": product_id}
        
    raise HTTPException(status_code=404, detail="Product not found")