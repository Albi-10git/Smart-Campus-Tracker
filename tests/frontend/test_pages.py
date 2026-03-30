def test_login_page_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "<title>Campus Tracker Login</title>" in html
    assert 'id="login-panel"' in html


def test_dashboard_loads(client):
    response = client.get("/dashboard")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Movement Dashboard" in html
    assert 'id="logs"' in html


def test_form_elements_exist(client):
    response = client.get("/register_student_page")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="name"' in html
    assert 'id="register"' in html
    assert 'id="rfid"' in html
