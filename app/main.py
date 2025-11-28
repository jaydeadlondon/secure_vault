from fastapi import FastAPI
from app.api.endpoints import router as api_router

app = FastAPI(title="SecureVault Cloud Storage")

app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "Vault is running"}
