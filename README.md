# Disaster Damage Assessment

**BuildSprint 2026 — AI-Powered Disaster Damage Assessment Prototype**

An end-to-end AI-assisted disaster-response platform that analyzes pre- and post-disaster imagery to classify building damage, present building-level assessments, support human review, and provide explainable AI assistance.

---

## 1. Project Overview

Natural disasters such as floods, landslides, earthquakes, cyclones, and other extreme events can damage large numbers of buildings in a very short period of time. After an event, emergency teams need to understand **where the damage occurred, how severe it is, and which structures should receive attention first**.

Manual inspection is often slow, difficult to scale, and potentially dangerous when affected areas are unstable or inaccessible.

**Disaster Damage Assessment** addresses this problem by comparing **pre-disaster and post-disaster imagery** and producing building-level damage classifications.

The current model uses a **Siamese ResNet-50** architecture and classifies buildings into four categories:

- `no-damage`
- `minor-damage`
- `major-damage`
- `destroyed`

The machine-learning pipeline is connected to a FastAPI backend and React/Vite frontend. The web application allows users to inspect assessment results, open individual building details, request human review where applicable, and use Explainable AI and building-context chat to understand individual assessments.

---

## 2. Problem Statement

Large disasters can affect thousands of structures. Emergency teams may have access to satellite or aerial imagery, but raw imagery alone does not immediately provide a building-by-building assessment.

The main challenges are:

1. **Scale** — large disaster areas may contain thousands of structures.
2. **Time sensitivity** — decisions need to be made quickly after a disaster.
3. **Responder safety** — physical inspection can be dangerous.
4. **Inconsistent manual assessment** — different inspectors may assess similar damage differently.
5. **Prioritization** — responders need actionable building-level information rather than only raw imagery.

The project therefore provides an automated first-pass assessment that can help humans understand and prioritize affected structures.

---

## 3. Objective

The core objective is:

> Convert pre- and post-disaster imagery into interpretable building-level damage assessments that can support faster disaster-response decisions.

The overall pipeline is:

```text
Pre/Post Disaster Imagery
          |
          v
Building Localization / Cropping
          |
          v
Preprocessing
          |
          v
Pre + Post Image Pairs
          |
          v
Siamese ResNet-50
          |
          v
Damage Class + Confidence
          |
          v
FastAPI Backend
          |
          v
React Web Application
          |
     +----+----+----------------+
     |         |                |
     v         v                v
 Details   Explainable AI   Human Review
                       |
                       v
                 Admin Dashboard
```

---

## 4. Key Features

### Building-level damage classification

Each building receives one of four damage classes:

| Class | Meaning |
|---|---|
| No Damage | No significant visible damage |
| Minor Damage | Limited visible damage |
| Major Damage | Significant visible damage |
| Destroyed | Severe destruction |

### Pre/Post comparison

The model works with paired imagery:

```text
PRE-DISASTER IMAGE
        +
POST-DISASTER IMAGE
        |
        v
DAMAGE ASSESSMENT
```

The pre-disaster image provides a reference state while the post-disaster image provides the observed post-event state.

### Confidence score

Every model prediction is accompanied by a confidence value. Confidence is presented as supporting information and is not treated as proof that a prediction is correct.

### Building detailed view

Users can open an individual building and inspect its complete available assessment information, including imagery, prediction, confidence, metadata, and review information.

### Explainable AI

The application can send the selected building's assessment context to Gemini and present a natural-language explanation.

Example questions include:

- "Why was this building classified as major damage?"
- "What does this prediction mean?"
- "What changes are visible between the two images?"

### Building-context AI chat

The detailed building page contains an AI chat interface that is aware of the building currently being viewed and the available associated assessment data.

This enables building-specific questions such as:

> "Is it safe to be near this building?"

The AI is intended for decision support and does **not** replace qualified structural or emergency-safety assessment.

### Human-in-the-loop review

Where applicable, a user can request human review. This creates a workflow in which AI provides an initial assessment and a human can verify or override it.

### Admin dashboard

