import firebase_admin
from firebase_admin import credentials, firestore
import json
import base64
import os
import logging

from core.config import settings

logger = logging.getLogger(__name__)
_db = None

def initialize_firebase():
    """Initialize Firebase Admin SDK with flexible credential handling.
    
    Supports three credential formats:
    1. Raw JSON string (if starts with '{')
    2. Base64-encoded JSON (primary method for deployment)
    3. File path to JSON key file
    """
    global _db
    if _db is not None:
        return _db
    
    # Get service account from env or fallback to GOOGLE_APPLICATION_CREDENTIALS
    service_account_value = settings.firebase_service_account or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if service_account_value:
        try:
            # Check if it's a raw JSON string (starts with '{')
            if service_account_value.strip().startswith('{'):
                logger.info("Parsing Firebase credentials as raw JSON string")
                cred_dict = json.loads(service_account_value)
                cred = credentials.Certificate(cred_dict)
            else:
                # Try Base64 decoding first
                try:
                    logger.info("Attempting to decode Firebase credentials as Base64")
                    decoded_json = base64.b64decode(service_account_value).decode('utf-8')
                    cred_dict = json.loads(decoded_json)
                    cred = credentials.Certificate(cred_dict)
                    logger.info("Firebase credentials decoded from Base64 successfully")
                except Exception:
                    # If Base64 fails, treat as file path
                    logger.info("Base64 decoding failed, treating as file path")
                    if os.path.exists(service_account_value):
                        cred = credentials.Certificate(service_account_value)
                        logger.info(f"Firebase credentials loaded from file: {service_account_value}")
                    else:
                        raise FileNotFoundError(f"Service account file not found: {service_account_value}")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase with provided credentials: {e}")
            raise
    else:
        # Fall back to default credentials (for local dev with gcloud)
        logger.info("No service account provided, using default credentials")
        cred = credentials.ApplicationDefault()
    
    firebase_admin.initialize_app(cred)
    _db = firestore.client()
    logger.info("Firebase initialized successfully")
    return _db

def get_firebase_db():
    """Get Firestore database instance."""
    if _db is None:
        return initialize_firebase()
    return _db
