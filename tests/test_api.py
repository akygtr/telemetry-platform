def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready(client):
    assert client.get("/ready").status_code == 200


def test_create_and_list_reading(client):
    r = client.post("/readings", json={"machine_id": "cnc-01", "tag": "spindle_temp", "value": 71.5})
    assert r.status_code == 201
    assert r.json()["id"] > 0

    rows = client.get("/readings", params={"machine_id": "cnc-01"}).json()
    assert any(row["value"] == 71.5 for row in rows)


def test_rejects_bad_payload(client):
    r = client.post("/readings", json={"machine_id": "", "tag": "x", "value": "hot"})
    assert r.status_code == 422


def test_metrics_exposed(client):
    client.post("/readings", json={"machine_id": "cnc-02", "tag": "vibration", "value": 0.4})
    body = client.get("/metrics").text
    assert "readings_ingested_total" in body
    assert "http_request_duration_seconds" in body
