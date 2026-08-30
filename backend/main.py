import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes import auth, assessment, history, review, admin
from backend.config import BASE_DIR, UPLOADS_DIR, OUTPUTS_DIR

app = FastAPI(
    title="Disaster Damage Assessment API",
    description="Backend API supporting Siamese ML inference and disaster damage assessment workflow.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(assessment.router)
app.include_router(history.router)
app.include_router(review.router)
app.include_router(admin.router)

# Serve Static Files (crop images, outputs, uploads, nepal images)
os.makedirs(os.path.join(BASE_DIR, "outputs"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "inference"), exist_ok=True)

app.mount("/outputs", StaticFiles(directory=os.path.join(BASE_DIR, "outputs")), name="outputs")
app.mount("/backend_uploads", StaticFiles(directory=os.path.join(BASE_DIR, "backend_uploads")), name="backend_uploads")
app.mount("/inference", StaticFiles(directory=os.path.join(BASE_DIR, "inference")), name="inference")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Disaster Damage Assessment Backend API"}
