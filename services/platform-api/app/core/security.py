"""JWT handling and demo user factory (local mode)."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.context import UserContext
import httpx
import structlog

logger = structlog.get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    subject: str,
    role: str,
    tenant_id: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode = {
        "sub": subject,
        "role": role,
        "tenant_id": tenant_id,
        "iat": int(time.time()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


class CognitoJWKSVerifier:
    def __init__(self):
        self.jwks = None
        self.jwks_url = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        self.last_fetch = 0

    def get_jwks(self) -> Dict[str, Any]:
        # Cache for 1 hour to avoid frequent network calls
        if not self.jwks or time.time() - self.last_fetch > 3600:
            if not settings.COGNITO_USER_POOL_ID:
                raise ValueError("COGNITO_USER_POOL_ID is not configured")
            response = httpx.get(self.jwks_url, timeout=5.0)
            response.raise_for_status()
            self.jwks = response.json()
            self.last_fetch = time.time()
        return self.jwks

    def verify(self, token: str) -> Dict[str, Any]:
        try:
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            for key in self.get_jwks().get("keys", []):
                if key["kid"] == unverified_header.get("kid"):
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"],
                    }
                    break

            if not rsa_key:
                raise ValueError("Unable to find appropriate key")

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=settings.COGNITO_APP_CLIENT_ID,
                issuer=f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
            )
            return payload
        except Exception as e:
            logger.warning("cognito_jwt_verification_failed", error=str(e))
            raise ValueError(f"Invalid Cognito token: {e}") from e

cognito_verifier = CognitoJWKSVerifier()

def decode_jwt(token: str) -> Dict[str, Any]:
    if settings.USE_REAL_AWS:
        return cognito_verifier.verify(token)
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e


# Demo users for local development and demos
DEMO_USERS: Dict[str, Dict[str, Any]] = {
    "patient@hospital-a.demo": {
        "user_id": "pat_001",
        "role": "patient",
        "tenant_id": "tenant_hospital_a",
        "name": "Maria Gonzalez",
        "assigned_patients": ["pat_001"],
    },
    "clinician@hospital-a.demo": {
        "user_id": "doc_001",
        "role": "clinician",
        "tenant_id": "tenant_hospital_a",
        "name": "Dr. Sarah Chen",
        "assigned_patients": ["pat_001", "pat_002"],
        "can_access_all": True,
    },
    "nurse@hospital-a.demo": {
        "user_id": "nurse_001",
        "role": "nurse",
        "tenant_id": "tenant_hospital_a",
        "name": "James Rivera, RN",
        "assigned_patients": ["pat_001", "pat_002"],
        "can_access_all": False,
    },
    "care_coordinator@hospital-a.demo": {
        "user_id": "cc_001",
        "role": "care_coordinator",
        "tenant_id": "tenant_hospital_a",
        "name": "Aisha Patel",
        "assigned_patients": ["pat_001", "pat_002"],
        "can_access_all": True,
    },
    "admin@hospital-a.demo": {
        "user_id": "admin_001",
        "role": "admin",
        "tenant_id": "tenant_hospital_a",
        "name": "Robert Kim",
        "assigned_patients": [],
        "can_access_all": False,  # Admins do NOT get automatic clinical PHI access
    },
    "compliance@hospital-a.demo": {
        "user_id": "comp_001",
        "role": "compliance_officer",
        "tenant_id": "tenant_hospital_a",
        "name": "Elena Vasquez",
        "assigned_patients": [],
        "can_access_all": False,
    },
}


def create_demo_user_context(email_or_id: str) -> UserContext:
    """Create a realistic UserContext for demos and local testing."""
    key = email_or_id if "@" in email_or_id else f"{email_or_id}@hospital-a.demo"
    data = DEMO_USERS.get(key, DEMO_USERS["patient@hospital-a.demo"])

    return UserContext(
        user_id=data["user_id"],
        role=data["role"],
        tenant_id=data["tenant_id"],
        email=key,
        full_name=data["name"],
        assigned_patient_ids=set(data.get("assigned_patients", [])),
        can_access_all_patients_in_tenant=data.get("can_access_all", False),
        consent_scopes=["treatment", "care_coordination"],
    )


def create_demo_token(email_or_id: str) -> str:
    user = create_demo_user_context(email_or_id)
    return create_access_token(
        subject=user.user_id,
        role=user.role,
        tenant_id=user.tenant_id,
        extra_claims={
            "email": user.email,
            "name": user.full_name,
            "assigned_patients": list(user.assigned_patient_ids),
        },
    )
