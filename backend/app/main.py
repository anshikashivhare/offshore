from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.routes import router as routes_router
from app.api.routes.seaice import router as seaice_router
from app.api.routes.iceberg import router as iceberg_router
from app.api.routes.dashboard import router as dashboard_router

app = FastAPI(title="Antarctic Navigation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_router)
app.include_router(seaice_router)
app.include_router(iceberg_router)
app.include_router(dashboard_router)


@app.get("/health")
def health():
    return {"status": "ok"}
