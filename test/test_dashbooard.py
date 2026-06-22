from fastapi.testclient import TestClient

def test_latest_crypto_http_route(client):
    response = client.get("/crypto/latest")
    assert response.status_code == 200

    data = response.json()
    assert "bitcoin" in data or "error" in data or "note" in data
    if "bitcoin" in data:
        assert "usd" in data["bitcoin"]

def test_websocket_connection_and_stream(client):
    with client.websocket_connect("/ws/crypto") as websocket:
        data = websocket.receive_json()

        assert "timestamp" in data
        assert "active_clients" in data
        assert "prices" in data
        assert data["active_clients"] == 1

def test_websocket_multi_connection(client):
    with client.websocket_connect("/ws/crypto") as ws1:
        with client.websocket_connect("/ws/crypto") as ws2:
            data1 = ws1.receive_json()
            data2 = ws2.receive_json()

            assert data1["active_clients"] == 2
            assert data2["active_clients"] == 2

            assert data1["timestamp"] == data2["timestamp"]
            assert data1["prices"]["bitcoin"]["usd"] == data2["prices"]["bitcoin"]["usd"]