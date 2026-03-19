"""Slalom Capabilities Management System API."""

import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Slalom Capabilities Management API",
              description="API for managing consulting capabilities and consultant expertise")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

PRACTICE_LEADS_FILE = current_dir / "practice_leads.json"
SESSION_COOKIE_NAME = "slalom_session"
SESSION_MAX_AGE_SECONDS = 8 * 60 * 60
PASSWORD_HASH_ITERATIONS = 120000

# In-memory capabilities database
capabilities = {
    "Cloud Architecture": {
        "description": "Design and implement scalable cloud solutions using AWS, Azure, and GCP",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["AWS Solutions Architect", "Azure Architect Expert"],
        "industry_verticals": ["Healthcare", "Financial Services", "Retail"],
        "capacity": 40,  # hours per week available across team
        "consultants": ["alice.smith@slalom.com", "bob.johnson@slalom.com"]
    },
    "Data Analytics": {
        "description": "Advanced data analysis, visualization, and machine learning solutions",
        "practice_area": "Technology", 
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Tableau Desktop Specialist", "Power BI Expert", "Google Analytics"],
        "industry_verticals": ["Retail", "Healthcare", "Manufacturing"],
        "capacity": 35,
        "consultants": ["emma.davis@slalom.com", "sophia.wilson@slalom.com"]
    },
    "DevOps Engineering": {
        "description": "CI/CD pipeline design, infrastructure automation, and containerization",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"], 
        "certifications": ["Docker Certified Associate", "Kubernetes Admin", "Jenkins Certified"],
        "industry_verticals": ["Technology", "Financial Services"],
        "capacity": 30,
        "consultants": ["john.brown@slalom.com", "olivia.taylor@slalom.com"]
    },
    "Digital Strategy": {
        "description": "Digital transformation planning and strategic technology roadmaps",
        "practice_area": "Strategy",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Digital Transformation Certificate", "Agile Certified Practitioner"],
        "industry_verticals": ["Healthcare", "Financial Services", "Government"],
        "capacity": 25,
        "consultants": ["liam.anderson@slalom.com", "noah.martinez@slalom.com"]
    },
    "Change Management": {
        "description": "Organizational change leadership and adoption strategies",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Prosci Certified", "Lean Six Sigma Black Belt"],
        "industry_verticals": ["Healthcare", "Manufacturing", "Government"],
        "capacity": 20,
        "consultants": ["ava.garcia@slalom.com", "mia.rodriguez@slalom.com"]
    },
    "UX/UI Design": {
        "description": "User experience design and digital product innovation",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Adobe Certified Expert", "Google UX Design Certificate"],
        "industry_verticals": ["Retail", "Healthcare", "Technology"],
        "capacity": 30,
        "consultants": ["amelia.lee@slalom.com", "harper.white@slalom.com"]
    },
    "Cybersecurity": {
        "description": "Information security strategy, risk assessment, and compliance",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["CISSP", "CISM", "CompTIA Security+"],
        "industry_verticals": ["Financial Services", "Healthcare", "Government"],
        "capacity": 25,
        "consultants": ["ella.clark@slalom.com", "scarlett.lewis@slalom.com"]
    },
    "Business Intelligence": {
        "description": "Enterprise reporting, data warehousing, and business analytics",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Microsoft BI Certification", "Qlik Sense Certified"],
        "industry_verticals": ["Retail", "Manufacturing", "Financial Services"],
        "capacity": 35,
        "consultants": ["james.walker@slalom.com", "benjamin.hall@slalom.com"]
    },
    "Agile Coaching": {
        "description": "Agile transformation and team coaching for scaled delivery",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Certified Scrum Master", "SAFe Agilist", "ICAgile Certified"],
        "industry_verticals": ["Technology", "Financial Services", "Healthcare"],
        "capacity": 20,
        "consultants": ["charlotte.young@slalom.com", "henry.king@slalom.com"]
    }
}

pending_requests = {capability_name: [] for capability_name in capabilities}
sessions: dict[str, dict[str, Any]] = {}
audit_log: list[dict[str, Any]] = []


class LoginRequest(BaseModel):
    username: str
    password: str


class CapabilityEmailRequest(BaseModel):
    email: str


def load_practice_leads() -> dict[str, dict[str, Any]]:
    with PRACTICE_LEADS_FILE.open("r", encoding="utf-8") as file_handle:
        practice_leads = json.load(file_handle)

    return {lead["username"]: lead for lead in practice_leads}


practice_leads = load_practice_leads()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def verify_password(password: str, salt_hex: str, password_hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    expected_hash = bytes.fromhex(password_hash_hex)
    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return secrets.compare_digest(candidate_hash, expected_hash)


def normalize_email(email: str) -> str:
    normalized_email = email.strip().lower()
    if not normalized_email or "@" not in normalized_email:
        raise HTTPException(status_code=400, detail="Provide a valid consultant email address")
    if not normalized_email.endswith("@slalom.com"):
        raise HTTPException(status_code=400, detail="Use a @slalom.com email address")
    return normalized_email


def get_capability(capability_name: str) -> dict[str, Any]:
    capability = capabilities.get(capability_name)
    if capability is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    return capability


def get_current_user(request: Request) -> dict[str, Any] | None:
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        return None
    return sessions.get(session_token)


def can_manage_capability(user: dict[str, Any] | None, capability_name: str) -> bool:
    if not user or user.get("role") != "practice_lead":
        return False

    permitted_practice_areas = user.get("practice_areas", [])
    capability_practice_area = capabilities[capability_name]["practice_area"]
    return "*" in permitted_practice_areas or capability_practice_area in permitted_practice_areas


def require_practice_lead(request: Request, capability_name: str | None = None) -> dict[str, Any]:
    current_user = get_current_user(request)
    if current_user is None:
        raise HTTPException(status_code=401, detail="Practice lead login required")
    if current_user.get("role") != "practice_lead":
        raise HTTPException(status_code=403, detail="Practice lead access required")
    if capability_name and not can_manage_capability(current_user, capability_name):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage this practice area",
        )
    return current_user


