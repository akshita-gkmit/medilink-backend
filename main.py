import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine, SessionLocal
from app.db.seed import run_seeder
from app.models import models
from app.routes.auth_routes import router as auth_router
from app.routes.doctor_routes import router as doctor_router
from app.routes.admin_routes import router as admin_router
from app.routes.appointments_routes import router as appointments_router
from app.routes.doctor_appointments import router as doctor_appointments
from app.routes.patient_routes import router as patient_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MediLink API")

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost:4173",
    "http://54.193.174.61"
    "http://127.0.0.1:4173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    run_seeder(db)
    db.close()

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(doctor_router)
app.include_router(appointments_router)
app.include_router(doctor_appointments)
app.include_router(patient_router)

@app.get("/")
def root():
    return {"message": "Welcome to MediLink backend!"}

if __name__ == "__main__":
 uvicorn.run("app:app", host="0.0.0.0", port=8000)