"""
Example: Authentication and Security

This example shows how to add authentication and security to your MCP server.
"""

import os
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import wraps
import asyncio

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
API_KEYS = os.getenv("API_KEYS", "").split(",")  # Comma-separated list of valid API keys
TOKEN_EXPIRY_HOURS = 24

# Store for rate limiting
request_counts = {}

# Example: API Key validation
def validate_api_key(api_key: str) -> bool:
    """Validate an API key"""
    if not API_KEYS:
        return True  # No authentication if no keys configured
    
    # Hash comparison for security
    for valid_key in API_KEYS:
        if secrets.compare_digest(api_key, valid_key):
            return True
    return False

# Example: JWT token generation
def generate_token(user_id: str, permissions: List[str] = None) -> str:
    """Generate a JWT token"""
    payload = {
        "user_id": user_id,
        "permissions": permissions or [],
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# Example: JWT token validation
def validate_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Example: Rate limiting decorator
def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Rate limiting decorator for tools"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get client identifier (you'd need to extract this from request context)
            client_id = kwargs.get("_client_id", "unknown")
            
            now = datetime.now()
            window_start = now - timedelta(seconds=window_seconds)
            
            # Clean old entries
            if client_id in request_counts:
                request_counts[client_id] = [
                    timestamp for timestamp in request_counts[client_id]
                    if timestamp > window_start
                ]
            else:
                request_counts[client_id] = []
            
            # Check rate limit
            if len(request_counts[client_id]) >= max_requests:
                return {
                    "error": "Rate limit exceeded",
                    "retry_after": window_seconds
                }
            
            # Record request
            request_counts[client_id].append(now)
            
            # Execute function
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Example: Permission checking
def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract token from kwargs (you'd need to pass this from request)
            token = kwargs.get("_auth_token")
            if not token:
                return {"error": "Authentication required"}
            
            payload = validate_token(token)
            if not payload:
                return {"error": "Invalid or expired token"}
            
            if permission not in payload.get("permissions", []):
                return {"error": f"Permission '{permission}' required"}
            
            # Add user context to kwargs
            kwargs["_user_id"] = payload["user_id"]
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Authentication tools for the MCP server

# @mcp.tool()
async def auth_login(
    api_key: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Authenticate with API key and get JWT token
    
    Args:
        api_key: Your API key
        user_id: Optional user identifier
    """
    if not validate_api_key(api_key):
        return {"error": "Invalid API key"}
    
    # Generate token with default permissions
    token = generate_token(
        user_id or "api_user",
        permissions=["read", "write"]
    )
    
    return {
        "token": token,
        "expires_in": TOKEN_EXPIRY_HOURS * 3600,
        "token_type": "Bearer"
    }

# @mcp.tool()
async def auth_validate(
    token: str
) -> Dict[str, Any]:
    """
    Validate a JWT token
    
    Args:
        token: JWT token to validate
    """
    payload = validate_token(token)
    if not payload:
        return {"valid": False, "error": "Invalid or expired token"}
    
    return {
        "valid": True,
        "user_id": payload["user_id"],
        "permissions": payload["permissions"],
        "expires_at": datetime.fromtimestamp(payload["exp"]).isoformat()
    }

# Example: Secured tool with authentication
# @mcp.tool()
@require_permission("admin")
@rate_limit(max_requests=10, window_seconds=60)
async def admin_tool(
    action: str,
    _auth_token: Optional[str] = None,
    _user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Admin-only tool (requires authentication)
    
    Args:
        action: Admin action to perform
    """
    return {
        "success": True,
        "action": action,
        "performed_by": _user_id,
        "timestamp": datetime.now().isoformat()
    }

# Example: Input sanitization
import re
import html

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    # Remove HTML tags
    text = re.sub('<.*?>', '', text)
    
    # Escape HTML entities
    text = html.escape(text)
    
    # Limit length
    text = text[:max_length]
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32)
    
    return text

# @mcp.tool()
async def secure_text_process(
    text: str
) -> Dict[str, Any]:
    """
    Process text with sanitization
    
    Args:
        text: Text to process (will be sanitized)
    """
    # Sanitize input
    clean_text = sanitize_input(text)
    
    if clean_text != text:
        sanitized = True
    else:
        sanitized = False
    
    return {
        "processed_text": clean_text,
        "was_sanitized": sanitized,
        "length": len(clean_text)
    }

# Example: Audit logging
import json
from pathlib import Path

async def audit_log(
    action: str,
    user_id: str,
    details: Dict[str, Any]
):
    """Log security-relevant actions"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "user_id": user_id,
        "details": details
    }
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Append to audit log
    with open("logs/audit.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

# Example: Secure configuration loading
def load_secure_config() -> Dict[str, Any]:
    """Load configuration with validation"""
    config = {
        "api_keys": [],
        "allowed_origins": ["*"],
        "max_request_size": 1024 * 1024,  # 1MB
        "enable_auth": False
    }
    
    # Load from environment
    if os.getenv("ENABLE_AUTH", "false").lower() == "true":
        config["enable_auth"] = True
        
        # Require API keys if auth is enabled
        api_keys = os.getenv("API_KEYS", "")
        if not api_keys:
            raise ValueError("API_KEYS must be set when ENABLE_AUTH is true")
        
        config["api_keys"] = [key.strip() for key in api_keys.split(",")]
    
    # Parse allowed origins
    origins = os.getenv("ALLOWED_ORIGINS", "*")
    config["allowed_origins"] = [o.strip() for o in origins.split(",")]
    
    return config
