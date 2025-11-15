from fastapi import FastAPI
from app.db.database import Base, engine, SessionLocal
from app.db.seed import run_seeder
from app.models import models
from app.routes import auth_routes, doctor_routes, admin_routes

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MediLink API", version="1.0.0")

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    run_seeder(db)
    db.close()


app.include_router(auth_routes.router)
#app.include_router(doctor_routes.router)
#app.include_router(admin_routes.router)

@app.get("/")
def root():
    return {"message": "Welcome to MediLink backend!"}
    raise HTTPException(status_code=401, detail="Invalid email or password")    