def append_audit_entry(
    action: str,
    actor: str,
    capability_name: str | None = None,
    consultant_email: str | None = None,
) -> None:
    audit_log.insert(
        0,
        {
            "timestamp": utc_now(),
            "action": action,
            "actor": actor,
            "capability_name": capability_name,
            "consultant_email": consultant_email,
        },
    )


def build_capabilities_response(current_user: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    response_payload = {}
    for capability_name, capability_details in capabilities.items():
        response_payload[capability_name] = {
            **capability_details,
            "consultants": list(capability_details["consultants"]),
            "pending_requests": list(pending_requests[capability_name]),
            "can_manage": can_manage_capability(current_user, capability_name),
        }
    return response_payload


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/auth/session")
def auth_session(request: Request):
    current_user = get_current_user(request)
    if current_user is None:
        return {
            "authenticated": False,
            "role": "consultant",
            "display_name": "Consultant self-service",
            "practice_areas": [],
        }

    return {
        "authenticated": True,
        "role": current_user["role"],
        "username": current_user["username"],
        "display_name": current_user["display_name"],
        "practice_areas": current_user.get("practice_areas", []),
    }


@app.post("/auth/login")
def login(credentials: LoginRequest):
    practice_lead = practice_leads.get(credentials.username.strip())
    if practice_lead is None or not verify_password(
        credentials.password,
        practice_lead["salt"],
        practice_lead["password_hash"],
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = {
        "username": practice_lead["username"],
        "display_name": practice_lead["display_name"],
        "role": practice_lead["role"],
        "practice_areas": practice_lead["practice_areas"],
    }

    append_audit_entry("login", practice_lead["username"])

    response = JSONResponse(
        {
            "message": f"Signed in as {practice_lead['display_name']}",
            "user": sessions[session_token],
        }
    )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE_SECONDS,
    )
    return response


@app.post("/auth/logout")
def logout(request: Request):
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    current_user = get_current_user(request)
    if session_token:
        sessions.pop(session_token, None)

    if current_user is not None:
        append_audit_entry("logout", current_user["username"])

    response = JSONResponse({"message": "Signed out"})
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@app.get("/capabilities")
def get_capabilities(request: Request):
    return build_capabilities_response(get_current_user(request))


@app.get("/audit-log")
def get_audit_log(request: Request):
    current_user = require_practice_lead(request)
    permitted_practice_areas = current_user.get("practice_areas", [])

    def is_visible(entry: dict[str, Any]) -> bool:
        capability_name = entry.get("capability_name")
        if capability_name is None:
            return True
        capability_practice_area = capabilities[capability_name]["practice_area"]
        return "*" in permitted_practice_areas or capability_practice_area in permitted_practice_areas

    return [entry for entry in audit_log if is_visible(entry)][:25]


@app.post("/capabilities/{capability_name}/request-access")
def request_capability_access(capability_name: str, registration: CapabilityEmailRequest):
    capability = get_capability(capability_name)
    email = normalize_email(registration.email)

    if email in capability["consultants"]:
        raise HTTPException(status_code=400, detail="Consultant is already registered for this capability")
    if email in pending_requests[capability_name]:
        raise HTTPException(status_code=400, detail="A request for this consultant is already pending")

    pending_requests[capability_name].append(email)
    append_audit_entry("request_submitted", email, capability_name, email)
    return {"message": f"Submitted a registration request for {email} in {capability_name}"}


@app.post("/capabilities/{capability_name}/register")
def register_for_capability(capability_name: str, registration: CapabilityEmailRequest, request: Request):
    current_user = require_practice_lead(request, capability_name)
    capability = get_capability(capability_name)
    email = normalize_email(registration.email)

    if email in capability["consultants"]:
        raise HTTPException(status_code=400, detail="Consultant is already registered for this capability")

    capability["consultants"].append(email)
    if email in pending_requests[capability_name]:
        pending_requests[capability_name].remove(email)

    append_audit_entry("registered", current_user["username"], capability_name, email)
    return {"message": f"Registered {email} for {capability_name}"}


@app.post("/capabilities/{capability_name}/approve-request")
def approve_capability_request(capability_name: str, registration: CapabilityEmailRequest, request: Request):
    current_user = require_practice_lead(request, capability_name)
    capability = get_capability(capability_name)
    email = normalize_email(registration.email)

    if email not in pending_requests[capability_name]:
        raise HTTPException(status_code=404, detail="Pending request not found")
    if email in capability["consultants"]:
        pending_requests[capability_name].remove(email)
        raise HTTPException(status_code=400, detail="Consultant is already registered for this capability")

    pending_requests[capability_name].remove(email)
    capability["consultants"].append(email)
    append_audit_entry("request_approved", current_user["username"], capability_name, email)
    return {"message": f"Approved {email} for {capability_name}"}


@app.delete("/capabilities/{capability_name}/unregister")
def unregister_from_capability(capability_name: str, email: str, request: Request):
    current_user = require_practice_lead(request, capability_name)
    capability = get_capability(capability_name)
    normalized_email = normalize_email(email)

    if normalized_email not in capability["consultants"]:
        raise HTTPException(status_code=400, detail="Consultant is not registered for this capability")

    capability["consultants"].remove(normalized_email)
    append_audit_entry("unregistered", current_user["username"], capability_name, normalized_email)
    return {"message": f"Unregistered {normalized_email} from {capability_name}"}
