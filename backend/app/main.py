from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.database import connect_to_database, close_database_connection
from app.routes import auth, users, admin, projects, scans, assets, ports, technologies, dns, ssl, web, vulnerabilities, threat, risk, history, reports, notifications, settings as settings_routes
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    # Permit the frontend when it is opened via a LAN hostname during local deployment.
    allow_origin_regex=r"https?://(?:localhost|127\.0\.0\.1|[A-Za-z0-9.-]+):5173",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(projects.router)
app.include_router(scans.router)
app.include_router(assets.router)
app.include_router(ports.router)
app.include_router(technologies.router)
app.include_router(dns.router)
app.include_router(ssl.router)
app.include_router(web.router)
app.include_router(vulnerabilities.router)
app.include_router(threat.router)
app.include_router(risk.router)
app.include_router(history.router)
app.include_router(reports.router)
app.include_router(notifications.router)
app.include_router(settings_routes.router)


@app.on_event("startup")
async def startup():
    logger.info("Connecting to MongoDB...")
    await connect_to_database()
    logger.info("Connected to MongoDB.")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Disconnecting from MongoDB...")
    await close_database_connection()
    logger.info("Disconnected from MongoDB.")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
