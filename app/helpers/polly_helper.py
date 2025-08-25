import uuid
import boto3
from google.cloud import storage
from google.oauth2 import service_account
import os

polly_client = boto3.client("polly", region_name="us-east-1")

def synthesize_speech(text, emotion):
    credentials = service_account.Credentials.from_service_account_file(
        os.path.join(os.path.dirname(__file__), "../../firebase_token.json")
    )

    # ✅ Initialize GCS client and bucket
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket("llm-tutor-cc826.firebasestorage.app")  # ✅ Correct bucket format (not .app)

    voice = "Joanna"
    prosody = {
        "happy": "<prosody rate='fast' pitch='+5%'>",
        "sad": "<prosody rate='slow' pitch='-3%'>",
        "angry": "<prosody volume='loud'>",
        "confused": "<prosody rate='slow' pitch='-2%'>",
        "neutral": "<prosody rate='medium'>"
    }.get(emotion, "<prosody rate='medium'>")

    ssml = f"<speak>{prosody}{text}</prosody></speak>"

    response = polly_client.synthesize_speech(
        Engine="standard",
        OutputFormat="mp3",
        TextType="ssml",
        Text=ssml,
        VoiceId=voice
    )

    file_id = uuid.uuid4().hex
    file_name = f"QA/audio_{file_id}.mp3"

    # Upload to Firebase Storage
    blob = bucket.blob(file_name)
    blob.upload_from_string(response["AudioStream"].read(), content_type="audio/mpeg")
    blob.make_public()

    return blob.public_url
