import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# Define absolute path to JSON
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "firebase_token.json")



# Initialize Firebase app once
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

    # Create db instance and expose it
    db = firestore.client()
