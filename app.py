import os
from datetime import datetime

from bson import ObjectId
from flask import Flask, render_template, request, redirect, jsonify
from pymongo.errors import DuplicateKeyError
from pymongo import MongoClient
import mongomock

from arduino_connection import create_arduino_bridge

app = Flask(__name__)

def create_mongo_client():
    if os.getenv("USE_MOCK_DB", "false").lower() in {"1", "true", "yes", "on"}:
        return mongomock.MongoClient()

    return MongoClient(
        os.getenv("MONGO_URI", "mongodb://localhost:27017/"),
        serverSelectionTimeoutMS=int(os.getenv("MONGO_TIMEOUT_MS", "5000"))
    )


client = create_mongo_client()
db = client["campus_tracker"]

users = db["users"]
students = db["students"]
visitors = db["visitors"]
movement_logs = db["movement_logs"]

students.create_index(
    "rfid_tag",
    unique=True,
    sparse=True
)


def normalize_rfid_tag(tag):
    return "".join((tag or "").split()).upper()


arduino_bridge = create_arduino_bridge(
    app_base_url=os.getenv("APP_BASE_URL", "http://127.0.0.1:5000"),
    serial_port=os.getenv("ARDUINO_SERIAL_PORT", "COM10"),
    baud_rate=int(os.getenv("ARDUINO_BAUD_RATE", "9600")),
    default_location=os.getenv("RFID_DEFAULT_LOCATION", "Main Gate"),
    enabled=os.getenv("ARDUINO_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
)


def get_open_log(tag, location):
    return movement_logs.find_one(
        {
            "rfid_tag": tag,
            "location": location,
            "$or": [
                {"time_out": {"$exists": False}},
                {"time_out": ""},
                {"status": "Time In"}
            ]
        },
        {"_id": 1, "status": 1},
        sort=[("timestamp", -1)]
    )


@app.route("/")
def login():
    return render_template("login.html", active_form="login", message=None, message_type=None)


@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html", active_form="login", message=None, message_type=None)


@app.route("/login", methods=["POST"])
def login_user():

    username = request.form.get("username")
    password = request.form.get("password")

    user = users.find_one({"username": username})

    if user and user["password"] == password:
        return redirect("/dashboard")

    return render_template(
        "login.html",
        active_form="login",
        message="Invalid username or password.",
        message_type="error"
    )


@app.route("/register_user", methods=["POST"])
def register_user():

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    if not username or not password or not confirm_password:
        return render_template(
            "login.html",
            active_form="register",
            message="Please fill in all registration fields.",
            message_type="error"
        )

    if password != confirm_password:
        return render_template(
            "login.html",
            active_form="register",
            message="Passwords do not match.",
            message_type="error"
        )

    if users.find_one({"username": username}):
        return render_template(
            "login.html",
            active_form="register",
            message="That username already exists.",
            message_type="error"
        )

    users.insert_one({"username": username, "password": password})

    return render_template(
        "login.html",
        active_form="login",
        message="Account created successfully. You can sign in now.",
        message_type="success"
    )


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")



@app.route("/logout")
def logout():
    return redirect("/")
# ---------------- STUDENTS ----------------

@app.route("/register_student_page")
def register_student_page():
    return render_template("register_student.html")


@app.route("/register_student", methods=["POST"])
def register_student():

    data = request.json or {}
    name = (data.get("name") or "").strip()
    register_number = (data.get("register_number") or "").strip()
    rfid_tag = normalize_rfid_tag(data.get("rfid_tag"))

    if not name or not register_number:
        return jsonify({"message": "Student name and register number are required."}), 400

    if rfid_tag and students.find_one({"rfid_tag": rfid_tag}):
        return jsonify({"message": "This RFID is already assigned to another student."}), 400

    student = {
        "name": name,
        "register_number": register_number
    }

    if rfid_tag:
        student["rfid_tag"] = rfid_tag

    try:
        students.insert_one(student)
    except DuplicateKeyError:
        return jsonify({"message": "This RFID is already assigned to another student."}), 400

    return jsonify({"message": "Student Registered"})


@app.route("/students")
def list_students():

    student_list = []
    sort_mode = (request.args.get("sort") or "name").strip().lower()
    sort_order = [("name", 1)]

    if sort_mode == "rfid":
        sort_order = [("rfid_tag", 1), ("name", 1)]

    for student in students.find({}, {"name": 1, "register_number": 1, "rfid_tag": 1}).sort(sort_order):
        student_list.append(
            {
                "id": str(student["_id"]),
                "name": student.get("name", ""),
                "register_number": student.get("register_number", ""),
                "rfid_tag": student.get("rfid_tag", "")
            }
        )

    return jsonify(student_list)


@app.route("/delete_student/<student_id>", methods=["POST"])
def delete_student(student_id):

    try:
        object_id = ObjectId(student_id)
    except Exception:
        return jsonify({"message": "Invalid student selected."}), 400

    deleted_student = students.find_one_and_delete({"_id": object_id})

    if not deleted_student:
        return jsonify({"message": "Student not found."}), 404

    return jsonify(
        {
            "message": f'{deleted_student.get("name", "Student")} was removed. The RFID can now be assigned again.'
        }
    )


# ---------------- VISITORS ----------------

@app.route("/register_visitor_page")
def register_visitor_page():
    return render_template("register_visitor.html")


@app.route("/register_visitor", methods=["POST"])
def register_visitor():

    data = request.json or {}
    rfid_tag = normalize_rfid_tag(data.get("rfid_tag"))

    if not rfid_tag:
        return jsonify({"message": "Visitor RFID tag is required."}), 400

    visitor = {
        "name": data["name"],
        "phone": data["phone"],
        "purpose": data["purpose"],
        "rfid_tag": rfid_tag
    }

    visitors.insert_one(visitor)

    return jsonify({"message": "Visitor Registered"})


# ---------------- RFID SIMULATION ----------------

@app.route("/rfid_scan", methods=["POST"])
def rfid_scan():

    data = request.json or {}
    tag = normalize_rfid_tag(data.get("rfid_tag"))
    location = (data.get("location") or arduino_bridge.default_location).strip()

    if not tag:
        return jsonify({"message": "RFID tag is required."}), 400

    if not location:
        return jsonify({"message": "Location is required."}), 400

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    open_log = get_open_log(tag, location)

    student = students.find_one({"rfid_tag": tag})
    visitor = visitors.find_one({"rfid_tag": tag})

    if student:
        if open_log:
            movement_logs.update_one(
                {"_id": open_log["_id"]},
                {"$set": {"time_out": current_time, "status": "Time Out", "timestamp": current_time}}
            )

            return jsonify({"message": "Student Detected - Time Out"})

        log = {
            "type": "student",
            "name": student["name"],
            "register_number": student["register_number"],
            "rfid_tag": tag,
            "location": location,
            "status": "Time In",
            "time_in": current_time,
            "time_out": "",
            "timestamp": current_time
        }

        movement_logs.insert_one(log)

        return jsonify({"message": "Student Detected - Time In"})


    if visitor:
        if open_log:
            movement_logs.update_one(
                {"_id": open_log["_id"]},
                {"$set": {"time_out": current_time, "status": "Time Out", "timestamp": current_time}}
            )

            return jsonify({"message": "Visitor Detected - Time Out"})

        log = {
            "type": "visitor",
            "name": visitor["name"],
            "rfid_tag": tag,
            "location": location,
            "status": "Time In",
            "time_in": current_time,
            "time_out": "",
            "timestamp": current_time
        }

        movement_logs.insert_one(log)

        return jsonify({"message": "Visitor Detected - Time In"})


    return jsonify({"message": "RFID not found"})


@app.route("/arduino_status")
def arduino_status():
    return jsonify(arduino_bridge.get_status())


@app.route("/logs")
def logs():

    logs = []

    for log in movement_logs.find({}, {"_id":0}).sort("timestamp", -1):
        logs.append(log)

    return jsonify(logs)


@app.route("/clear_logs", methods=["POST"])
def clear_logs():
    return jsonify({"message": "Dashboard log view can be cleared without deleting saved movement records."})


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() in {"1", "true", "yes", "on"}
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))

    if not debug_mode or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        arduino_bridge.start()

    app.run(host=host, port=port, debug=debug_mode)
