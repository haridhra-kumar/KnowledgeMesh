from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.api.documents import router as documents_router
from app.api.facts import router as facts_router
from app.api.relationships import router as relationships_router
from app.api.clusters import router as clusters_router
from app.api.timeline import router as timeline_router
from app.api.review import router as review_router
from app.api.stats import router as stats_router
from app.api.diagnostics import router as diagnostics_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure directories and initialize SQLite DB
    settings.ensure_directories()
    init_db()
    yield
    # Shutdown

app = FastAPI(
    title="KnowledgeMesh API",
    description="Evidence-backed document intelligence API for fact extraction, grounding, and cross-document reasoning.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(documents_router, prefix="/api")
app.include_router(facts_router, prefix="/api")
app.include_router(relationships_router, prefix="/api")
app.include_router(clusters_router, prefix="/api")
app.include_router(timeline_router, prefix="/api")
app.include_router(review_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(diagnostics_router, prefix="/api")

# Serve uploaded source PDFs for direct evidence inspection
if Path(settings.upload_dir).exists():
    app.mount("/files", StaticFiles(directory=settings.upload_dir), name="files")

@app.get("/")
def root():
    # If frontend build exists, serve it, otherwise return API info
    frontend_dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    index_path = frontend_dist_dir / "index.html"
    if index_path.exists():
        from fastapi.responses import FileResponse
        return FileResponse(str(index_path))
    return {
        "name": "KnowledgeMesh API",
        "description": "Evidence-backed document intelligence",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Mount frontend production build if available
frontend_dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API, files, docs, or health routes
        if full_path.startswith("api") or full_path.startswith("files") or full_path.startswith("docs") or full_path.startswith("openapi.json") or full_path == "health":
            return None
        index_path = frontend_dist_dir / "index.html"
        if index_path.exists():
            from fastapi.responses import FileResponse
            return FileResponse(str(index_path))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
