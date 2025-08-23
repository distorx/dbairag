from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .config import settings
from .database import engine
from .models import Base
from .routers import connections, queries, hints, fuzzy_test
from .services.redis_service import redis_service
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Redis if enabled
    if settings.redis_enabled:
        await redis_service.connect(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db
        )
        if redis_service.is_connected:
            logger.info("Redis cache initialized successfully")
        else:
            logger.warning("Redis cache initialization failed, running without cache")
    
    yield
    
    # Shutdown
    if redis_service.is_connected:
        await redis_service.disconnect()
    await engine.dispose()

app = FastAPI(
    title="RAG SQL Query API",
    description="API for natural language SQL queries with RAG",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url, 
        "http://localhost:4200",
        "http://100.123.6.21:4200",
        "http://100.88.142.40:4200",
        "http://0.0.0.0:4200",
        "*"  # Allow all origins in development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(connections.router)
app.include_router(queries.router)
app.include_router(hints.router)
app.include_router(fuzzy_test.router)

@app.get("/")
async def root():
    return {
        "message": "RAG SQL Query API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}