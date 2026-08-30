import os
from dotenv import load_dotenv, find_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load .env explicitly from backend directory or project root
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(find_dotenv(usecwd=True))

# Gemini API Key (backend only)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

USERS_MOCKAPI_URL = "https://6a93b8d325936d5660f0c368.mockapi.io/USERS"
HISTORY_MOCKAPI_URL = "https://6a93b8d325936d5660f0c368.mockapi.io/HISTORY"
ADMIN_MOCKAPI_URL = "https://6a93bad225936d5660f0c3fd.mockapi.io/ADMIN"

# Local file storage locations
UPLOADS_DIR = os.path.join(BASE_DIR, "backend_uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
RESULTS_DIR = os.path.join(BASE_DIR, "outputs", "inference_results")
EXPLANATION_CACHE_DIR = os.path.join(BASE_DIR, "outputs", "explanations")
MODEL_CHECKPOINT = os.path.join(BASE_DIR, "outputs", "best_siamese_model.pth")
CONFIG_YAML = os.path.join(BASE_DIR, "config.yaml")

# Demo Nepal Dataset Paths
NEPAL_PRE_TIFF = os.path.join(BASE_DIR, "inference", "nepal", "10500100364E8400_pre.tif")
NEPAL_POST_TIFF = os.path.join(BASE_DIR, "inference", "nepal", "B040001100881710_post.tif")
NEPAL_FOOTPRINTS_GEOJSON = os.path.join(BASE_DIR, "inference", "nepal", "buildings.geojson")
NEPAL_PRECOMPUTED_JSON = os.path.join(BASE_DIR, "outputs", "nepal_inference_results.json")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(EXPLANATION_CACHE_DIR, exist_ok=True)