Administrators can inspect the complete building assessment information available to normal users, excluding the user-facing AI chatbox, and can participate in the review/approval/override workflow.

---

# 5. System Architecture

```text
+------------------------------------------------------+
|                    FRONTEND                          |
|                 React + Vite                        |
|                                                      |
| Landing | Auth | Assessment | Results | Details     |
| History | Explain AI | Review | Admin Dashboard     |
+-------------------------+----------------------------+
                          |
                          | HTTP / API
                          v
+------------------------------------------------------+
|                     BACKEND                          |
|                    FastAPI                           |
|                                                      |
| Auth | Assessment | History | Review | Admin        |
| AI Service | MockAPI Service                        |
+-------------------------+----------------------------+
                          |
                +---------+---------+
                |                   |
                v                   v
+-----------------------+   +-------------------------+
| ML / INFERENCE        |   | MockAPI                 |
|                       |   |                         |
| preprocess.py         |   | USERS                   |
| train.py              |   | HISTORY                 |
| test.py               |   | Application records     |
| inference.py          |   |                         |
| satellite_crop_       |   +-------------------------+
| engine.py             |
+-----------------------+
```

---

# 6. Input Modes

The application supports two primary processing modes.

## 6.1 Satellite Mode

The user supplies larger-area satellite/disaster imagery.

The satellite crop engine converts the large image into building-level crops.

```text
Large Satellite Image
        |
        v
satellite_crop_engine.py
        |
        v
Building-level PRE/POST crops
        |
        v
Inference
```

This represents the intended large-area disaster-response workflow.

## 6.2 Direct Crop Mode

The user supplies building-level imagery directly.

The satellite crop stage can be bypassed:

```text
Building PRE Image
        +
Building POST Image
        |
        v
Inference
        |
        v
Prediction
```

This mode is useful for demonstrations, testing, and already-prepared building crops.

---

# 7. Dataset

The project uses the **xBD disaster damage assessment dataset** as the basis for model development.

The current prototype uses a selected subset rather than attempting to process the entire raw dataset.

The current preprocessing run reported:

- **Image pairs discovered:** 200
- **Image pairs processed:** 200
- **Unique image groups:** 200
- **Generated crops:** 43,899
- **Training crops:** 30,413
- **Validation crops:** 6,583
- **Test crops:** 6,903

The four target classes are:

```text
no-damage
minor-damage
major-damage
destroyed
```

---

# 8. Data Preprocessing

The preprocessing pipeline is implemented in:

```text
preprocess.py
```

Current configuration:

```text
Building crop size:        128 x 128
Bounding-box padding:      10 px
Minimum polygon dimension: 10 px
Train / Validation / Test: 70% / 15% / 15%
```

The preprocessing pipeline:

1. Loads the selected subset manifest.
2. Locates disaster imagery.
3. Matches pre- and post-disaster image pairs.
4. Reads building annotations.
5. Converts building polygons into crop regions.
6. Applies bounding-box padding.
7. Generates building-level crops.
8. Filters unsuitable annotations.
9. Associates samples with damage labels.
10. Produces train/validation/test manifests.

The current preprocessing run successfully generated **43,899 crops**.

Some annotations are skipped when they cannot be safely converted into valid training samples. The recorded run included skipped annotations caused by unmapped damage labels and small polygons.

---

# 9. Model Architecture

The current prototype uses a **Siamese ResNet-50** architecture.

## Why Siamese?

Disaster damage is fundamentally a **change-detection problem**.

Instead of examining only a post-disaster image, the system compares the building before and after the event:

```text
             PRE IMAGE
                 |
                 v
          Feature Encoder
                 |
                 +------+
                        |
                        v
                 Comparison
                        ^
                        |
                 +------+
                 |
                 v
          Feature Encoder
                 ^
                 |
             POST IMAGE
```

The paired architecture allows the model to learn representations associated with changes between the two observations.

## ResNet-50

ResNet-50 is used as the feature-extraction backbone.

The model receives paired building imagery and produces a classification over the four damage categories.

---

