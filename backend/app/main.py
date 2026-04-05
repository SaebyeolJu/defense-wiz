from fastapi import FastAPI

from app.core.config import settings
from app.api.endpoints import qa

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(qa.router, prefix="/api/qa", tags=["qa"])

@app.get("/")
async def root():
    return {"message": "Welcome to DefenseWiz API"}
