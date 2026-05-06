import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from testjam.core.config import settings
from testjam.routers import auth, users, groups, projects, suites, cases, testplans, executions, versions, members, tokens

app = FastAPI(title=settings.APP_NAME, docs_url="/api/docs", redoc_url="/api/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
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

os.makedirs("/app/uploads", exist_ok=True)
app.mount("/files", StaticFiles(directory="/app/uploads"), name="uploads")