# 10. Training

Training is implemented in:

```text
train.py
```

The recorded training configuration was:

```text
Device:               CPU
Batch size:           8
Target epochs:        3
Learning rate:        0.0001
Checkpoint:           outputs/best_siamese_model.pth
```

The model supports checkpoint-based training.

### Epoch 2

```text
Train Loss: 0.6910
Train Accuracy: 73.65%

Validation Loss: 3.3370
Validation Accuracy: 69.60%
```

### Epoch 3

```text
Train Loss: 0.6226
Train Accuracy: 76.42%

Validation Loss: 1.0628
Validation Accuracy: 70.35%
```

Final recorded validation accuracy:

**70.35%**

---

# 11. Validation

Validation samples are not used directly to optimize the model parameters. They are used to monitor generalization during training.

The final recorded validation performance was:

**70.35% validation accuracy**

This is useful for monitoring whether training performance is translating to unseen validation samples.

---

# 12. Testing

Testing is implemented in:

```text
test.py
```

The current test run used:

```text
Test samples: 6,903
Checkpoint:   outputs/best_siamese_model.pth
Device:       CPU
```

Results:

```text
Test Loss:              1.0965
Test Accuracy:          65.91%
Correct Predictions:    4,550
Incorrect Predictions:  2,353
```

## Class-level performance

| Damage Class | Correct / Total | Accuracy |
|---|---:|---:|
| No Damage | 591 / 1,372 | 43.08% |
| Minor Damage | 1,878 / 3,065 | 61.27% |
| Major Damage | 881 / 1,165 | 75.62% |
| Destroyed | 1,200 / 1,301 | 92.24% |

These are the results of the current prototype checkpoint and should not be interpreted as production-level performance.

---

# 13. Confusion Matrix

Rows represent the actual class and columns represent the predicted class.

| Actual / Predicted | No Damage | Minor Damage | Major Damage | Destroyed |
|---|---:|---:|---:|---:|
| No Damage | 591 | 220 | 250 | 311 |
| Minor Damage | 74 | 1,878 | 809 | 304 |
| Major Damage | 9 | 120 | 881 | 155 |
| Destroyed | 7 | 24 | 70 | 1,200 |

The current results show strong performance for the `destroyed` category, while `no-damage` is considerably more difficult for the current model.

This helps identify where future model improvements should be concentrated.

---

# 14. Inference Pipeline

Inference is handled through:

```text
inference.py
```

Conceptually:

```text
PRE IMAGE
    +
POST IMAGE
    |
    v
Siamese ResNet-50
    |
    v
Damage Class
    +
Confidence
    |
    v
Backend
    |
    v
Web Application
```

The trained checkpoint is loaded and applied to new paired building imagery.

The resulting assessment is then made available to the backend and frontend.

---

# 15. Satellite Crop Engine

The satellite processing component is:

```text
satellite_crop_engine.py
```

Its purpose is to convert large-area imagery into building-level inputs.

```text
Large Pre-Disaster Image
           +
Large Post-Disaster Image
           |
           v
Building Localization / Crop Generation
           |
           v
Building PRE/POST Pairs
           |
           v
Model Inference
```

This component is important for making the system applicable to larger disaster scenes rather than requiring every building crop to be manually prepared.

---

# 16. Web Application Flow

The user-facing workflow is:

```text
Landing Page
      |
      v
Authentication
      |
      v
Assessment
      |
      +----------------------+
      |                      |
      v                      v
Satellite Mode         Direct Crop Mode
      |                      |
      +----------+-----------+
                 |
                 v
          Disaster Processing
                 |
                 v
          Building Results
                 |
       +---------+---------+
       |                   |
       v                   v
Building Details        History
       |
   +---+--------------------+
   |                        |
   v                        v
Explainable AI          Request Review
   |
   v
Building-context Chat
```

---

# 17. Building Detailed View

The building detailed view provides substantially more information than the summary building card.

It can contain:

- Building ID
- PRE-disaster image
- POST-disaster image
- Damage prediction
- Model confidence
- Available building/location information
- Assessment metadata
- Review information
- Explainable AI
- Building-specific AI chat

