from flask import Flask
from flask_cors import CORS

from app.routes.auth_routes import auth_bp
from app.routes.upload_routes import upload_bp
from app.routes.roadmap_routes import roadmap_bp
from app.routes.index_routes import index_bp
from app.routes.audio_routes import audio_bp
from app.routes.qa_routes import qa_bp


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(upload_bp, url_prefix="/upload")
app.register_blueprint(roadmap_bp, url_prefix="/roadmap")
app.register_blueprint(index_bp, url_prefix="/index")
app.register_blueprint(audio_bp, url_prefix="/audio")
app.register_blueprint(qa_bp, url_prefix="/qa")


@app.route("/")
def index():
    return {"message": "LLM Tutor API (Flask) is running"}

if __name__ == "__main__":
    app.run(debug=True, port=8000)


# d10046d1-4c92-4131-8ea6-eb7cdae0ecd8