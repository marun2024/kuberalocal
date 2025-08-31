import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .auth.router import router as auth_router
from .core.config import API_V1_PREFIX, PROJECT_NAME, VERSION, settings
from .core.health import router as health_router
from .core.middleware import tenant_middleware
from .core.migrations import init_shared_schema
from .sessions import session_router
from .tenants.router import router as tenants_router
#from .vendors import router as vendors_router
#from .vendors.router import router as vendors_router
#from .contracts.routers.contract import router as contract_router
#from .contracts.routers.tag import router as tag_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database - only ensure shared tables exist
    await init_shared_schema()

    yield


app = FastAPI(
    title=PROJECT_NAME,
    version=VERSION,
    openapi_url=f"{API_V1_PREFIX}/openapi.json",
    docs_url=f"{API_V1_PREFIX}/docs",
    redoc_url=f"{API_V1_PREFIX}/redoc",
    redirect_slashes=False,
    lifespan=lifespan,
)

# -- Logging Configuration

# Configure environment-based logging
log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"{request.method} {request.url} - {exc.status_code}: {exc.detail}")
    raise exc

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"{request.method} {request.url} - {type(exc).__name__}: {exc}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})

# -- Middleware Configuration

# Add tenant middleware to extract tenant from subdomain
app.middleware("http")(tenant_middleware)

# Add CORS middleware for development (frontend dev server cross-origin requests)
# For multi-tenant setup, we need to handle subdomain-based origins dynamically
if settings.ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^http://([a-zA-Z0-9-]+\.)?localhost:(5173|5174|3000|8000)$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],  # Allow all headers in development
        expose_headers=["*"],  # Expose all headers in development
    )
else:
    # In production, no CORS needed as frontend is served by FastAPI
    pass

# -- Routing Configuration

app.include_router(health_router, prefix=API_V1_PREFIX)
app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(session_router, prefix=API_V1_PREFIX)
app.include_router(tenants_router, prefix=API_V1_PREFIX)
#app.include_router(vendors_router, prefix=API_V1_PREFIX)
#app.include_router(tag_router, prefix=API_V1_PREFIX)
#app.include_router(contract_router, prefix=API_V1_PREFIX)

# -- Static Files Configuration

# Only serve frontend static files in production
# In development, frontend runs on separate Vite dev server with HMR
if settings.ENVIRONMENT != "development":
    frontend_path = Path(settings.FRONTEND_DIST_PATH)
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")
    else:
        print(f"Warning: Frontend dist path {frontend_path} not found. Static files not mounted.")
