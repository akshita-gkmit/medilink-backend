from fastapi import FastAPI
from app.db.database import Base, engine
from app.models import models
from app.routes import auth_routes

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MediLink API", version="1.0.0")

# Include routers
app.include_router(auth_routes.router)

@app.get("/")
def root():
    return {"message": "Welcome to MediLink backend!"}
    raise HTTPException(status_code=401, detail="Invalid email or password")    