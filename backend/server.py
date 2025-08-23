# ============================================================
# SafeTrack Backend (FastAPI)
# Author: [Your Name]
# Description: This is the backend API for the SafeTrack system,
# a student safety and emergency support application.
# 
# Key Features in this file:
# - MongoDB database connection
# - Authentication with JWT and password hashing
# - Student registration & login
# - Emergency alert creation & retrieval
# - Multilingual support (English & Bengali)
# ============================================================

# ------------------------------------------------------------
# Import dependencies
# --------------------------------------

from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
import asyncio
from bson import ObjectId

# ------------------------------------------------------------
# Load environment variables from .env file
# ------------------------------------------------------------

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ------------------------------------------------------------
# Database setup (MongoDB)
# ------------------------------------------------------------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'safetrack_secret_key_2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="SafeTrack API", description="Student Safety and Emergency Support System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Multilingual Support
translations = {
    "en": {
        "welcome": "Welcome to SafeTrack",
        "emergency_alert": "Emergency Alert",
        "profile_updated": "Profile updated successfully",
        "alert_created": "Emergency alert created successfully",
        "invalid_credentials": "Invalid credentials",
        "user_exists": "User already exists",
        "user_registered": "User registered successfully"
    },
    "bn": {
        "welcome": "SafeTrack এ স্বাগতম",
        "emergency_alert": "জরুরি সতর্কতা",
        "profile_updated": "প্রোফাইল সফলভাবে আপডেট হয়েছে",
        "alert_created": "জরুরি সতর্কতা সফলভাবে তৈরি হয়েছে",
        "invalid_credentials": "অবৈধ পরিচয়পত্র",
        "user_exists": "ব্যবহারকারী ইতিমধ্যে বিদ্যমান",
        "user_registered": "ব্যবহারকারী সফলভাবে নিবন্ধিত হয়েছে"
    }
}

def get_translation(key: str, lang: str = "en") -> str:
    return translations.get(lang, translations["en"]).get(key, key)

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id: str = payload.get("sub")
        if student_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user = await db.students.find_one({"student_id": student_id})
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        return Student(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Pydantic Models
class EmergencyContact(BaseModel):
    name: str
    relationship: str
    phone: str
    email: Optional[EmailStr] = None

class Student(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    student_id: str
    email: EmailStr
    blood_group: str
    emergency_contacts: List[EmergencyContact] = []
    location: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_admin: bool = False

class StudentCreate(BaseModel):
    name: str
    student_id: str
    email: EmailStr
    password: str
    blood_group: str
    emergency_contacts: List[EmergencyContact] = []
    location: Optional[str] = None

class StudentLogin(BaseModel):
    student_id: str
    password: str

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contacts: Optional[List[EmergencyContact]] = None
    location: Optional[str] = None

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    student_name: str
    student_email: str
    blood_group: str
    emergency_contacts: List[EmergencyContact]
    location: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "active"  # active, resolved
    message: Optional[str] = None

class AlertCreate(BaseModel):
    message: Optional[str] = None

class AlertUpdate(BaseModel):
    status: str
    resolved_by: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Student

class ApiResponse(BaseModel):
    message: str
    data: Optional[Dict] = None
    lang: str = "en"

# Status endpoint
@api_router.get("/status")
async def get_api_status():
    return {"message": "SafeTrack API is running", "status": "healthy", "timestamp": datetime.now(timezone.utc)}

# Authentication endpoints
@api_router.post("/auth/register", response_model=ApiResponse)
async def register_student(student: StudentCreate, lang: str = "en"):
    # Check if user already exists
    existing_user = await db.students.find_one({"student_id": student.student_id})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_translation("user_exists", lang)
        )
    
    # Hash password
    hashed_password = hash_password(student.password)
    
    # Create student document
    student_dict = student.dict(exclude={"password"})
    student_dict["password_hash"] = hashed_password
    student_dict["id"] = str(uuid.uuid4())
    student_dict["created_at"] = datetime.now(timezone.utc)
    student_dict["is_admin"] = False
    
    # Insert into database
    await db.students.insert_one(student_dict)
    
    return ApiResponse(
        message=get_translation("user_registered", lang),
        data={"student_id": student.student_id},
        lang=lang
    )

@api_router.post("/auth/login", response_model=Token)
async def login_student(login_data: StudentLogin, lang: str = "en"):
    # Find user
    user = await db.students.find_one({"student_id": login_data.student_id})
    if not user or not verify_password(login_data.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_translation("invalid_credentials", lang)
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["student_id"]})
    
    # Prepare user data (exclude password_hash)
    user_data = {k: v for k, v in user.items() if k != "password_hash" and k != "_id"}
    student_obj = Student(**user_data)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=student_obj
    )

