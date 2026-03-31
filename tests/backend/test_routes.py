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
    assert response.get_json() == {
        "message": "Visitor Registered",
        "sms_message": "Visitor registered. SMS not sent because SMS settings are not configured."
    }

    saved_visitor = app_module.visitors.find_one({"name": "John Visitor"})
    assert saved_visitor["phone"] == "9876543210"
    assert saved_visitor["rfid_tag"] == "VF99"


def test_register_visitor_rejects_non_numeric_phone(client):
    response = client.post(
        "/register_visitor",
        json={
            "name": "John Visitor",
            "phone": "98765AB210",
            "purpose": "Campus tour",
            "rfid_tag": "vf 99"
        }
    )

    assert response.status_code == 400
    assert response.get_json() == {"message": "Phone number must contain exactly 10 digits."}


def test_register_visitor_rejects_phone_longer_than_ten_digits(client):
    response = client.post(
        "/register_visitor",
        json={
            "name": "John Visitor",
            "phone": "98765432101",
            "purpose": "Campus tour",
            "rfid_tag": "vf 99"
        }
    )

    assert response.status_code == 400
    assert response.get_json() == {"message": "Phone number must contain exactly 10 digits."}


def test_register_visitor_rejects_rfid_already_assigned_to_student(client, app_module):
    app_module.students.insert_one(
        {
            "name": "Alice Johnson",
            "register_number": "REG-001",
            "rfid_tag": "AB12CD"
        }
    )

    response = client.post(
        "/register_visitor",
        json={
            "name": "John Visitor",
            "phone": "9876543210",
            "purpose": "Campus tour",
            "rfid_tag": "ab 12 cd"
        }
    )

    assert response.status_code == 400
    assert response.get_json() == {"message": "This RFID is already assigned to another person."}


def test_list_and_delete_visitor_releases_rfid(client, app_module):
    register_response = client.post(
        "/register_visitor",
        json={
            "name": "John Visitor",
            "phone": "9876543210",
            "purpose": "Campus tour",
            "rfid_tag": "vf 99"
        }
    )

    assert register_response.status_code == 200

    visitors_response = client.get("/visitors?sort=rfid")
    visitors_payload = visitors_response.get_json()

    assert visitors_response.status_code == 200
    assert len(visitors_payload) == 1
    assert visitors_payload[0]["name"] == "John Visitor"
    assert visitors_payload[0]["phone"] == "9876543210"
    assert visitors_payload[0]["purpose"] == "Campus tour"
    assert visitors_payload[0]["rfid_tag"] == "VF99"

    delete_response = client.post(f"/delete_visitor/{visitors_payload[0]['id']}")

    assert delete_response.status_code == 200
    assert delete_response.get_json() == {
        "message": "John Visitor was removed. The RFID can now be assigned again."
    }

    reuse_response = client.post(
        "/register_visitor",
        json={
            "name": "Mary Visitor",
            "phone": "9123456789",
            "purpose": "Parent visit",
            "rfid_tag": "vf 99"
        }
    )

    assert reuse_response.status_code == 200
    assert app_module.visitors.find_one({"name": "Mary Visitor"})["rfid_tag"] == "VF99"


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
