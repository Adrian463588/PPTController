import sys
sys.stdout.reconfigure(line_buffering=True)
import time
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk
import uvicorn
from PIL import Image, ImageTk
import qrcode

from server.ws_server import PresentationServer
from server.network_utils import get_local_ip, print_terminal_qr

class PPTControllerApp:
    def __init__(self, port=8765):
        self.port = port
        self.server = PresentationServer(port=self.port)
        self.server_thread = None
        self.uvicorn_server = None
        self.root = None
        self.qr_photo = None
        self.current_ip = get_local_ip()

    def start_server_thread(self):
        """Starts the FastAPI + WebSocket server in a background thread."""
        config = uvicorn.Config(
            app=self.server.app,
            host="0.0.0.0",
            port=self.port,
            log_level="warning"
        )
        self.uvicorn_server = uvicorn.Server(config)
        self.server_thread = threading.Thread(target=self.uvicorn_server.run, daemon=True)
        self.server_thread.start()

    def launch_gui(self):
        """Launches the desktop GUI with QR code and pairing info."""
        self.root = tk.Tk()
        self.root.title("PPT & Canva Remote Controller")
        self.root.geometry("420x540")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f172a")

        style = ttk.Style()
        style.theme_use("clam")

        # Title Section
        header_frame = tk.Frame(self.root, bg="#1e293b", pady=12)
        header_frame.pack(fill="x")

        lbl_title = tk.Label(
            header_frame,
            text="📱 Presentation Remote Host",
            font=("Segoe UI", 14, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        )
        lbl_title.pack()

        lbl_subtitle = tk.Label(
            header_frame,
            text="Kontrol PowerPoint & Canva lewat HP",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#1e293b"
        )
        lbl_subtitle.pack()

        # QR Code Container
        qr_frame = tk.Frame(self.root, bg="#0f172a", pady=15)
        qr_frame.pack()

        self.qr_label = tk.Label(qr_frame, bg="#ffffff", relief="solid", bd=2)
        self.qr_label.pack()

        # URL Info Label
        url_frame = tk.Frame(self.root, bg="#0f172a")
        url_frame.pack(pady=5)

        self.lbl_url = tk.Label(
            url_frame,
            text="",
            font=("Segoe UI", 11, "bold"),
            fg="#38bdf8",
            bg="#0f172a",
            cursor="hand2"
        )
        self.lbl_url.pack()
        self.lbl_url.bind("<Button-1>", lambda e: webbrowser.open(f"http://{self.current_ip}:{self.port}"))

        self.lbl_status = tk.Label(
            url_frame,
            text="Menunggu koneksi dari HP...",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#0f172a"
        )
        self.lbl_status.pack(pady=4)

        # Action Buttons Frame
        btn_frame = tk.Frame(self.root, bg="#0f172a", pady=10)
        btn_frame.pack(fill="x", padx=30)

        btn_test_next = tk.Button(
            btn_frame,
            text="⏩ Tes Next Slide",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="white",
            relief="flat",
            pady=6,
            command=self.server.input_handler.next_slide
        )
        btn_test_next.pack(fill="x", pady=4)

        btn_test_laser = tk.Button(
            btn_frame,
            text="🎯 Tes Laser Pointer PowerPoint (1 Detik)",
            font=("Segoe UI", 9),
            bg="#334155",
            fg="#f8fafc",
            relief="flat",
            pady=5,
            command=self._test_laser
        )
        btn_test_laser.pack(fill="x", pady=4)

        btn_open_browser = tk.Button(
            btn_frame,
            text="🌐 Buka Controller di Browser Laptop",
            font=("Segoe UI", 9),
            bg="#1e293b",
            fg="#38bdf8",
            relief="flat",
            pady=5,
            command=lambda: webbrowser.open(f"http://{self.current_ip}:{self.port}")
        )
        btn_open_browser.pack(fill="x", pady=4)

        self._update_qr()
        self.root.after(1000, self._refresh_status)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def _test_laser(self):
        """Temporarily triggers the native PowerPoint laser pointer."""
        self.server.input_handler.set_laser_state(True)
        threading.Timer(1.5, lambda: self.server.input_handler.set_laser_state(False)).start()

    def _update_qr(self):
        url = f"http://{self.current_ip}:{self.port}"
        self.lbl_url.config(text=url)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        self.qr_photo = ImageTk.PhotoImage(img, master=self.root)
        self.qr_label.config(image=self.qr_photo)

    def _refresh_status(self):
        count = len(self.server.connected_clients)
        if count > 0:
            self.lbl_status.config(
                text=f"🟢 {count} Perangkat HP Terhubung",
                fg="#10b981"
            )
        else:
            self.lbl_status.config(
                text="📱 Arahkan kamera HP ke QR Code di atas",
                fg="#94a3b8"
            )
        if self.root:
            self.root.after(1000, self._refresh_status)

    def on_close(self):
        print("[App] Shutting down server...")
        if self.uvicorn_server:
            self.uvicorn_server.should_exit = True
        if self.root:
            self.root.destroy()
        sys.exit(0)

    def run(self, cli_mode=False):
        print("\n=============================================")
        print("  POWERPOINT & CANVA REMOTE CONTROLLER HOST")
        print("=============================================\n")

        url = f"http://{self.current_ip}:{self.port}"
        print_terminal_qr(url)
        print(f"[*] Server aktif di: {url}")
        print("[*] Buka URL tersebut di browser HP atau scan QR Code di atas.")
        print("[*] Tekan Ctrl+C untuk menghentikan server.\n")

        self.start_server_thread()

        if cli_mode:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.on_close()
        else:
            try:
                self.launch_gui()
            except KeyboardInterrupt:
                self.on_close()

if __name__ == "__main__":
    cli = "--cli" in sys.argv or "--headless" in sys.argv
    app = PPTControllerApp(port=8765)
    app.run(cli_mode=cli)