# Student endpoints
@api_router.get("/students/me", response_model=Student)
async def get_current_student_profile(current_user: Student = Depends(get_current_user)):
    return current_user

@api_router.put("/students/me", response_model=ApiResponse)
async def update_student_profile(
    student_update: StudentUpdate,
    current_user: Student = Depends(get_current_user),
    lang: str = "en"
):
    # Update student data
    update_data = {k: v for k, v in student_update.dict().items() if v is not None}
    if update_data:
        await db.students.update_one(
            {"student_id": current_user.student_id},
            {"$set": update_data}
        )
    
    return ApiResponse(
        message=get_translation("profile_updated", lang),
        lang=lang
    )

@api_router.get("/students", response_model=List[Student])
async def get_all_students(current_user: Student = Depends(get_current_user)):
    # Only admin can view all students
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    students = await db.students.find({}, {"password_hash": 0}).to_list(1000)
    return [Student(**{k: v for k, v in student.items() if k != "_id"}) for student in students]

# Alert endpoints
@api_router.post("/alerts", response_model=ApiResponse)
async def create_emergency_alert(
    alert_data: AlertCreate,
    current_user: Student = Depends(get_current_user),
    lang: str = "en"
):
    # Create alert with student information
    alert_dict = {
        "id": str(uuid.uuid4()),
        "student_id": current_user.student_id,
        "student_name": current_user.name,
        "student_email": current_user.email,
        "blood_group": current_user.blood_group,
        "emergency_contacts": [contact.dict() for contact in current_user.emergency_contacts],
        "location": current_user.location,
        "timestamp": datetime.now(timezone.utc),
        "status": "active",
        "message": alert_data.message
    }
    
    # Insert alert into database
    await db.alerts.insert_one(alert_dict)
    
    return ApiResponse(
        message=get_translation("alert_created", lang),
        data={"alert_id": alert_dict["id"]},
        lang=lang
    )

@api_router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    status_filter: Optional[str] = "active",
    current_user: Student = Depends(get_current_user)
):
    # Build query
    query = {}
    if status_filter:
        query["status"] = status_filter
    
    # If not admin, only show user's own alerts
    if not current_user.is_admin:
        query["student_id"] = current_user.student_id
    
    alerts = await db.alerts.find(query).sort("timestamp", -1).to_list(1000)
    return [Alert(**{k: v for k, v in alert.items() if k != "_id"}) for alert in alerts]

@api_router.get("/alerts/active", response_model=List[Alert])
async def get_active_alerts(current_user: Student = Depends(get_current_user)):
    # Only admin can view all active alerts
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    alerts = await db.alerts.find({"status": "active"}).sort("timestamp", -1).to_list(1000)
    return [Alert(**{k: v for k, v in alert.items() if k != "_id"}) for alert in alerts]

@api_router.put("/alerts/{alert_id}", response_model=ApiResponse)
async def update_alert_status(
    alert_id: str,
    alert_update: AlertUpdate,
    current_user: Student = Depends(get_current_user),
    lang: str = "en"
):
    # Only admin can update alert status
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    # Update alert
    update_data = alert_update.dict()
    if alert_update.status == "resolved":
        update_data["resolved_at"] = datetime.now(timezone.utc)
        update_data["resolved_by"] = current_user.student_id
    
    result = await db.alerts.update_one(
        {"id": alert_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    return ApiResponse(message="Alert updated successfully", lang=lang)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Create admin user on startup
@app.on_event("startup")
async def create_admin_user():
    # Check if admin exists
    admin_exists = await db.students.find_one({"student_id": "admin"})
    if not admin_exists:
        admin_user = {
            "id": str(uuid.uuid4()),
            "name": "System Administrator",
            "student_id": "admin",
            "email": "admin@safetrack.com",
            "password_hash": hash_password("admin123"),
            "blood_group": "Unknown",
            "emergency_contacts": [],
            "location": "Admin Office",
            "created_at": datetime.now(timezone.utc),
            "is_admin": True
        }
        await db.students.insert_one(admin_user)
        logger.info("Admin user created with ID: admin, Password: admin123")