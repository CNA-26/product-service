from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return { "msg": "Hello!", "v": "0.4" }

products = ["monstera", "cactus"]

@app.get("/products")
def read_products():
    return products

@app.get("/products/{product_id}")
def read_product(product_id: int, q: str = None):
    return {"id": product_id, "name": products[product_id]}
