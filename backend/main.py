from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import asyncio
import sys
from dotenv import load_dotenv

# Fix Windows asyncio compatibility issue
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load environment variables
load_dotenv()

# Import routers
from routers import cities, scraper, dashboard

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 HappyCow Scraper API starting up...")
    yield
    # Shutdown
    print("🛑 HappyCow Scraper API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="HappyCow Scraper API",
    description="API for managing HappyCow restaurant scraping operations",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174",  # Vite dev server (current)
        "http://localhost:3000"   # Alternative React dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cities.router, prefix="/api/cities", tags=["cities"])
app.include_router(scraper.router, prefix="/api/scraper", tags=["scraper"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])

@app.get("/")
async def root():
    return {"message": "HappyCow Scraper API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 