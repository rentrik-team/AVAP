from app.core.enums import TargetType


def test_create_target_success(client):
    response = client.post("/api/v1/targets", json={"target": "10.10.10.10"})
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["target"] == "10.10.10.10"
    assert data["data"]["target_type"] == TargetType.IPV4
    assert "id" in data["data"]


def test_create_target_validation_failure(client):
    response = client.post("/api/v1/targets", json={"target": "invalid-target!!!!"})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_create_duplicate_target(client):
    client.post("/api/v1/targets", json={"target": "duplicate.com"})
    response = client.post("/api/v1/targets", json={"target": "duplicate.com"})
    
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "CONFLICT"


def test_get_targets(client):
    client.post("/api/v1/targets", json={"target": "list1.com"})
    client.post("/api/v1/targets", json={"target": "list2.com"})
    
    response = client.get("/api/v1/targets")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] >= 2
    assert len(data["data"]["targets"]) >= 2


def test_get_single_target(client):
    create_resp = client.post("/api/v1/targets", json={"target": "single.com"})
    target_id = create_resp.json()["data"]["id"]
    
    response = client.get(f"/api/v1/targets/{target_id}")
    assert response.status_code == 200
    assert response.json()["data"]["target"] == "single.com"


def test_get_target_not_found(client):
    import uuid
    response = client.get(f"/api/v1/targets/{uuid.uuid4()}")
    assert response.status_code == 404


def test_update_target(client):
    create_resp = client.post("/api/v1/targets", json={"target": "old.com"})
    target_id = create_resp.json()["data"]["id"]
    
    response = client.put(f"/api/v1/targets/{target_id}", json={"target": "new.com"})
    assert response.status_code == 200
    assert response.json()["data"]["target"] == "new.com"


def test_delete_target(client):
    create_resp = client.post("/api/v1/targets", json={"target": "delete.com"})
    target_id = create_resp.json()["data"]["id"]
    
    response = client.delete(f"/api/v1/targets/{target_id}")
    assert response.status_code == 204
    
    # Verify it's gone
    get_resp = client.get(f"/api/v1/targets/{target_id}")
    assert get_resp.status_code == 404
