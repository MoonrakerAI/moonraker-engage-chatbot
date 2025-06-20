"""
Main FastAPI application for HIPAA-compliant mental health chatbot.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import uvicorn

from .api.therapist_interface import router as therapist_router
from .api.patient_chatbot import router as patient_router
from .core.config import settings
from .core.security import audit_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    
    # Startup
    logger.info("Starting HIPAA-compliant mental health chatbot")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"HIPAA compliance mode: {settings.hipaa_compliant_mode}")
    
    # Log application startup
    await audit_logger.log_access(
        user_id="system",
        patient_id=None,
        action="application_startup",
        resource="application",
        outcome="success",
        details={
            "environment": settings.environment,
            "hipaa_mode": settings.hipaa_compliant_mode,
            "version": "1.0.0"
        }
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down mental health chatbot")
    await audit_logger.log_access(
        user_id="system",
        patient_id=None,
        action="application_shutdown",
        resource="application",
        outcome="success"
    )


# Create FastAPI application
app = FastAPI(
    title="Mental Health AI Chatbot",
    description="HIPAA-compliant AI chatbot for mental health therapists built on GoHighLevel foundation",
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan
)

# Security middleware
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
    )

# CORS middleware (restrictive for production)
allowed_origins = ["http://localhost:3000"] if settings.is_development else ["https://yourdomain.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with audit logging."""
    
    # Log the exception
    await audit_logger.log_access(
        user_id=getattr(request.state, "user_id", None),
        patient_id=None,
        action="http_exception",
        resource=str(request.url),
        outcome="failure",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        details={
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with audit logging."""
    
    # Log the exception
    await audit_logger.log_access(
        user_id=getattr(request.state, "user_id", None),
        patient_id=None,
        action="general_exception",
        resource=str(request.url),
        outcome="failure",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        details={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }
    )
    
    logger.error(f"Unhandled exception: {exc}")
    
    # Return generic error in production
    error_detail = str(exc) if settings.is_development else "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": error_detail,
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.environment
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with system status."""
    
    # Check various system components
    checks = {
        "api": "healthy",
        "database": "unknown",  # Would check actual database
        "ghl_mcp": "unknown",   # Would check MCP server
        "ai_models": "unknown", # Would check AI model availability
        "encryption": "healthy" if settings.hipaa_compliant_mode else "disabled",
        "audit_logging": "active"
    }
    
    # Determine overall status
    overall_status = "healthy" if all(check != "error" for check in checks.values()) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.environment,
        "checks": checks,
        "compliance": {
            "hipaa_mode": settings.hipaa_compliant_mode,
            "audit_retention_days": settings.audit_log_retention_days,
            "data_encryption": "enabled" if settings.hipaa_compliant_mode else "disabled"
        }
    }


@app.get("/")
async def root():
    """Root endpoint with application information."""
    return {
        "application": "Mental Health AI Chatbot",
        "description": "HIPAA-compliant AI chatbot for mental health therapists",
        "version": "1.0.0",
        "documentation": "/docs" if settings.is_development else "Contact administrator",
        "features": {
            "therapist_interface": "Therapy-focused practice management",
            "patient_chatbot": "AI-powered mental health support",
            "crisis_detection": "Real-time risk assessment",
            "ghl_integration": "Seamless backend with GoHighLevel",
            "hipaa_compliance": "Full encryption and audit logging"
        },
        "endpoints": {
            "therapist_dashboard": "/therapist/dashboard",
            "patient_chat": "/chat/message",
            "emergency_resources": "/chat/emergency-resources",
            "health_check": "/health"
        },
        "security": {
            "authentication": "JWT-based",
            "encryption": "AES-256",
            "audit_logging": "Full HIPAA compliance",
            "crisis_protocols": "Automated therapist notification"
        }
    }


# Include routers
app.include_router(therapist_router)
app.include_router(patient_router)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for audit compliance."""
    
    start_time = datetime.utcnow()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    # Log the request (for audit compliance)
    await audit_logger.log_access(
        user_id=getattr(request.state, "user_id", None),
        patient_id=getattr(request.state, "patient_id", None),
        action="http_request",
        resource=str(request.url.path),
        outcome="success" if response.status_code < 400 else "failure",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        details={
            "method": request.method,
            "status_code": response.status_code,
            "process_time": process_time,
            "content_length": response.headers.get("content-length")
        }
    )
    
    return response


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
        access_log=True
    )