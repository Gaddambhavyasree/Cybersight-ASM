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
    # Continuous monitoring is scheduler-driven and disabled until an admin
    # enables it in Settings, so startup behavior is unchanged by default.
    from app.services.intelligence import scheduler_service
    scheduler_service.start_scheduler()


@app.on_event("shutdown")
async def shutdown():
    logger.info("Disconnecting from MongoDB...")
    from app.services.intelligence import scheduler_service
    scheduler_service.stop_scheduler()
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
