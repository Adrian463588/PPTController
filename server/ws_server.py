import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from .input_handler import InputHandler
from .network_utils import get_local_ip, generate_qr_base64

class PresentationServer:
    def __init__(self, port: int = 8765):
        self.port = port
        self.app = FastAPI(title="PPT & Canva Controller")
        self.input_handler = InputHandler()
        self.connected_clients: set[WebSocket] = set()
        self.web_dir = Path(__file__).resolve().parent.parent / "web"
        self._setup_routes()

    def _setup_routes(self):
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.connected_clients.add(websocket)
            print(f"[WS] Client connected. Total active: {len(self.connected_clients)}")
            try:
                await websocket.send_json({
                    "type": "connected",
                    "status": "ok",
                    "screen": {
                        "width": self.input_handler.screen_width,
                        "height": self.input_handler.screen_height
                    }
                })

                while True:
                    text_data = await websocket.receive_text()
                    try:
                        data = json.loads(text_data)
                        await self._handle_client_message(data, websocket)
                    except json.JSONDecodeError:
                        pass
            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)
                print(f"[WS] Client disconnected. Total active: {len(self.connected_clients)}")
            except Exception as e:
                if websocket in self.connected_clients:
                    self.connected_clients.remove(websocket)
                print(f"[WS] Error: {e}")

        @self.app.get("/api/info")
        async def get_info():
            ip = get_local_ip()
            url = f"http://{ip}:{self.port}"
            return {
                "ip": ip,
                "port": self.port,
                "url": url,
                "clients_count": len(self.connected_clients),
                "screen": {
                    "width": self.input_handler.screen_width,
                    "height": self.input_handler.screen_height
                }
            }

        @self.app.get("/api/qr")
        async def get_qr():
            ip = get_local_ip()
            url = f"http://{ip}:{self.port}"
            qr_base64 = generate_qr_base64(url)
            return {"qr": f"data:image/png;base64,{qr_base64}", "url": url}

        if self.web_dir.exists():
            self.app.mount("/", StaticFiles(directory=str(self.web_dir), html=True), name="web")

    async def _handle_client_message(self, data: dict, sender: WebSocket):
        msg_type = data.get("type")

        if msg_type == "action":
            action = data.get("action")
            print(f"[WS Action] Received action: {action}", flush=True)
            if action == "next":
                self.input_handler.next_slide()
            elif action == "prev":
                self.input_handler.prev_slide()
            elif action == "start":
                self.input_handler.start_presentation(from_beginning=True)
            elif action == "resume":
                self.input_handler.start_presentation(from_beginning=False)
            elif action == "exit":
                self.input_handler.exit_presentation()
            elif action == "blackout":
                self.input_handler.blackout()
            elif action == "whiteout":
                self.input_handler.whiteout()
            elif action == "canva":
                effect = data.get("effect", "")
                self.input_handler.canva_effect(effect)
            elif action == "click":
                button = data.get("button", "left")
                self.input_handler.click(button)

        elif msg_type == "laser_move":
            dx = float(data.get("dx", 0))
            dy = float(data.get("dy", 0))
            sens = float(data.get("sensitivity", 2.0))
            self.input_handler.move_cursor_relative(dx, dy, sens)

        elif msg_type == "laser_pos":
            x_norm = float(data.get("x", 0.5))
            y_norm = float(data.get("y", 0.5))
            self.input_handler.set_cursor_normalized(x_norm, y_norm)

        elif msg_type == "laser_state":
            visible = bool(data.get("visible", False))
            print(f"[WS Laser] Laser state: {visible}", flush=True)
            self.input_handler.set_laser_state(visible)

        elif msg_type == "ping":
            await sender.send_json({"type": "pong", "time": data.get("time")})
