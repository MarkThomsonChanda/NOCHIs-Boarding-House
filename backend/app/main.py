import os
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env")
db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="NOCHIs Boarding House API", version="1.0.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

def current_user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Sign in first.")
    token = authorization.split(" ", 1)[1]
    try:
        user = db.auth.get_user(token).user
        if not user:
            raise ValueError()
        return user
    except Exception:
        raise HTTPException(401, "Invalid or expired login session.")

def profile(user):
    result = db.table("profiles").select("*").eq("id", user.id).single().execute()
    if not result.data:
        raise HTTPException(404, "Profile not found.")
    return result.data

def owner(user=Depends(current_user)):
    p = profile(user)
    if p.get("role") != "owner":
        raise HTTPException(403, "Owner access required.")
    return user

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

@app.get("/")
def health():
    return {"service": "NOCHIs Boarding House API", "status": "ok"}

@app.get("/api/me")
def me(user=Depends(current_user)):
    return profile(user)

@app.put("/api/me")
def update_me(payload: ProfileIn, user=Depends(current_user)):
    data = payload.model_dump()
    result = db.table("profiles").update(data).eq("id", user.id).execute()
    return result.data[0] if result.data else data

@app.get("/api/rooms")
def rooms(user=Depends(current_user)):
    all_rooms = db.table("rooms").select("*").order("room_number").execute().data
    allocations = db.table("room_allocations").select("room_number").execute().data
    counts = {}
    for a in allocations:
        counts[a["room_number"]] = counts.get(a["room_number"], 0) + 1
    return [{**r, "occupied": counts.get(r["room_number"],0),
             "available_spaces": max(0,r["capacity"]-counts.get(r["room_number"],0))}
            for r in all_rooms]

@app.post("/api/applications")
def apply(payload: ApplicationIn, user=Depends(current_user)):
    room = db.table("rooms").select("*").eq("room_number",payload.requested_room).single().execute().data
    if not room:
        raise HTTPException(404,"Room not found.")
    allocation = db.table("room_allocations").select("id").eq("student_id",user.id).execute().data
    if allocation:
        raise HTTPException(409,"You already have an allocated room.")
    result = db.table("room_applications").insert({"student_id":user.id,"requested_room":payload.requested_room}).execute()
    return result.data[0]

@app.get("/api/my-room")
def my_room(user=Depends(current_user)):
    result = db.table("room_allocations").select("*, rooms(*)").eq("student_id",user.id).execute()
    return result.data[0] if result.data else None

@app.get("/api/my-applications")
def my_applications(user=Depends(current_user)):
    return db.table("room_applications").select("*").eq("student_id",user.id).order("created_at",desc=True).execute().data

@app.get("/api/payments")
def my_payments(user=Depends(current_user)):
    return db.table("payments").select("*").eq("student_id",user.id).order("payment_date",desc=True).execute().data

@app.post("/api/swaps")
def request_swap(payload: SwapIn, user=Depends(current_user)):
    current = db.table("room_allocations").select("*").eq("student_id",user.id).execute().data
    if not current:
        raise HTTPException(400,"You need an allocated room before requesting a swap.")
    if current[0]["room_number"] == payload.requested_room:
        raise HTTPException(400,"Choose a different room.")
    return db.table("room_swap_requests").insert({
        "student_id":user.id,"current_room":current[0]["room_number"],
        "requested_room":payload.requested_room,"reason":payload.reason
    }).execute().data[0]

@app.get("/api/admin/overview")
def admin_overview(user=Depends(owner)):
    students = db.table("profiles").select("id",count="exact").eq("role","student").execute()
    apps = db.table("room_applications").select("id",count="exact").eq("status","pending").execute()
    allocations = db.table("room_allocations").select("id",count="exact").execute()
    payments = db.table("payments").select("amount_kwacha").eq("status","recorded").execute().data
    return {"students":students.count or 0,"pending_applications":apps.count or 0,
            "allocated_students":allocations.count or 0,
            "recorded_payments":sum(float(p["amount_kwacha"]) for p in payments)}

@app.get("/api/admin/applications")
def admin_applications(user=Depends(owner)):
    return db.table("room_applications").select("*, profiles(full_name,phone), rooms(*)").order("created_at",desc=True).execute().data

@app.post("/api/admin/applications/{application_id}/review")
def review_application(application_id: UUID, decision: str, user=Depends(owner)):
    if decision not in ("approve","reject"):
        raise HTTPException(400,"decision must be approve or reject")
    app_data = db.table("room_applications").select("*").eq("id",str(application_id)).single().execute().data
    if not app_data or app_data["status"] != "pending":
        raise HTTPException(404,"Pending application not found.")
    if decision == "approve":
        room_num = app_data["requested_room"]
        room = db.table("rooms").select("*").eq("room_number",room_num).single().execute().data
        occupied = db.table("room_allocations").select("id").eq("room_number",room_num).execute().data
        if len(occupied) >= room["capacity"]:
            raise HTTPException(409,"That room is full.")
        existing = db.table("room_allocations").select("id").eq("student_id",app_data["student_id"]).execute().data
        if existing:
            raise HTTPException(409,"Student already has a room.")
        db.table("room_allocations").insert({"student_id":app_data["student_id"],"room_number":room_num}).execute()
        status = "approved"
    else:
        status = "rejected"
    return db.table("room_applications").update({"status":status,"reviewed_at":datetime.now(timezone.utc).isoformat()}).eq("id",str(application_id)).execute().data[0]

@app.post("/api/admin/payments")
def record_payment(payload: PaymentIn, user=Depends(owner)):
    data = payload.model_dump()
    data["payment_date"] = data["payment_date"].isoformat()
    data["recorded_by"] = user.id
    return db.table("payments").insert(data).execute().data[0]

@app.get("/api/admin/swaps")
def admin_swaps(user=Depends(owner)):
    return db.table("room_swap_requests").select("*, profiles(full_name,phone)").eq("status","pending").execute().data

@app.post("/api/admin/swaps/{swap_id}/review")
def review_swap(swap_id: UUID, decision: str, user=Depends(owner)):
    if decision not in ("approve","reject"):
        raise HTTPException(400,"decision must be approve or reject")
    req = db.table("room_swap_requests").select("*").eq("id",str(swap_id)).single().execute().data
    if not req or req["status"] != "pending":
        raise HTTPException(404,"Pending swap request not found.")
    if decision == "approve":
        room = db.table("rooms").select("*").eq("room_number",req["requested_room"]).single().execute().data
        occupied = db.table("room_allocations").select("id").eq("room_number",req["requested_room"]).execute().data
        if len(occupied) >= room["capacity"]:
            raise HTTPException(409,"Requested room is full.")
        db.table("room_allocations").update({"room_number":req["requested_room"]}).eq("student_id",req["student_id"]).execute()
    return db.table("room_swap_requests").update({"status":"approved" if decision=="approve" else "rejected",
        "reviewed_at":datetime.now(timezone.utc).isoformat()}).eq("id",str(swap_id)).execute().data[0]
