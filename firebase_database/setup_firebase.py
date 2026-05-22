import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from pathlib import Path

# Get the absolute path to the service account key file
current_dir = Path(__file__).parent
service_account_path = current_dir / "firebase_service_account.json"

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(str(service_account_path))
    firebase_admin.initialize_app(cred)

# Export the db and auth instances
db = firestore.client()
auth_client = auth
admin = firebase_admin