The detailed view is intended to give the user enough context to understand an individual assessment rather than only seeing a class and confidence value.

---

# 18. Explainable AI

The Explainable AI layer is focused on the **individual building currently being viewed**.

The application supplies relevant building context to Gemini:

```text
Building ID
Damage Class
Confidence
Available Building Data
Assessment Context
        |
        v
      Gemini
        |
        v
Natural-language explanation
```

The feature is intended to answer questions such as:

- Why was this building classified as major damage?
- What does the prediction mean?
- What changed between the two observations?
- What information contributed to the assessment?

The explanation should be grounded in the information supplied by the application and should not invent evidence that is not present.

---

# 19. Building-context AI Chat

The detailed building page includes an AI chatbox that is aware of the building currently selected.

The intended context includes:

- Building identifier
- Damage classification
- Confidence
- Available imagery context
- Available building metadata
- Assessment/review information

Example:

> **User:** Is it safe to be near this building?

The AI can explain the assessment context, but it must not be presented as a certified structural-safety determination.

For real-world deployment, safety-critical decisions must involve qualified professionals.

---

# 20. Human-in-the-Loop Review

The project does not treat AI predictions as unquestionable final decisions.

Where applicable:

```text
AI Prediction
      |
      v
Review Requested
      |
      v
Human Assessment
      |
      v
Reviewed / Final Decision
```

This provides a mechanism for important or uncertain cases to receive human attention.

---

# 21. Admin Dashboard

The Admin Dashboard provides administrative visibility over building assessments and review operations.

The admin building detail view is designed to contain the **same complete building information available in the user detailed view**, excluding the AI chatbox.

The admin workflow can distinguish between:

```text
AI Prediction
      |
      v
Model Confidence
      |
      v
Human Review
      |
      v
Admin Decision / Override
```

This separation is important because an AI prediction is not automatically equivalent to a human-reviewed final decision.

---

# 22. Project Structure

```text
Disaster-Assessment-Project/
│
├── backend/
│   ├── main.py
│   ├── config.py
│   │
│   ├── routes/
│   │   ├── admin.py
│   │   ├── assessment.py
│   │   ├── auth.py
│   │   ├── history.py
│   │   └── review.py
│   │
│   └── services/
│       ├── ai_service.py
│       └── mockapi_service.py
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   │
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── index.css
│       ├── config.js
│       ├── components/
│       │   ├── AdminDashboard.jsx
│       │   ├── AssessmentHistory.jsx
│       │   ├── AuthModals.jsx
│       │   ├── BuildingDetailModal.jsx
│       │   ├── BuildingGrid.jsx
│       │   ├── InputSelector.jsx
│       │   ├── LandingPage.jsx
│       │   ├── Navbar.jsx
│       │   ├── ProcessingScreen.jsx
│       │   ├── ResultsPage.jsx
│       │   └── StatisticsCards.jsx
│       └── assets/
│
├── data/
│   ├── raw/
│   │   └── xBD/
│   └── processed/
│
├── inference/
│
├── outputs/
│   ├── best_siamese_model.pth
│   ├── selected_200_subset.json
│   └── test_results.json
│
├── preprocess.py
├── train.py
├── test.py
├── inference.py
├── satellite_crop_engine.py
├── select_200_subset.py
├── select_balanced_subset.py
├── analyze_xbd_distribution.py
├── config.yaml
├── requirements.txt
├── .gitignore
└── README.md
```

The exact frontend component list can evolve during development; the structure above documents the project's major current modules.

---

# 23. Backend Structure

## `backend/main.py`

FastAPI application entry point. It starts the backend application and registers the API routes.

## `backend/config.py`

Central backend configuration.

## `backend/routes/auth.py`

Authentication-related endpoints and operations.

## `backend/routes/assessment.py`

Assessment-related API operations and connections to the inference workflow.

## `backend/routes/history.py`

Assessment history functionality.

## `backend/routes/review.py`

Human-review operations.

