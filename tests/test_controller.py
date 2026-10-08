import pytest
from fastapi.testclient import TestClient
from server.ws_server import PresentationServer
from server.network_utils import get_local_ip, generate_qr_base64

@pytest.fixture
def server_instance():
    srv = PresentationServer(port=8765)
    return srv

def test_network_utils():
    ip = get_local_ip()
    assert isinstance(ip, str)
    assert len(ip.split('.')) == 4

    qr_b64 = generate_qr_base64("http://127.0.0.1:8765")
    assert isinstance(qr_b64, str)
    assert len(qr_b64) > 100

def test_api_endpoints(server_instance):
    client = TestClient(server_instance.app)
    
    # Test info API
    res_info = client.get("/api/info")
    assert res_info.status_code == 200
    info_data = res_info.json()
    assert "ip" in info_data
    assert "port" in info_data
    assert info_data["port"] == 8765
    assert "screen" in info_data

    # Test QR API
    res_qr = client.get("/api/qr")
    assert res_qr.status_code == 200
    qr_data = res_qr.json()
    assert "qr" in qr_data
    assert qr_data["qr"].startswith("data:image/png;base64,")

def test_websocket_actions(server_instance):
    client = TestClient(server_instance.app)
    with client.websocket_connect("/ws") as websocket:
        # Handshake verification
        initial_msg = websocket.receive_json()
        assert initial_msg["type"] == "connected"
        assert initial_msg["status"] == "ok"
        assert "screen" in initial_msg

        # Test slide next action
        websocket.send_json({"type": "action", "action": "next"})

        # Test slide prev action
        websocket.send_json({"type": "action", "action": "prev"})

        # Test laser move
        websocket.send_json({
            "type": "laser_move",
            "dx": 10.5,
            "dy": -5.2,
            "visible": True,
            "sensitivity": 2.0
        })

        # Test laser position normalized
        websocket.send_json({
            "type": "laser_pos",
            "x": 0.5,
            "y": 0.5,
            "visible": True
        })

        # Test laser configuration
        websocket.send_json({
            "type": "laser_config",
            "color": "green",
            "mode": "laser"
        })

        # Test ping/pong
        websocket.send_json({"type": "ping", "time": 12345})
        pong_msg = websocket.receive_json()
        assert pong_msg["type"] == "pong"
        assert pong_msg["time"] == 12345

def test_slide_debounce(server_instance):
    handler = server_instance.input_handler
    # First action succeeds
    assert handler.next_slide() is True
    # Immediate second action within cooldown is debounced
    assert handler.next_slide() is False
    # After cooldown period, action succeeds
    import time
    time.sleep(0.26)
    assert handler.next_slide() is True
