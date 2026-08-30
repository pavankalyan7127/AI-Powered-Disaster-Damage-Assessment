import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Ensure environment variables are loaded prior to routes initialization
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from backend.routes import auth, assessment, history, review, admin, explain, chat
from backend.config import UPLOADS_DIR, OUTPUTS_DIR

app = FastAPI(
    title="Disaster Damage Assessment API",
    description="Backend API supporting Siamese ML inference, disaster damage assessment workflow, Gemini AI explanations, and building chat.",
    version="1.2.0"
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
app.include_router(explain.router)
app.include_router(chat.router)

# Serve Static Files (crop images, outputs, uploads, nepal images)
os.makedirs(os.path.join(BASE_DIR, "outputs"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "inference"), exist_ok=True)

app.mount("/outputs", StaticFiles(directory=os.path.join(BASE_DIR, "outputs")), name="outputs")
app.mount("/backend_uploads", StaticFiles(directory=os.path.join(BASE_DIR, "backend_uploads")), name="backend_uploads")
app.mount("/inference", StaticFiles(directory=os.path.join(BASE_DIR, "inference")), name="inference")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Disaster Damage Assessment Backend API"}