## `backend/routes/admin.py`

Administrative operations and review/override workflows.

## `backend/services/ai_service.py`

Gemini/AI integration used by Explainable AI and building-context AI functionality.

The Gemini API key must be supplied through environment configuration and never hardcoded into source code.

## `backend/services/mockapi_service.py`

Integration with the project's MockAPI-backed persistence layer.

---

# 24. Frontend Structure

The frontend uses **React + Vite**.

## `frontend/index.html`

HTML entry point and browser page metadata.

The application title is:

**Disaster Damage Assessment**

## `frontend/src/main.jsx`

React entry point and application mounting.

## `frontend/src/App.jsx`

Application-level UI and state flow.

## `frontend/src/components/`

Reusable UI components for:

- Landing page
- Navigation
- Authentication
- Input selection
- Processing
- Results
- Building details
- Statistics
- History
- Review
- Administration

## `frontend/src/index.css`

Global application styling.

---

# 25. API and MockAPI Integration

The frontend communicates with the FastAPI backend rather than implementing model logic directly.

```text
React
  |
  v
FastAPI
  |
  +------------------+
  |                  |
  v                  v
ML / AI Services   MockAPI
```

MockAPI acts as a lightweight persistence layer for the hackathon prototype.

This supports application features such as:

- User records
- Authentication-related data
- Assessment history
- Review workflow
- Administrative records

A production deployment would replace the prototype persistence layer with a robust database and object-storage architecture.

---

# 26. Installation

## Prerequisites

Recommended:

- Python 3.x
- Node.js
- npm
- Git

## Create the Python environment

From the project root:

```powershell
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.
env\Scripts\Activate.ps1
```

Install Python dependencies:

```powershell
pip install -r requirements.txt
```

## Install frontend dependencies

```powershell
cd frontend
npm install
```

---

# 27. Running the Project

## Backend

From the project root:

