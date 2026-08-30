from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from backend.services.mockapi_service import mockapi_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

@router.post("/login")
async def login(req: LoginRequest):
    user = await mockapi_service.get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    
    if str(user.get("PASSWORD")) != str(req.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    return {
        "id": user["id"],
        "name": user.get("NAME"),
        "email": user.get("EMAIL"),
        "role": user.get("ROLE", "user")
    }

@router.post("/signup")
async def signup(req: SignupRequest):
    existing = await mockapi_service.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered.")

    new_user = await mockapi_service.create_user(
        name=req.name,
        email=req.email,
        password=req.password,
        role="user"
    )

    return {
        "id": new_user["id"],
        "name": new_user.get("NAME"),
        "email": new_user.get("EMAIL"),
        "role": new_user.get("ROLE", "user")
    }
