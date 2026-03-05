import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import create_db
from app.routers import products

#INVENTORY_URL = os.environ.get("INVENTORY_URL")
#ADMIN_FRONTEND_URL = os.environ.get("ADMIN_FRONTEND_URL")
#STORE_FRONTEND_URL = os.environ.get("STORE_FRONTEND_URL")

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/uploads", StaticFiles(directory=os.path.join(BASE_DIR, "uploads")), name="uploads")

origins = [
    "https://store-frontend-git-store-frontend.2.rahtiapp.fi",
    "https://admin-frontend-nico-branch-cna26-admin-frontend.2.rahtiapp.fi"
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/products", tags=["Products"])