```powershell
.
env\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

## Frontend

In a second terminal:

```powershell
cd frontend
npm run dev
```

Frontend:

```text
http://localhost:5173/
```

The Vite configuration can proxy relevant frontend API paths to the FastAPI server.

---

# 28. Running the ML Pipeline

## Preprocessing

```powershell
python preprocess.py --config config.yaml --subset-manifest outputs/selected_200_subset.json
```

## Training

```powershell
python train.py
```

## Testing

```powershell
python test.py
```

Testing writes:

```text
outputs/test_results.json
```

---

# 29. Environment Variables and Secrets

Sensitive credentials must never be committed to GitHub.

The Gemini API key should be stored in a backend environment file such as:

```env
GEMINI_API_KEY=your_api_key_here
```

Never place the real key in:

- Python source code
- JavaScript source code
- README
- screenshots
- public frontend environment variables
- Git commits

If an API key is accidentally exposed or committed, it should be revoked/rotated.

---

# 30. Large Data and Git

The raw xBD dataset and generated image collections are large and should not normally be committed to GitHub.

The repository should contain the code and lightweight project metadata required to reproduce the workflow, while `.gitignore` should exclude large datasets, generated crops, caches, virtual environments, and other unnecessary artifacts.

The `.latentcode/` directory can remain tracked when required by the BuildSprint/LatentCode workflow.

---

# 31. Model Artifacts

Important model/evaluation artifacts include:

```text
outputs/
├── best_siamese_model.pth
├── selected_200_subset.json
└── test_results.json
```

The trained checkpoint contains the learned model parameters.

The test-results JSON contains the evaluation results generated by the testing pipeline.

---

# 32. Current Prototype Results

The current prototype reports:

```text
Validation Accuracy: 70.35%
Test Accuracy:       65.91%
```

Class-level test accuracy:

```text
No Damage:     43.08%
Minor Damage:  61.27%
Major Damage:  75.62%
Destroyed:     92.24%
```

These values reflect the current prototype configuration and selected dataset subset.

They should be presented honestly as prototype results rather than as production-grade performance.

---

# 33. Limitations

## Limited training subset

The current model was trained using a selected subset of the dataset. A larger and more diverse dataset would be required for stronger generalization.

## Uneven class performance

The current model performs much better on `destroyed` than on `no-damage`.

## Imagery quality

Performance depends on the availability and quality of pre- and post-disaster imagery.

Potential issues include:

- Cloud cover
- Occlusion
- Low resolution
- Missing imagery
- Misalignment
- Different imaging conditions

## Geographic generalization

Performance may vary when the system is applied to geographic regions or disaster types not adequately represented in training.

## Prototype infrastructure

MockAPI and local development services are appropriate for a hackathon prototype but are not a production-scale architecture.

## Structural safety

The system assesses visible damage from imagery. It is not a structural-engineering certification system.

AI responses to safety-related questions must therefore be treated as decision support and not as a guarantee that a structure is safe or unsafe.

---

# 34. Future Improvements

### Model

- Train on a larger portion of xBD.
- Improve class balancing.
- Tune hyperparameters.
- Experiment with stronger pretrained backbones.
- Improve data augmentation.
- Improve no-damage classification.
- Calibrate confidence scores.
- Evaluate performance across individual disaster types and geographic regions.

### Data

- Add more disaster types.
- Add more geographic diversity.
- Integrate additional satellite sources.
- Integrate higher-resolution aerial/drone imagery.
- Improve image alignment and image-quality validation.

### Explainability

- Add visual attribution/activation maps.
- Provide evidence-oriented explanations.
- Distinguish observed visual evidence from AI-generated interpretation.

### Infrastructure

- Replace MockAPI with a production database.
- Add object storage for imagery.
- Containerize services.
- Add GPU inference.
- Add asynchronous processing queues.
- Add monitoring and logging.

### Disaster-response integration

Future versions could provide:

- GIS map layers
- Damage heatmaps
- Priority-zone ranking
- Rescue-route planning
- Building-risk ranking
- Search and filtering
- Exportable assessment reports
- Emergency-management system integration

---

# 35. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Build Tool | Vite |
| Backend | FastAPI |
| Server | Uvicorn |
| ML Framework | PyTorch |
| Model | Siamese ResNet-50 |
| Dataset | xBD |
| Generative AI | Gemini API |
| Prototype Persistence | MockAPI |
| Languages | Python, JavaScript/JSX |
| Configuration | YAML, environment variables |
| AI-assisted Development | LatentCode |

---

# 36. Hackathon Context

This project is being developed during **BuildSprint 2026**.

The development workflow uses **LatentCode** as an AI-assisted development environment. It has enabled rapid iteration across the frontend, backend, API integration, debugging, Explainable AI, and application functionality.

The project demonstrates an end-to-end workflow rather than an isolated machine-learning model:

```text
Dataset
   ↓
Preprocessing
   ↓
Model Training
   ↓
Validation
   ↓
Testing
   ↓
Inference
   ↓
Backend API
   ↓
Web Application
   ↓
Building Assessment
   ↓
Explainable AI
   ↓
Human Review
   ↓
Admin Decision Support
```

---

# 37. End-to-End Summary

**Disaster Damage Assessment** is an AI-assisted disaster-response prototype that transforms pre- and post-disaster imagery into building-level structural damage assessments.

The system combines:

- xBD disaster imagery
- Building-level preprocessing
- Satellite crop generation
- Siamese ResNet-50
- Damage classification
- Confidence scoring
- FastAPI backend
- React web application
- Explainable AI
- Building-context AI chat
- Human-in-the-loop review
- Administrative review and override workflows

The long-term vision is to evolve the prototype into a robust disaster-intelligence platform that can help response teams rapidly identify damaged structures, prioritize inspection, understand model assessments, and make better-informed decisions after large-scale disasters.

---

## Disclaimer

This is a hackathon/research prototype.

Its model predictions and AI-generated explanations must not be treated as certified structural-safety assessments. Real-world emergency deployment would require larger and more diverse training data, extensive validation, domain-expert review, reliable imagery infrastructure, appropriate security controls, and compliance with relevant operational and safety requirements.
