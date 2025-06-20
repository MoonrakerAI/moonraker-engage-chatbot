"""
HIPAA-compliant security utilities for mental health chatbot.
Implements encryption, hashing, and audit logging required for healthcare data.
"""

import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings


class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass


class AuditLogEntry(BaseModel):
    """Model for HIPAA audit log entries."""
    timestamp: datetime
    user_id: Optional[str]
    patient_id: Optional[str]
    action: str
    resource: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    outcome: str  # success, failure, warning
    details: Optional[Dict[str, Any]] = None


class HIPAAEncryption:
    """HIPAA-compliant encryption utilities."""
    
    def __init__(self, encryption_key: str):
        """Initialize encryption with provided key."""
        self.fernet = Fernet(self._derive_key(encryption_key))
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        salt = b'mental_health_chatbot_salt_v1'  # Use consistent salt for key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data and return base64 encoded string."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted_data = self.fernet.encrypt(data)
        return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded string and return original data."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            raise SecurityError(f"Decryption failed: {str(e)}")
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt dictionary data."""
        import json
        json_data = json.dumps(data, default=str)
        return self.encrypt(json_data)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt to dictionary data."""
        import json
        decrypted_json = self.decrypt(encrypted_data)
        return json.loads(decrypted_json)


class PatientDataEncryption(HIPAAEncryption):
    """Specialized encryption for patient data with additional safeguards."""
    
    def __init__(self):
        """Initialize with patient data encryption key."""
        super().__init__(settings.patient_data_encryption_key)
    
    def anonymize_patient_id(self, patient_id: str) -> str:
        """Create anonymized patient identifier."""
        # Create deterministic but irreversible hash
        salt = "patient_anonymization_salt_v1"
        combined = f"{patient_id}{salt}"
        hash_obj = hashlib.sha256(combined.encode())
        return f"anon_{hash_obj.hexdigest()[:16]}"
    
    def encrypt_pii(self, pii_data: Dict[str, Any]) -> str:
        """Encrypt personally identifiable information."""
        # Add metadata for compliance tracking
        encrypted_pii = {
            "data": pii_data,
            "encrypted_at": datetime.utcnow().isoformat(),
            "encryption_version": "v1",
            "compliance_flags": ["hipaa", "phi"]
        }
        return self.encrypt_dict(encrypted_pii)


class HIPAAPasswordContext:
    """HIPAA-compliant password hashing and verification."""
    
    def __init__(self):
        """Initialize password context with strong settings."""
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12,  # Strong rounds for healthcare data
        )
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.pwd_context.hash(password)
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate cryptographically secure password."""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class JWTManager:
    """JWT token management for secure authentication."""
    
    def __init__(self):
        """Initialize JWT manager."""
        self.secret_key = settings.secret_key
        self.algorithm = settings.encryption_algorithm
        self.access_token_expire = timedelta(minutes=settings.access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=settings.refresh_token_expire_days)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + self.access_token_expire
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + self.refresh_token_expire
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise SecurityError(f"Token verification failed: {str(e)}")


class HIPAAAuditLogger:
    """HIPAA-compliant audit logging for all patient data access."""
    
    def __init__(self):
        """Initialize audit logger."""
        self.encryption = HIPAAEncryption(settings.database_encryption_key)
    
    async def log_access(
        self,
        user_id: Optional[str],
        patient_id: Optional[str],
        action: str,
        resource: str,
        outcome: str = "success",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log patient data access for HIPAA compliance."""
        audit_entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            patient_id=patient_id,
            action=action,
            resource=resource,
            ip_address=ip_address,
            user_agent=user_agent,
            outcome=outcome,
            details=details
        )
        
        # TODO: Store in database with encryption
        # This would typically go to a separate audit database
        print(f"AUDIT LOG: {audit_entry.model_dump()}")


# Global instances
patient_encryption = PatientDataEncryption()
password_context = HIPAAPasswordContext()
jwt_manager = JWTManager()
audit_logger = HIPAAAuditLogger()