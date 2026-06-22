import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import dashboard

@asynccontextmanager
async def lifespan(app: FastAPI):
    bg_task = asyncio.create_task(dashboard.crypto_background_fetcher())
    print("[Lifespan] Starting background fetcher task.")
    yield
    print("[Lifespan] Stopping background fetcher task.")
    bg_task.cancel()

app = FastAPI(title="Crypto Dashboard", version="1.0", lifespan=lifespan)
app.include_router(dashboard.router)