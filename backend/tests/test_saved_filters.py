import uuid

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def _login(username: str, password: str) -> TestClient:
    client = TestClient(app)
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return client


def test_saved_filters_require_login():
    with TestClient(app) as client:
        assert client.get("/api/saved-filters").status_code == 401
        assert client.post("/api/saved-filters", json={"name": "x", "keyword": "x"}).status_code == 401


def test_job_08_saved_filter_crud_validation_and_three_account_isolation():
    marker = uuid.uuid4().hex
    name = f"隔离验证-{marker}"
    clients = [
        _login("jobseeker1", settings.seed_jobseeker1_password),
        _login("jobseeker2", settings.seed_jobseeker2_password),
        _login("maintainer", settings.seed_maintainer_password),
    ]
    created: list[tuple[TestClient, str]] = []
    try:
        owner = clients[0]
        invalid = owner.post("/api/saved-filters", json={"name": "空条件", "keyword": " ", "city": ""})
        assert invalid.status_code == 422

        response = owner.post(
            "/api/saved-filters", json={"name": f"  {name}  ", "keyword": "  AI  ", "city": "  北京  "}
        )
        assert response.status_code == 201
        item = response.json()
        created.append((owner, item["id"]))
        assert (item["name"], item["keyword"], item["city"]) == (name, "AI", "北京")

        duplicate = owner.post("/api/saved-filters", json={"name": name, "keyword": "Python"})
        assert duplicate.status_code == 409

        for other in clients[1:]:
            assert all(saved["id"] != item["id"] for saved in other.get("/api/saved-filters").json())
            assert other.put(
                f"/api/saved-filters/{item['id']}", json={"name": name, "keyword": "越权"}
            ).status_code == 404
            assert other.delete(f"/api/saved-filters/{item['id']}").status_code == 404

            same_name = other.post("/api/saved-filters", json={"name": name, "city": "上海"})
            assert same_name.status_code == 201
            created.append((other, same_name.json()["id"]))

        updated = owner.put(
            f"/api/saved-filters/{item['id']}",
            json={"name": f"{name}-修改", "keyword": "后端", "city": None},
        )
        assert updated.status_code == 200
        assert updated.json()["keyword"] == "后端"
        assert updated.json()["city"] is None

        assert owner.delete(f"/api/saved-filters/{item['id']}").status_code == 204
        created.pop(0)
        assert owner.delete(f"/api/saved-filters/{item['id']}").status_code == 404
    finally:
        for client, filter_id in created:
            client.delete(f"/api/saved-filters/{filter_id}")
        for client in clients:
            client.post("/api/auth/logout")
            client.close()
