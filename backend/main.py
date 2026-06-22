from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager for FastAPI startup and shutdown events.
    Useful for initializing databases, creating pools, and starting background processes.
    """
    # Startup: Create tables in local development database
    if settings.APP_ENV == "development":
        Base.metadata.create_all(bind=engine)
    
    yield
    
    # Shutdown: Clean up connections, close pools, etc.
    pass


# Initialize FastAPI instance
app = FastAPI(
    title="LifeLink AI Backend",
    description="Emergency healthcare coordination system using Google ADK and MCP.",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS for frontend Streamlit dashboard or web components
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific domains in production env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health Check"])
async def health_check():
    """
    Simple API health endpoint confirming app and environment status.
    """
    return {
        "status": "healthy",
        "app": "LifeLink AI",
        "environment": settings.APP_ENV
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
