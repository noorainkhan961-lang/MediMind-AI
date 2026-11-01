from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sqlite3
import uuid

from backend.symptom_analyzer import analyze_symptoms
from backend.chatbot import chat_with_ollama, get_available_model

app = Flask(__name__, template_folder="frontend")
CORS(app)

# Local-only prototype storage. Do not expose this development server publicly.
DATABASE = os.path.join(app.root_path, "medimind.db")
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                full_name TEXT NOT NULL,
                date_of_birth TEXT,
                gender TEXT,
                blood_group TEXT,
                height TEXT,
                weight TEXT,
                emergency_contact TEXT,
                conditions TEXT,
                allergies TEXT,
                surgeries TEXT,
                family_history TEXT,
                current_medicines TEXT,
                hospitalisations TEXT
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS health_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_type TEXT NOT NULL,
                test_name TEXT,
                result TEXT,
                unit TEXT,
                reference_range TEXT,
                record_date TEXT,
                notes TEXT,
                stored_filename TEXT,
                original_filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({
        "status": "success",
        "message": "MediMind AI is running!"
    })


@app.route("/models")
def models():
    try:
        model = get_available_model()
        return jsonify({"available": True, "model": model})
    except RuntimeError as error:
        return jsonify({"available": False, "error": str(error)}), 503


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    symptoms = data.get("symptoms", [])
    description = data.get("description", "")

    if not isinstance(symptoms, list):
        return jsonify({"error": "Invalid symptoms."}), 400
    if not all(isinstance(item, str) for item in symptoms):
        return jsonify({"error": "Invalid symptom values."}), 400
    if not isinstance(description, str) or len(description) > 2000:
        return jsonify({"error": "Invalid or overly long description."}), 400

    return jsonify(analyze_symptoms(symptoms, description))


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    history = data.get("history", [])

    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Please enter a message."}), 400
    if len(message) > 1200:
        return jsonify({"error": "Please keep your message under 1,200 characters."}), 400
    if not isinstance(history, list):
        return jsonify({"error": "Invalid chat history."}), 400

    try:
        answer, model = chat_with_ollama(message.strip(), history)
        return jsonify({"reply": answer, "model": model})
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "GET":
        with get_db() as db:
            row = db.execute("SELECT * FROM profile WHERE id = 1").fetchone()
        return jsonify(dict(row) if row else {})
    data = request.get_json(silent=True) or {}
    full_name = str(data.get("full_name", "")).strip()[:80]
    if not full_name:
        return jsonify({"error": "Full name is required."}), 400
    fields = [
        "date_of_birth", "gender", "blood_group", "height", "weight",
        "emergency_contact", "conditions", "allergies", "surgeries",
        "family_history", "current_medicines", "hospitalisations"
    ]
    values = [str(data.get(field, "")).strip()[:1000] for field in fields]
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO profile "
            "(id, full_name, " + ", ".join(fields) + ") "
            "VALUES (1, ?, " + ", ".join(["?"] * len(fields)) + ")",
            [full_name] + values
        )
    return jsonify({"saved": True, "message": "Health profile saved on this computer."})


@app.route("/records", methods=["GET", "POST"])
def records():
    if request.method == "GET":
        with get_db() as db:
            rows = db.execute(
                "SELECT id, record_type, test_name, result, unit, reference_range, "
                "record_date, notes, original_filename, created_at "
                "FROM health_records ORDER BY id DESC"
            ).fetchall()
        return jsonify([dict(row) for row in rows])

    record_type = request.form.get("record_type", "manual").strip()
    record_date = request.form.get("record_date", "").strip()[:20]
    notes = request.form.get("notes", "").strip()[:1000]
    if record_type == "upload":
        file = request.files.get("report")
        if not file or not file.filename:
            return jsonify({"error": "Choose a report file."}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF, JPG, JPEG and PNG files are allowed."}), 400
        content = file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            return jsonify({"error": "File is larger than 5 MB."}), 413
        safe_original = secure_filename(file.filename)[:150]
        stored = uuid.uuid4().hex + "." + safe_original.rsplit(".", 1)[1].lower()
        with open(os.path.join(UPLOAD_FOLDER, stored), "wb") as output:
            output.write(content)
        with get_db() as db:
            cursor = db.execute(
                "INSERT INTO health_records "
                "(record_type, record_date, notes, stored_filename, original_filename) "
                "VALUES ('upload', ?, ?, ?, ?)",
                (record_date, notes, stored, safe_original)
            )
            record_id = cursor.lastrowid
        return jsonify({"saved": True, "id": record_id})

    test_name = request.form.get("test_name", "").strip()[:120]
    result = request.form.get("result", "").strip()[:120]
    unit = request.form.get("unit", "").strip()[:40]
    reference_range = request.form.get("reference_range", "").strip()[:120]
    if not test_name or not result:
        return jsonify({"error": "Test name and result are required."}), 400
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO health_records "
            "(record_type, test_name, result, unit, reference_range, record_date, notes) "
            "VALUES ('manual', ?, ?, ?, ?, ?, ?)",
            (test_name, result, unit, reference_range, record_date, notes)
        )
        record_id = cursor.lastrowid
    return jsonify({"saved": True, "id": record_id})


@app.route("/dashboard-summary", methods=["GET"])
def dashboard_summary():
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) FROM health_records").fetchone()[0]
        uploaded = db.execute(
            "SELECT COUNT(*) FROM health_records WHERE record_type = 'upload'"
        ).fetchone()[0]
        manual = db.execute(
            "SELECT COUNT(*) FROM health_records WHERE record_type = 'manual'"
        ).fetchone()[0]
        recent = db.execute(
            "SELECT id, record_type, test_name, original_filename, record_date, created_at "
            "FROM health_records ORDER BY COALESCE(record_date, created_at) DESC, id DESC LIMIT 5"
        ).fetchall()
    return jsonify({
        "total_records": total,
        "uploaded_reports": uploaded,
        "manual_results": manual,
        "recent_records": [dict(row) for row in recent]
    })


@app.route("/records/<int:record_id>", methods=["DELETE"])
def delete_record(record_id):
    with get_db() as db:
        row = db.execute(
            "SELECT stored_filename FROM health_records WHERE id = ?", (record_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "Record not found."}), 404
        db.execute("DELETE FROM health_records WHERE id = ?", (record_id,))
    if row["stored_filename"]:
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, row["stored_filename"]))
        except FileNotFoundError:
            pass
    return jsonify({"deleted": True})


@app.route("/records/file/<int:record_id>")
def view_record_file(record_id):
    with get_db() as db:
        row = db.execute(
            "SELECT stored_filename FROM health_records WHERE id = ?", (record_id,)
        ).fetchone()
    if not row or not row["stored_filename"]:
        return jsonify({"error": "Uploaded file not found."}), 404
    return send_from_directory(UPLOAD_FOLDER, row["stored_filename"], as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000,debug=False)
