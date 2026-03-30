def test_login_route_loads(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b"Campus Portal" in response.data


def test_register_student_api(client, app_module):
    response = client.post(
        "/register_student",
        json={
            "name": "Alice Johnson",
            "register_number": "REG-001",
            "rfid_tag": "ab 12 cd"
        }
    )

    assert response.status_code == 200
    assert response.get_json() == {"message": "Student Registered"}

    saved_student = app_module.students.find_one({"register_number": "REG-001"})
    assert saved_student["name"] == "Alice Johnson"
    assert saved_student["rfid_tag"] == "AB12CD"


def test_register_visitor_api(client, app_module):
    response = client.post(
        "/register_visitor",
        json={
            "name": "John Visitor",
            "phone": "9876543210",
            "purpose": "Campus tour",
            "rfid_tag": "vf 99"
        }
    )

    assert response.status_code == 200
    assert response.get_json() == {"message": "Visitor Registered"}

    saved_visitor = app_module.visitors.find_one({"name": "John Visitor"})
    assert saved_visitor["rfid_tag"] == "VF99"


def test_rfid_scan_api_creates_student_time_in_log(client, app_module):
    app_module.students.insert_one(
        {
            "name": "Alice Johnson",
            "register_number": "REG-001",
            "rfid_tag": "AB12CD"
        }
    )

    response = client.post(
        "/rfid_scan",
        json={
            "rfid_tag": "ab 12 cd",
            "location": "Main Gate"
        }
    )

    assert response.status_code == 200
    assert response.get_json() == {"message": "Student Detected - Time In"}

    saved_log = app_module.movement_logs.find_one({"rfid_tag": "AB12CD"})
    assert saved_log["status"] == "Time In"
    assert saved_log["location"] == "Main Gate"
