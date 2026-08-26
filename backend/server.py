
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
import notifications
import monitoring
import photo_storage
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, WebSocket, WebSocketDisconnect, UploadFile, File

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

# ------------------------------------------------------------
# Rate limiting
# ------------------------------------------------------------
# Limits requests per client IP to stop abuse of the alert system
# (e.g. someone flooding fake emergency alerts) and to slow down
# brute-force login attempts. Limits are generous enough that a
# real student in genuine distress is never blocked.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Multilingual Support — powered by Azure Translator (see translation.py).
# Supports any language Azure Translator offers (100+), not just English/Bengali.
from translation import get_translation

# ------------------------------------------------
# Password hashing utilities
# ------------------------------------------------
# These functions handle secure password storage
# and verification using bcrypt

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ------------------------------------------------
# JWT Token creation
# ------------------------------------------------
# Creates signed JWT tokens for authentication

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

# ------------------------------------------------------------
# Real-time push (WebSockets)
# ------------------------------------------------------------
# Admins connect once and get pushed new/updated alerts instantly,
# instead of polling the API or relying only on email. This never
# blocks the underlying alert flow — a failed broadcast to one admin
# just means that admin misses the live push (they'll still see it
# on refresh), it never fails the alert creation itself.

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

async def get_admin_from_ws_token(token: str) -> Optional["Student"]:
    """Validates a JWT passed as a query param on the WebSocket handshake
    (browsers can't send Authorization headers on ws:// connections) and
    confirms the user is an admin. Returns None on any failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id: str = payload.get("sub")
        if student_id is None:
            return None
        user = await db.students.find_one({"student_id": student_id})
        if user is None or not user.get("is_admin"):
            return None
        return Student(**user)
    except jwt.PyJWTError:
        return None

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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_sos: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "active"  # active, resolved
    message: Optional[str] = None
    photo_url: Optional[str] = None

class AlertCreate(BaseModel):
    message: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class SOSCreate(BaseModel):
    # One-tap SOS: only GPS coordinates are required. Everything else
    # (name, blood group, contacts) is pulled from the student's profile
    # automatically so there's nothing to type in an emergency.
    latitude: Optional[float] = None
    longitude: Optional[float] = None

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

@api_router.get("/languages")
async def get_supported_languages():
    """A curated shortlist for the frontend's language picker. Azure
    Translator supports 100+ languages; any valid ISO code works even
    if it's not in this list — this is just what's shown by default."""
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "bn", "name": "বাংলা (Bengali)"},
            {"code": "hi", "name": "हिन्दी (Hindi)"},
            {"code": "ur", "name": "اردو (Urdu)"},
            {"code": "es", "name": "Español (Spanish)"},
            {"code": "fr", "name": "Français (French)"},
            {"code": "ar", "name": "العربية (Arabic)"},
            {"code": "zh-Hans", "name": "中文 (Chinese)"},
            {"code": "pa", "name": "ਪੰਜਾਬੀ (Punjabi)"},
            {"code": "tl", "name": "Tagalog"},
        ]
    }

# -------------------------------------------------
# Authentication routes
# -------------------------------------------------
# /register -> for new student signup
# /login -> verify credentials and return JWT

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
@limiter.limit("10/minute")
async def login_student(request: Request, login_data: StudentLogin, lang: str = "en"):
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

# -------------------------------------------------
# Student profile management
# -------------------------------------------------
# Handles creating, updating, and retrieving student info
# Includes student ID, blood group, emergency contacts

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

# -------------------------------------------------
# Emergency alerts
# -------------------------------------------------
# Students can create alerts that include their profile info
# (ID, name, email, blood group, contacts, location, timestamp).
# Admins can view all alerts (active/resolved) and update their status.
# Non-admin students can only view their own alerts.

@api_router.post("/alerts", response_model=ApiResponse)
@limiter.limit("5/minute")
async def create_emergency_alert(
    request: Request,
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
        "latitude": alert_data.latitude,
        "longitude": alert_data.longitude,
        "is_sos": False,
        "timestamp": datetime.now(timezone.utc),
        "status": "active",
        "message": alert_data.message
    }
    
    # Insert alert into database
    await db.alerts.insert_one(alert_dict)
    
    # Notify admins by email. This never blocks or fails the alert itself —
    # the alert record is already saved above regardless of email outcome.
    await notifications.notify_new_alert(
        student_name=current_user.name,
        student_id=current_user.student_id,
        location=current_user.location,
        message=alert_data.message,
        alert_id=alert_dict["id"],
        lang=lang,
        latitude=alert_data.latitude,
        longitude=alert_data.longitude,
    )

    # Push to any connected admins in real time. Soft-fail by design —
    # a broadcast failure never affects the alert record already saved.
    await manager.broadcast({
        "event": "new_alert",
        "alert": {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in alert_dict.items() if k != "_id"}
    })

    monitoring.track_event("alert_created", {
        "is_sos": False,
        "has_location": bool(alert_data.latitude and alert_data.longitude),
        "lang": lang,
    })
    
    return ApiResponse(
        message=get_translation("alert_created", lang),
        data={"alert_id": alert_dict["id"]},
        lang=lang
    )

@api_router.post("/alerts/sos", response_model=ApiResponse)
@limiter.limit("5/minute")
async def create_sos_alert(
    request: Request,
    sos_data: SOSCreate,
    current_user: Student = Depends(get_current_user),
    lang: str = "en"
):
    """One-tap SOS: creates an emergency alert instantly using the
    student's profile info, with no typing required. Intended for the
    big red 'SOS' button in the app — GPS coordinates are auto-captured
    by the frontend and sent here directly."""
    alert_dict = {
        "id": str(uuid.uuid4()),
        "student_id": current_user.student_id,
        "student_name": current_user.name,
        "student_email": current_user.email,
        "blood_group": current_user.blood_group,
        "emergency_contacts": [contact.dict() for contact in current_user.emergency_contacts],
        "location": current_user.location,
        "latitude": sos_data.latitude,
        "longitude": sos_data.longitude,
        "is_sos": True,
        "timestamp": datetime.now(timezone.utc),
        "status": "active",
        "message": "🆘 SOS — one-tap emergency alert"
    }

    await db.alerts.insert_one(alert_dict)

    # SOS alerts are the highest-urgency case — always notify admins,
    # same soft-fail behavior as regular alerts.
    await notifications.notify_new_alert(
        student_name=current_user.name,
        student_id=current_user.student_id,
        location=current_user.location,
        message=alert_dict["message"],
        alert_id=alert_dict["id"],
        lang=lang,
        latitude=sos_data.latitude,
        longitude=sos_data.longitude,
    )

    await manager.broadcast({
        "event": "new_alert",
        "alert": {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in alert_dict.items() if k != "_id"}
    })

    monitoring.track_event("sos_triggered", {
        "is_sos": True,
        "has_location": bool(sos_data.latitude and sos_data.longitude),
        "lang": lang,
    })

    return ApiResponse(
        message=get_translation("alert_created", lang),
        data={"alert_id": alert_dict["id"]},
        lang=lang
    )

@api_router.post("/alerts/{alert_id}/photo", response_model=ApiResponse)
@limiter.limit("10/minute")
async def upload_alert_photo(
    request: Request,
    alert_id: str,
    photo: UploadFile = File(...),
    current_user: Student = Depends(get_current_user),
    lang: str = "en"
):
    """Attach a photo to an existing alert (evidence of an injury, hazard,
    or the scene). Only the alert's own reporter or an admin can attach a
    photo. If photo storage isn't configured or the upload fails, the
    endpoint still returns success for the alert itself — the photo is
    an enhancement, never a blocker for a safety-critical report."""
    alert = await db.alerts.find_one({"id": alert_id})
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    if alert.get("student_id") != current_user.student_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this alert")

    file_bytes = await photo.read()
    photo_url = await photo_storage.upload_alert_photo(
        file_bytes=file_bytes,
        content_type=photo.content_type,
        alert_id=alert_id,
    )

    if photo_url is None:
        return ApiResponse(
            message="Alert saved, but photo upload was unavailable",
            data={"alert_id": alert_id, "photo_url": None},
            lang=lang
        )

    await db.alerts.update_one({"id": alert_id}, {"$set": {"photo_url": photo_url}})

    await manager.broadcast({
        "event": "alert_updated",
        "alert_id": alert_id,
        "photo_url": photo_url,
    })

    monitoring.track_event("alert_photo_uploaded", {"alert_id": alert_id})

    return ApiResponse(
        message="Photo attached successfully",
        data={"alert_id": alert_id, "photo_url": photo_url},
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

@api_router.get("/analytics")
async def get_analytics(
    days: int = 30,
    current_user: Student = Depends(get_current_user)
):
    """Admin-only dashboard data: resolution rate, average response time,
    daily alert volume, and SOS vs. regular alert breakdown over the
    given window (default 30 days)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    alerts = await db.alerts.find({"timestamp": {"$gte": since}}).to_list(10000)

    total = len(alerts)
    resolved = [a for a in alerts if a.get("status") == "resolved"]
    active = total - len(resolved)
    sos_count = sum(1 for a in alerts if a.get("is_sos"))

    # Average response time = time between alert creation and resolution,
    # for alerts that have both timestamps recorded.
    response_times_seconds = []
    for a in resolved:
        created = a.get("timestamp")
        resolved_at = a.get("resolved_at")
        if created and resolved_at:
            # Mongo may return naive datetimes; normalize to UTC-aware
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if resolved_at.tzinfo is None:
                resolved_at = resolved_at.replace(tzinfo=timezone.utc)
            response_times_seconds.append((resolved_at - created).total_seconds())

    avg_response_seconds = (
        sum(response_times_seconds) / len(response_times_seconds)
        if response_times_seconds else None
    )

    # Daily alert volume, oldest to newest, for a simple trend chart.
    daily_counts: Dict[str, int] = {}
    for a in alerts:
        ts = a.get("timestamp")
        if ts:
            day_key = ts.strftime("%Y-%m-%d")
            daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
    daily_trend = [{"date": d, "count": c} for d, c in sorted(daily_counts.items())]

    return {
        "window_days": days,
        "total_alerts": total,
        "active_alerts": active,
        "resolved_alerts": len(resolved),
        "resolution_rate": round(len(resolved) / total, 3) if total else None,
        "sos_alerts": sos_count,
        "avg_response_time_seconds": (
            round(avg_response_seconds, 1) if avg_response_seconds is not None else None
        ),
        "daily_trend": daily_trend,
    }

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
    
    # Fetch the alert first so we have the student's email/name for notification
    existing_alert = await db.alerts.find_one({"id": alert_id})
    if existing_alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    result = await db.alerts.update_one(
        {"id": alert_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    # Notify the reporting student of the status change. Never blocks the response.
    await notifications.notify_alert_status_change(
        student_email=existing_alert.get("student_email", ""),
        student_name=existing_alert.get("student_name", "Student"),
        new_status=alert_update.status,
        alert_id=alert_id,
        lang=lang,
    )

    # Push the status change to all connected admin dashboards.
    await manager.broadcast({
        "event": "alert_updated",
        "alert_id": alert_id,
        "status": alert_update.status,
    })

    if alert_update.status == "resolved":
        created = existing_alert.get("timestamp")
        response_seconds = None
        if created:
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            response_seconds = (datetime.now(timezone.utc) - created).total_seconds()
        monitoring.track_event("alert_resolved", {
            "is_sos": existing_alert.get("is_sos", False),
            "response_seconds": response_seconds,
        })
    
    return ApiResponse(message="Alert updated successfully", lang=lang)

# Include the router in the main app
app.include_router(api_router)

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket, token: str = ""):
    """Admins connect here (with their JWT as a ?token= query param) to
    receive new/updated alerts in real time. Non-admins and invalid
    tokens are rejected before the connection is accepted."""
    admin_user = await get_admin_from_ws_token(token)
    if admin_user is None:
        await websocket.close(code=4401)  # custom code: unauthorized
        return

    await manager.connect(websocket)
    try:
        while True:
            # We don't expect incoming messages, but need to keep the
            # loop alive to detect disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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


  # ------------------------------------------------------------
# Multilingual support (English & Bengali) — Design Notes
# ------------------------------------------------------------
# Goal: Allow clients to request responses in English or Bengali
# using a query param (?lang=en or ?lang=bn) without changing
# core business logic.
#
# Sketch:
# SUPPORTED_LANGS = {"en", "bn"}
# TRANSLATIONS = {
#   "en": {"alert_created": "Emergency alert created",
#          "active": "active", "resolved": "resolved"},
#   "bn": {"alert_created": "জরুরি সতর্কতা তৈরি হয়েছে",
#          "active": "চলমান", "resolved": "সমাধান হয়েছে"}
# }
#
# Helper (pseudo):
# def t(key: str, lang: str) -> str:
#     lang = lang if lang in SUPPORTED_LANGS else "en"
#     return TRANSLATIONS[lang].get(key, key)
#
# Usage idea:
# - When creating an alert, return {"message": t("alert_created", lang)}
# - When listing alerts, map each `status` through t(status, lang)
#
# Notes:
# - Keep translations in a small dict for now; later can move to /locales/*.json
# - Default to English when ?lang is missing/invalid
# - This design keeps API stable and adds i18n progressivelydo in