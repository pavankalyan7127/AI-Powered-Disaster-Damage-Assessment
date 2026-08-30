import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

USERS_MOCKAPI_URL = "https://6a93b8d325936d5660f0c368.mockapi.io/USERS"
HISTORY_MOCKAPI_URL = "https://6a93b8d325936d5660f0c368.mockapi.io/HISTORY"
ADMIN_MOCKAPI_URL = "https://6a93bad225936d5660f0c3fd.mockapi.io/ADMIN"

# Local file storage locations
UPLOADS_DIR = os.path.join(BASE_DIR, "backend_uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
RESULTS_DIR = os.path.join(BASE_DIR, "outputs", "inference_results")
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
