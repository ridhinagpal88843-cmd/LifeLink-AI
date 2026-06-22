from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import Base, engine

# Import all SQLAlchemy models to register them on Base metadata
from backend import models

# Import API routers
from backend.api.auth import router as auth_router
from backend.api.profile import router as profile_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App lifespan context manager. 
    Handles startup events (e.g. creating tables in SQLite) and shutdown.
    """
    # Create SQLite database tables if they do not exist
    Base.metadata.create_all(bind=engine)
    yield


# Initialize FastAPI application instance
app = FastAPI(
    title="LifeLink AI",
    description="Emergency healthcare coordination system using Google ADK and MCP.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router)
app.include_router(profile_router)


@app.get("/")
async def root_health_check():
    """
    Root endpoint returning application name and status.
    """
    return {
        "application": "LifeLink AI",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
