import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from testjam.core.config import settings
from testjam.core.logging import RequestContextMiddleware, configure_logging
from testjam.core.middleware import SecurityHeadersMiddleware
from testjam.core.rate_limit import limiter
from testjam.core.sentry import configure_sentry

configure_logging()
configure_sentry()
from testjam.database import SessionLocal
from testjam.realtime import manager, set_main_loop
from testjam.realtime_backplane import build_backplane, set_backplane
from testjam.routers import admin, auth, users, groups, projects, suites, cases, testplans, executions, versions, members, tokens, notifications, notification_preferences, settings as settings_router, ws, health
from testjam.services.log_flusher import configure_from_settings as configure_log_flusher
from testjam.services.settings import get_settings as get_app_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    set_main_loop(asyncio.get_running_loop())
    with SessionLocal() as db:
        configure_log_flusher(get_app_settings(db))

    backplane = None
    if settings.REDIS_URL:
        backplane = build_backplane(
            settings.REDIS_URL,
            settings.REALTIME_CHANNEL_PREFIX,
            manager.deliver_local,
        )
        await backplane.start()
        set_backplane(backplane)

    try:
        yield
    finally:
        if backplane is not None:
            set_backplane(None)
            await backplane.stop()


app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(groups.router, prefix=settings.API_V1_PREFIX)
app.include_router(projects.router, prefix=settings.API_V1_PREFIX)
app.include_router(suites.projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(suites.suites_router, prefix=settings.API_V1_PREFIX)
app.include_router(cases.projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(cases.suites_router, prefix=settings.API_V1_PREFIX)
app.include_router(cases.cases_router, prefix=settings.API_V1_PREFIX)
app.include_router(testplans.projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(testplans.plans_router, prefix=settings.API_V1_PREFIX)
app.include_router(executions.projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(executions.executions_router, prefix=settings.API_V1_PREFIX)
app.include_router(executions.results_router, prefix=settings.API_V1_PREFIX)
app.include_router(versions.projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(versions.versions_router, prefix=settings.API_V1_PREFIX)
app.include_router(members.router, prefix=settings.API_V1_PREFIX)
app.include_router(tokens.user_router, prefix=settings.API_V1_PREFIX)
app.include_router(tokens.project_router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)
app.include_router(notification_preferences.router, prefix=settings.API_V1_PREFIX)
app.include_router(settings_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(ws.router, prefix=settings.API_V1_PREFIX)
app.include_router(health.router)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
