from fastapi import FastAPI
from database import engine
import inventory

app = FastAPI()

inventory.Base.metadata.create_all(bind=engine)

app.include_router(inventory.router)

@app.get("/")
def root():
    return {"status": "Inventory API Running"}
from fastapi import HTTPException
