from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.database import init_db

from src.auth.router import router as auth_router
from src.vehicles.router import router as vehicles_router
from src.earnings.router import router as earnings_router
from src.yield_engine.router import router as yield_router
from src.ws_router import router as ws_router
from src.llm.router import router as llm_router
from src.routing.router import router as routing_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    description="M-SUITE - Your car works while you sleep",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix=f"{settings.api_v1_prefix}/auth", tags=["Authentication"])
app.include_router(vehicles_router, prefix=f"{settings.api_v1_prefix}/vehicles", tags=["Vehicles"])
app.include_router(earnings_router, prefix=f"{settings.api_v1_prefix}/earnings", tags=["Earnings"])
app.include_router(yield_router, prefix=f"{settings.api_v1_prefix}/yield", tags=["Yield-Drive AI"])
app.include_router(llm_router, prefix=f"{settings.api_v1_prefix}/llm", tags=["LLM"])
app.include_router(routing_router, prefix=f"{settings.api_v1_prefix}/routing", tags=["Routing"])
app.include_router(ws_router, tags=["WebSocket"])


@app.get("/")
async def root():
    return {
        "message": "M-SUITE API",
        "tagline": "Your car works while you sleep",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
