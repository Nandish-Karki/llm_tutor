import os
import json
import re
import boto3
from firebase_admin import firestore
from google.cloud import storage
from google.oauth2 import service_account
from app.helpers.polly_helper import synthesize_speech
# Initialize Firebase and Polly
db = firestore.client()
polly = boto3.client("polly",region_name="us-east-1")


# Ensure output folder exists
os.makedirs("output", exist_ok=True)

# Keywords that should be emphasized in speech
EMPHASIS_KEYWORDS = {"important", "critical", "alert", "note", "warning"}

def get_cached_modules(email, document_id):
    """
    Retrieves cached module list from Firestore.
    Path: Indexes/{email}/{document_id}/modules
    """
    print(f"Fetching cached modules for {email} in document {document_id}")
    doc_ref = db.collection("Indexes").document(email).collection(document_id).document("modules")
    doc = doc_ref.get()
    if not doc.exists:
        return None
    print(f"Found {len(doc.to_dict().get('modules', []))} modules")
    return doc.to_dict().get("modules", [])

def generate_ssml(text, chunk_id=0):
    ssml = '<speak>'
    sentences = re.split(r'(?<=[.!?]) +', text)
    word_index = 0

    for sentence in sentences:
        words = sentence.split()
        for i, word in enumerate(words):
            # only apply <mark> to actual words
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word:
                ssml += f'<mark name="w{chunk_id}_{word_index}"/>'
                word_index += 1

                if clean_word in EMPHASIS_KEYWORDS:
                    ssml += f'<emphasis level="moderate">{word}</emphasis>'
                else:
                    ssml += word
            else:
                ssml += word  # for punctuation

            if i < len(words) - 1:
                ssml += ' '

        # ✅ insert <break> only AFTER sentence, NOT after <mark>
        ssml += '<break time="600ms"/>'

    ssml += '</speak>'
    return ssml

def synthesize_audio_and_marks(ssml, module_number):
    """
    Sends SSML to Polly and saves both MP3 audio and speech mark JSON locally.
    Returns:
      - audio file path
      - cleaned speech marks (list of dicts)
    """
    audio_path = f"output/audio_module{module_number}.mp3"
    marks_path = f"output/marks_module{module_number}.json"

    # Generate audio
    audio_res = polly.synthesize_speech(
        Text=ssml,
        TextType="ssml",
        VoiceId="Joanna",
        OutputFormat="mp3"
    )

    # Generate speech marks
    marks_res = polly.synthesize_speech(
        Text=ssml,
        TextType="ssml",
        VoiceId="Joanna",
        OutputFormat="json",
        SpeechMarkTypes=["word"]
    )

    # Save audio
    with open(audio_path, "wb") as f:
        f.write(audio_res["AudioStream"].read())

    # Save speech marks as raw lines
    with open(marks_path, "wb") as f:
        f.write(marks_res["AudioStream"].read())

    # Parse speech marks JSON lines
    with open(marks_path, "r") as f:
        speech_marks = [
    mark for line in f if line.strip()
    for mark in [json.loads(line)]
    if mark["type"] == "word" and not mark["value"].startswith("<")
]

    return audio_path, speech_marks

def save_module_audio(email, document_id, module_number, ssml, audio_path, speech_marks):
    """
    Uploads audio to Firebase Storage and saves metadata to Firestore.
    Firestore path: SSML/{email}/{document_id}/modules/module{n}
    Storage path: audio/{email}/{document_id}/module{n}.mp3
    """
    print(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../firebase_token.json")))
    # ✅ Load service account credentials
    credentials = service_account.Credentials.from_service_account_file(
        os.path.join(os.path.dirname(__file__), "../../firebase_token.json")
    )
    print(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../firebase_token.json")))


    # ✅ Initialize GCS client and bucket
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket("llm-tutor-cc826.firebasestorage.app")  # ✅ Correct bucket format (not .app)

    # ✅ Upload file
    blob_path = f"audio/{email}/{document_id}/module{module_number}.mp3"
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(audio_path)

    # ✅ Make public (or generate signed URL)
    blob.make_public()
    public_url = blob.public_url

    # ✅ Store metadata in Firestore
    doc_ref = db.collection("SSML").document(email).collection(document_id).document("modules")
    doc_ref.set({
        f"module{module_number}": {
            "ssml": ssml,
            "audio_url": public_url,
            "speech_marks": speech_marks
        }
    }, merge=True)

    print(f"✅ Audio uploaded to: {public_url}")
    return public_url
    
