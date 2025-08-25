from google.oauth2 import service_account
from google.cloud import storage
from google.cloud.firestore_v1.base_query import FieldFilter
from flask import current_app
import os
import uuid



def upload_file_to_storage(file, filename, folder):
    credentials = service_account.Credentials.from_service_account_file(
        os.path.join(os.path.dirname(__file__), "../../firebase_token.json")
    )

    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket('llm-tutor-cc826.firebasestorage.app') 

    unique_name = f"{folder}/{uuid.uuid4()}_{filename}"
    blob = bucket.blob(unique_name)

    # Upload file
    blob.upload_from_file(file, content_type=file.content_type)

    # Make the blob public forever
    blob.make_public()
    print(blob)

    # Return public URL (will never expire)
    return blob.public_url, unique_name
