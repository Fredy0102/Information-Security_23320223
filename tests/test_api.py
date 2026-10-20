import html

import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "test.db"),
            "JWT_SECRET": "test-secret-only-for-ci-at-least-32-bytes-long",
        }
    )
    return app.test_client()


def token_for(client):
    response = client.post(
        "/auth/login", json={"login": "student", "password": "ChangeMe123!"}
    )
    assert response.status_code == 200
    return response.json["access_token"]


def test_login_and_protected_data(client):
    assert client.get("/api/data").status_code == 401
    token = token_for(client)
    response = client.get("/api/data", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json["data"][0]["title"] == "Welcome"


def test_bad_login_and_sqli_input_rejected(client):
    assert client.post("/auth/login", json={"login": "student", "password": "wrong"}).status_code == 401
    response = client.post(
        "/auth/login", json={"login": "' OR 1=1 --", "password": "x"}
    )
    assert response.status_code == 401


def test_post_creation_escapes_returned_markup(client):
    token = token_for(client)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": '<script>alert("x")</script>', "body": "safe?"}
    assert client.post("/api/posts", json=payload, headers=headers).status_code == 201
    response = client.get("/api/data", headers=headers)
    assert response.status_code == 200
    assert response.json["data"][-1]["title"] == html.escape(payload["title"], quote=True)


def test_tampered_token_rejected(client):
    token = token_for(client)
    response = client.get("/api/data", headers={"Authorization": f"Bearer {token}x"})
    assert response.status_code == 401
