import tkinter as tk
import threading
import queue
import ctypes
import win32api
import win32con
import win32gui

class LaserOverlay:
    def __init__(self):
        self.cmd_queue = queue.Queue()
        self.is_running = False
        self.thread = None
        self.root = None
        self.canvas = None
        self.laser_items = []
        self.spotlight_items = []
        self.transparent_color = '#000001'
        self.color_map = {
            'red': {'core': '#ffffff', 'glow': '#ff0033', 'halo': '#ff3366'},
            'green': {'core': '#ffffff', 'glow': '#00ff66', 'halo': '#33ff99'},
            'blue': {'core': '#ffffff', 'glow': '#00ccff', 'halo': '#33ddff'}
        }
        self.current_color = 'red'
        self.pointer_mode = 'laser'

    def start(self, parent_root=None):
        """Starts the overlay window. If parent_root is provided, creates Toplevel in same thread."""
        if parent_root:
            self.root = tk.Toplevel(parent_root)
            self._setup_window()
            self._process_queue()
        else:
            if self.thread and self.thread.is_alive():
                return
            self.is_running = True
            self.thread = threading.Thread(target=self._run_standalone, daemon=True)
            self.thread.start()

    def _setup_window(self):
        try:
            user32 = ctypes.windll.user32
            hdesk = user32.OpenDesktopW("default", 0, False, 0x10000000)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
        except Exception:
            pass

        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-transparentcolor', self.transparent_color)
        self.root.config(bg=self.transparent_color)

        vx = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        vy = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
        vw = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        vh = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

        self.root.geometry(f"{vw}x{vh}+{vx}+{vy}")

        self.canvas = tk.Canvas(
            self.root,
            bg=self.transparent_color,
            highlightthickness=0,
            width=vw,
            height=vh
        )
        self.canvas.pack(fill='both', expand=True)

        self.root.update()

        hwnd = self.root.winfo_id()
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        WS_EX_NOACTIVATE = 0x08000000
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_EXSTYLE,
            style | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED | WS_EX_NOACTIVATE
        )
        self.is_running = True

    def _run_standalone(self):
        try:
            user32 = ctypes.windll.user32
            hdesk = user32.OpenDesktopW("default", 0, False, 0x10000000)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
        except Exception:
            pass
        self.root = tk.Tk()
        self._setup_window()
        self._process_queue()
        self.root.mainloop()

    def _process_queue(self):
        try:
            while not self.cmd_queue.empty():
                cmd, args = self.cmd_queue.get_nowait()
                if cmd == 'show_laser':
                    self._draw_laser(*args)
                elif cmd == 'hide_laser':
                    self._clear_laser()
                elif cmd == 'set_color':
                    self.current_color = args[0]
                elif cmd == 'set_mode':
                    self.pointer_mode = args[0]
                elif cmd == 'quit':
                    if self.root:
                        try:
                            self.root.destroy()
                        except Exception:
                            pass
                    return
        except Exception:
            pass

        if self.is_running and self.root:
            try:
                self.root.after(16, self._process_queue)
            except Exception:
                pass

    def _draw_laser(self, x: int, y: int):
        self._clear_laser()
        palette = self.color_map.get(self.current_color, self.color_map['red'])

        if self.pointer_mode == 'laser':
            r3 = 18
            h1 = self.canvas.create_oval(
                x - r3, y - r3, x + r3, y + r3,
                fill=palette['halo'], outline=''
            )
            r2 = 10
            h2 = self.canvas.create_oval(
                x - r2, y - r2, x + r2, y + r2,
                fill=palette['glow'], outline=''
            )
            r1 = 4
            h3 = self.canvas.create_oval(
                x - r1, y - r1, x + r1, y + r1,
                fill=palette['core'], outline=''
            )
            self.laser_items.extend([h1, h2, h3])

    def _clear_laser(self):
        for item in self.laser_items:
            try:
                self.canvas.delete(item)
            except Exception:
                pass
        self.laser_items.clear()

    def update_position(self, x: int, y: int, visible: bool = True):
        if visible:
            self.cmd_queue.put(('show_laser', (int(x), int(y))))
        else:
            self.cmd_queue.put(('hide_laser', ()))

    def set_color(self, color_name: str):
        if color_name in self.color_map:
            self.cmd_queue.put(('set_color', (color_name,)))

    def set_mode(self, mode: str):
        if mode in ['laser', 'spotlight']:
            self.cmd_queue.put(('set_mode', (mode,)))

    def hide(self):
        self.cmd_queue.put(('hide_laser', ()))

    def stop(self):
        self.is_running = False
        self.cmd_queue.put(('quit', ()))
