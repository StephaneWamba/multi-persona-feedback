from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from database import engine
from models import Base
from auth_routes import router as auth_router
from pdf_routes import router as pdf_router

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multi-Persona Feedback API",
    description="API for multi-persona feedback simulation system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "https://your-frontend-domain.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(pdf_router)


@app.get("/")
async def root():
    return {"message": "Multi-Persona Feedback API is running!"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "API is operational",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
