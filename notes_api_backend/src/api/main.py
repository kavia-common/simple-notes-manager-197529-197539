from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import db
from src.api.notes_routes import router as notes_router

openapi_tags = [
    {
        "name": "health",
        "description": "Service health and readiness checks.",
    },
    {
        "name": "notes",
        "description": "CRUD operations for notes.",
    },
]

app = FastAPI(
    title="Notes API",
    description="Backend API for a simple notes application (FastAPI + SQLite).",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# Frontend runs on localhost:3000 and calls backend on localhost:3001
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    """Initialize database schema on application startup."""
    db.ensure_schema()


@app.get(
    "/",
    tags=["health"],
    summary="Health check",
    description="Simple health endpoint to verify the API is running.",
    operation_id="healthCheck",
)
def health_check():
    """Return basic health status."""
    return {"message": "Healthy"}


app.include_router(notes_router)
