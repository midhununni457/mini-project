from fastapi import FastAPI
from app.routes.router import router

app = FastAPI(title="Classification Service")

app.include_router(router)