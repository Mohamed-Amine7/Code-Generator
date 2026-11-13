USER = {"username": "alice", "email": "alice@example.com", "password": "secret123"}


def test_root_and_status(client):
    assert client.get("/").status_code == 200
    status_data = client.get("/status").json()
    assert "models" in status_data
    assert "cache" in status_data

    health_data = client.get("/health").json()
    assert "status" in health_data
    assert "database" in health_data
    assert "cache" in health_data


def test_register_rejects_weak_password_and_bad_email(client):
    assert client.post("/register", json={**USER, "password": "short"}).status_code == 422
    assert client.post("/register", json={**USER, "password": "onlyletters"}).status_code == 422
    assert client.post("/register", json={**USER, "email": "nope"}).status_code == 422


def test_register_login_me_logout(client):
    assert client.post("/register", json=USER).status_code == 201
    assert client.post("/register", json=USER).status_code == 400  # doublon

    bad = client.post("/login", data={"username": "alice", "password": "wrong-pass1"})
    assert bad.status_code == 401

    ok = client.post("/login", data={"username": "alice", "password": USER["password"]})
    assert ok.status_code == 200
    assert "httponly" in ok.headers["set-cookie"].lower()

    me = client.get("/users/me")  # le cookie est conservé par le client
    assert me.status_code == 200 and me.json()["username"] == "alice"

    client.post("/logout")
    client.cookies.clear()
    assert client.get("/users/me").status_code == 401


def test_protected_routes_require_auth(client):
    client.cookies.clear()
    for method, url in [("get", "/history"), ("post", "/generate"), ("post", "/analyze"),
                        ("post", "/api/feedback/validate"), ("post", "/api/correction/")]:
        assert getattr(client, method)(url).status_code == 401, url


def test_validate_and_history_when_logged_in(client):
    client.post("/login", data={"username": "alice", "password": USER["password"]})
    r = client.post("/api/feedback/validate", json={"code": "def f(:\n  pass", "language": "python"})
    assert r.status_code == 200 and r.json()["valid"] is False
    assert client.get("/history").json() == []
    bad = client.post("/generate", json={"text": "reverse a string", "language": "cpp"})
    assert bad.status_code == 422  # langage non supporté
