import firebase_admin
from firebase_admin import credentials, auth
import os
import base64
import json
import logging
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

# Configurar un logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_firebase():
    if firebase_admin._apps:
        return

    try:
        firebase_creds_base64 = os.getenv("FIREBASE_CREDENTIALS_BASE64")

        if firebase_creds_base64:
            firebase_creds_json = base64.b64decode(firebase_creds_base64).decode('utf-8')
            firebase_creds = json.loads(firebase_creds_json)
            cred = credentials.Certificate(firebase_creds)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with environment variable credentials")
        else:
            # Fallback to local file (for local development)
            cred = credentials.Certificate("secrests/secrests.json")
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with JSON file")

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise HTTPException(status_code=500, detail=f"Firebase configuration error: {str(e)}")

def create_firebase_user(email, password):
    return auth.create_user(email=email, password=password)

def get_firebase_user_by_email(email):
    return auth.get_user_by_email(email)