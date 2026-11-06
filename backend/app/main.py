import os
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client, Client

# ==========================================
# CONFIGURATION
# ==========================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env"
    )

db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="NOCHIs Boarding House API",
    description="Boarding House Management System",
    version="2.0.0"
)

origins = [
    x.strip()
    for x in os.getenv("CORS_ORIGINS", "*").split(",")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# AUTHENTICATION
# ==========================================

def current_user(
    authorization: Optional[str] = Header(
        default=None,
        alias="Authorization"
    )
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is missing."
        )

    parts = authorization.strip().split(None, 1)

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format."
        )

    token = parts[1].strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication token is empty."
        )

    try:
        response = db.auth.get_user(token)
        user = response.user

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid login session."
            )

        return user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired login session."
        )


# ==========================================
# USER PROFILE
# ==========================================

def profile(user):
    result = (
        db.table("profiles")
        .select("*")
        .eq("id", str(user.id))
        .maybe_single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Profile not found."
        )

    return result.data


def owner(user=Depends(current_user)):
    p = profile(user)

    if p.get("role") != "owner":
        raise HTTPException(
            status_code=403,
            detail="Owner access required."
        )

    return user


# ==========================================
# DATA MODELS
# ==========================================

class ApplicationIn(BaseModel):
    requested_room: int


class ProfileIn(BaseModel):
    full_name: str = ""
    nrc_number: str = ""
    phone: str = ""
    residential_address: str = ""
    guardian_name: str = ""
    guardian_phone: str = ""
    profile_picture_url: str = ""


class PaymentIn(BaseModel):
    student_id: str
    amount_kwacha: float = Field(gt=0)
    payment_date: date
    payment_method: str = ""
    reference: str = ""
    notes: str = ""


class SwapIn(BaseModel):
    requested_room: int
    reason: str = ""


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/")
def health():
    return {
        "service": "NOCHIs Boarding House API",
        "status": "ok"
    }


# ==========================================
# STUDENT PROFILE
# ==========================================

@app.get("/api/me")
def me(user=Depends(current_user)):
    return profile(user)


@app.put("/api/me")
def update_me(
    payload: ProfileIn,
    user=Depends(current_user)
):
    data = payload.model_dump()

    result = (
        db.table("profiles")
        .update(data)
        .eq("id", str(user.id))
        .execute()
    )

    return result.data[0] if result.data else data


# ==========================================
# ROOMS
# ==========================================

@app.get("/api/rooms")
def rooms(user=Depends(current_user)):

    all_rooms = (
        db.table("rooms")
        .select("*")
        .order("room_number")
        .execute()
        .data
    )

    allocations = (
        db.table("room_allocations")
        .select("room_number")
        .execute()
        .data
    )

    counts = {}

    for allocation in allocations:
        room_number = allocation["room_number"]

        counts[room_number] = (
            counts.get(room_number, 0) + 1
        )

    return [
        {
            **room,
            "occupied": counts.get(room["room_number"], 0),
            "available_spaces": max(
                0,
                room["capacity"] - counts.get(
                    room["room_number"], 0
                )
            )
        }
        for room in all_rooms
    ]


# ==========================================
# ROOM APPLICATIONS
# ==========================================

@app.post("/api/applications")
def apply(
    payload: ApplicationIn,
    user=Depends(current_user)
):

    room_result = (
        db.table("rooms")
        .select("*")
        .eq("room_number", payload.requested_room)
        .maybe_single()
        .execute()
    )

    room = room_result.data

    if not room:
        raise HTTPException(404, "Room not found.")

    allocation = (
        db.table("room_allocations")
        .select("id")
        .eq("student_id", str(user.id))
        .execute()
        .data
    )

    if allocation:
        raise HTTPException(
            409,
            "You already have an allocated room."
        )

    existing = (
        db.table("room_applications")
        .select("id")
        .eq("student_id", str(user.id))
        .eq("status", "pending")
        .execute()
        .data
    )

    if existing:
        raise HTTPException(
            409,
            "You already have a pending application."
        )

    result = (
        db.table("room_applications")
        .insert({
            "student_id": str(user.id),
            "requested_room": payload.requested_room
        })
        .execute)
