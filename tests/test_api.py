import uuid


def _register(client):
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "email": f"user{suffix}@example.com",
        "username": f"user{suffix}",
        "password": "secret123",
    }
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    return data["access_token"], data["user"], payload


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "providers_configured" in body


def test_register_and_login(client):
    token, user, payload = _register(client)
    assert user["email"] == payload["email"]

    # duplicate fails
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 400

    # login works
    r = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_me_requires_auth(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401

    token, _, _ = _register(client)
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_conversations_empty(client):
    token, _, _ = _register(client)
    r = client.get("/api/conversations", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []


def test_metrics_empty(client):
    token, _, _ = _register(client)
    r = client.get("/api/metrics", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["total_conversations"] == 0
    assert body["total_messages"] == 0
