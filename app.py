from datetime import datetime

from flask import Flask, render_template, request, redirect, jsonify
from pymongo.errors import DuplicateKeyError
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["campus_tracker"]

users = db["users"]
students = db["students"]
visitors = db["visitors"]
movement_logs = db["movement_logs"]

students.create_index(
    "rfid_tag",
    unique=True,
    partialFilterExpression={"rfid_tag": {"$exists": True, "$nin": ["", None]}}
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
    rfid_tag = (data.get("rfid_tag") or "").strip()

    if not name or not register_number:
        return jsonify({"message": "Student name and register number are required."}), 400

    if rfid_tag and students.find_one({"rfid_tag": rfid_tag}):
        return jsonify({"message": "This RFID is already assigned to another student."}), 400

    student = {
        "name": name,
        "register_number": register_number,
        "rfid_tag": rfid_tag
    }

    try:
        students.insert_one(student)
    except DuplicateKeyError:
        return jsonify({"message": "This RFID is already assigned to another student."}), 400

    return jsonify({"message": "Student Registered"})


# ---------------- VISITORS ----------------

@app.route("/register_visitor_page")
def register_visitor_page():
    return render_template("register_visitor.html")


@app.route("/register_visitor", methods=["POST"])
def register_visitor():

    data = request.json

    visitor = {
        "name": data["name"],
        "phone": data["phone"],
        "purpose": data["purpose"],
        "rfid_tag": data["rfid_tag"]
    }

    visitors.insert_one(visitor)

    return jsonify({"message": "Visitor Registered"})


# ---------------- RFID SIMULATION ----------------

@app.route("/rfid_scan", methods=["POST"])
def rfid_scan():

    data = request.json
    tag = data["rfid_tag"]
    location = data["location"]
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    open_log = get_open_log(tag, location)

    student = students.find_one({"rfid_tag": tag})
    visitor = visitors.find_one({"rfid_tag": tag})

    if student:
        if open_log:
            movement_logs.update_one(
                {"_id": open_log["_id"]},
                {"$set": {"time_out": current_time, "status": "Time Out"}}
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
                {"$set": {"time_out": current_time, "status": "Time Out"}}
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


@app.route("/logs")
def logs():

    logs = []

    for log in movement_logs.find({}, {"_id":0}):
        logs.append(log)

    return jsonify(logs)


@app.route("/clear_logs", methods=["POST"])
def clear_logs():
    movement_logs.delete_many({})
    return jsonify({"message": "Recent campus movement cleared"})


if __name__ == "__main__":
    app.run(debug=True)

