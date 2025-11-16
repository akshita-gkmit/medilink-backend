from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine, SessionLocal
from app.db.seed import run_seeder
from app.models import models

# Import routers correctly
from app.routes.auth_routes import router as auth_router
from app.routes.doctor_routes import router as doctor_router
from app.routes.admin_routes import router as admin_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MediLink API")

# CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seeder
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    run_seeder(db)
    db.close()

# Include routers
app.include_router(auth_router)
# app.include_router(doctor_router)
app.include_router(admin_router)

@app.get("/")
def root():
    return {"message": "Welcome to MediLink backend!"}
