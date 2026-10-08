import ctypes
import ctypes.wintypes
import threading
import time
import win32api
import win32con
import win32gui

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32

class Win32LaserDot:
    """Lightweight 24x24 borderless, click-through, circular red laser dot overlay."""
    def __init__(self):
        self.hwnd = None
        self._visible = False
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=2.0)

    def _run(self):
        hdesk = user32.OpenDesktopW("default", 0, False, 0x10000000)
        if hdesk:
            user32.SetThreadDesktop(hdesk)

        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = win32gui.DefWindowProc
        wc.lpszClassName = "PPTUniversalLaserDot"
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = gdi32.CreateSolidBrush(0x0000FF)  # Pure Red in BGR (0x0000FF)
        try:
            win32gui.RegisterClass(wc)
        except Exception:
            pass

        ex_style = (
            win32con.WS_EX_TOPMOST
            | win32con.WS_EX_LAYERED
            | win32con.WS_EX_TRANSPARENT
            | win32con.WS_EX_TOOLWINDOW
            | win32con.WS_EX_NOACTIVATE
        )
        style = win32con.WS_POPUP

        self.hwnd = user32.CreateWindowExW(
            ex_style, "PPTUniversalLaserDot", "LaserDot", style,
            -100, -100, 24, 24, 0, 0, 0, 0
        )
        if self.hwnd:
            hrgn = gdi32.CreateEllipticRgn(0, 0, 24, 24)
            user32.SetWindowRgn(self.hwnd, hrgn, True)
            user32.SetLayeredWindowAttributes(self.hwnd, 0, 245, win32con.LWA_ALPHA)
        self._ready.set()

        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def show(self, x: int, y: int):
        self._visible = True
        if self.hwnd:
            user32.SetWindowPos(
                self.hwnd, win32con.HWND_TOPMOST,
                int(x) - 12, int(y) - 12, 24, 24,
                win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW
            )

    def hide(self):
        self._visible = False
        if self.hwnd:
            user32.ShowWindow(self.hwnd, win32con.SW_HIDE)

    @property
    def is_visible(self) -> bool:
        return self._visible

class InputHandler:
    def __init__(self):
        self._ensure_interactive_desktop()
        self.screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        self.screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        self.cursor_x = self.screen_width // 2
        self.cursor_y = self.screen_height // 2
        self.laser_active = False
        self._last_slide_time = 0.0
        self._debounce_threshold = 0.2
        self.laser_dot = Win32LaserDot()

    def _ensure_interactive_desktop(self):
        """Attaches current thread to interactive user desktop ('default')."""
        try:
            hdesk = user32.OpenDesktopW("default", 0, False, 0x10000000)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
        except Exception:
            pass

    def find_target_presentation_hwnd(self) -> tuple[int, str]:
        """Finds active presentation window and identifies platform ('powerpoint', 'canva', 'googleslides', 'generic')."""
        self._ensure_interactive_desktop()

        # 1. Active PowerPoint Fullscreen Slide Show
        h_slideshow = user32.FindWindowW("screenClass", None)
        if h_slideshow and user32.IsWindowVisible(h_slideshow):
            return h_slideshow, "powerpoint"

        # 2. PowerPoint Presenter View
        candidate_hwnd = 0
        def enum_cb(hwnd, _):
            nonlocal candidate_hwnd
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            if "Presenter View" in title:
                candidate_hwnd = hwnd
                return False
            return True

        user32.EnumWindows(
            ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong, ctypes.c_long)(enum_cb),
            0
        )
        if candidate_hwnd:
            return candidate_hwnd, "powerpoint"

        # 3. PowerPoint Main Application window (exact class PPTFrameClass)
        h_ppt = user32.FindWindowW("PPTFrameClass", None)
        if h_ppt and user32.IsWindowVisible(h_ppt):
            return h_ppt, "powerpoint"

        # 4. Canva or Google Slides presentation (browser windows)
        browser_hwnd = 0
        platform_type = "generic"
        def browser_cb(hwnd, _):
            nonlocal browser_hwnd, platform_type
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.lower()
            if "canva" in title:
                browser_hwnd = hwnd
                platform_type = "canva"
                return False
            if any(term in title for term in ["google slides", "slide google", "google slide", "slides.google", "presentasi"]):
                browser_hwnd = hwnd
                platform_type = "googleslides"
                return False
            return True

        user32.EnumWindows(
            ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong, ctypes.c_long)(browser_cb),
            0
        )
        if browser_hwnd:
            return browser_hwnd, platform_type

        return 0, "generic"

    def focus_target_window(self) -> tuple[int, str]:
        """Brings the target presentation window to the foreground."""
        self._ensure_interactive_desktop()
        target_hwnd, platform = self.find_target_presentation_hwnd()
        if target_hwnd:
            fore_hwnd = user32.GetForegroundWindow()
            if fore_hwnd != target_hwnd:
                try:
                    fore_thread = user32.GetWindowThreadProcessId(fore_hwnd, None)
                    my_thread = kernel32.GetCurrentThreadId()
                    user32.AttachThreadInput(my_thread, fore_thread, True)
                    user32.SetForegroundWindow(target_hwnd)
                    user32.BringWindowToTop(target_hwnd)
                    user32.AttachThreadInput(my_thread, fore_thread, False)
                    time.sleep(0.02)
                except Exception:
                    pass
        return target_hwnd, platform

    def _send_key_with_focus(self, vk_code: int):
        """Sends clean single keystroke with foreground focus."""
        self.focus_target_window()
        scan_code = user32.MapVirtualKeyW(vk_code, 0)
        user32.keybd_event(vk_code, scan_code, 0, 0)
        time.sleep(0.01)
        user32.keybd_event(vk_code, scan_code, win32con.KEYEVENTF_KEYUP, 0)

    def _is_slide_debounced(self) -> bool:
        """Suppresses duplicate triggers within debounce window."""
        now = time.time()
        if now - self._last_slide_time < self._debounce_threshold:
            return True
        self._last_slide_time = now
        return False

    def next_slide(self) -> bool:
        """Advances slide (PageDown / VK_NEXT) with debounce protection."""
        if self._is_slide_debounced():
            return False
        self._send_key_with_focus(win32con.VK_NEXT)
        return True

    def prev_slide(self) -> bool:
        """Reverses slide (PageUp / VK_PRIOR) with debounce protection."""
        if self._is_slide_debounced():
            return False
        self._send_key_with_focus(win32con.VK_PRIOR)
        return True

    def start_presentation(self, from_beginning=True):
        """Starts presentation (F5 or Shift+F5)."""
        if not from_beginning:
            user32.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
            self._send_key_with_focus(win32con.VK_F5)
            user32.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
        else:
            self._send_key_with_focus(win32con.VK_F5)

    def exit_presentation(self):
        """Exits presentation (Escape)."""
        self._send_key_with_focus(win32con.VK_ESCAPE)

    def blackout(self):
        """Toggles black screen ('B' key)."""
        self._send_key_with_focus(ord('B'))

    def whiteout(self):
        """Toggles white screen ('W' key)."""
        self._send_key_with_focus(ord('W'))

    def canva_effect(self, effect_char: str):
        """Triggers Canva magic effects: 'c', 'd', 'o', 'q'."""
        if effect_char and len(effect_char) == 1:
            self._send_key_with_focus(ord(effect_char.upper()))

    def set_laser_state(self, visible: bool):
        """Activates universal laser pointer across PowerPoint, Canva, and Google Slides."""
        self.laser_active = visible
        if visible:
            self.laser_dot.show(self.cursor_x, self.cursor_y)
        else:
            self.laser_dot.hide()

        target_hwnd, platform = self.focus_target_window()

        if platform == "googleslides":
            # Google Slides toggles native laser pointer using 'L'
            user32.keybd_event(ord('L'), 0, 0, 0)
            time.sleep(0.01)
            user32.keybd_event(ord('L'), 0, win32con.KEYEVENTF_KEYUP, 0)
        elif platform == "powerpoint":
            # PowerPoint native laser pointer (Ctrl+L) or revert to arrow (Ctrl+A)
            # Synchronized when slide show (screenClass) is actively running
            h_slideshow = user32.FindWindowW("screenClass", None)
            if h_slideshow:
                if visible:
                    user32.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                    user32.keybd_event(ord('L'), 0, 0, 0)
                    time.sleep(0.01)
                    user32.keybd_event(ord('L'), 0, win32con.KEYEVENTF_KEYUP, 0)
                    user32.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                else:
                    user32.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                    user32.keybd_event(ord('A'), 0, 0, 0)
                    time.sleep(0.01)
                    user32.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
                    user32.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

    def move_cursor_relative(self, dx: float, dy: float, sensitivity: float = 1.8):
        """Moves cursor coordinates on screen smoothly, relative to real OS position and generates mouse movement event."""
        self._ensure_interactive_desktop()
        try:
            pt = win32api.GetCursorPos()
            cur_x, cur_y = pt[0], pt[1]
        except Exception:
            cur_x, cur_y = self.cursor_x, self.cursor_y

        # Handle screen bounds: check if PowerPoint slideshow window is active
        h_slideshow = user32.FindWindowW("screenClass", None)
        if h_slideshow and user32.IsWindowVisible(h_slideshow):
            rect = win32gui.GetWindowRect(h_slideshow)
            min_x, min_y, max_x, max_y = rect[0], rect[1], rect[2], rect[3]
        else:
            min_x, min_y = 0, 0
            max_x, max_y = self.screen_width, self.screen_height

        self.cursor_x = max(min_x, min(max_x, cur_x + int(dx * sensitivity)))
        self.cursor_y = max(min_y, min(max_y, cur_y + int(dy * sensitivity)))

        user32.SetCursorPos(self.cursor_x, self.cursor_y)
        delta_x = self.cursor_x - cur_x
        delta_y = self.cursor_y - cur_y
        user32.mouse_event(win32con.MOUSEEVENTF_MOVE, delta_x, delta_y, 0, 0)

        # Update universal laser dot position
        if self.laser_active:
            self.laser_dot.show(self.cursor_x, self.cursor_y)

        return self.cursor_x, self.cursor_y

    def set_cursor_normalized(self, norm_x: float, norm_y: float):
        """Sets cursor position using normalized coordinates (0.0 to 1.0)."""
        self._ensure_interactive_desktop()
        h_slideshow = user32.FindWindowW("screenClass", None)
        if h_slideshow and user32.IsWindowVisible(h_slideshow):
            rect = win32gui.GetWindowRect(h_slideshow)
            min_x, min_y, max_x, max_y = rect[0], rect[1], rect[2], rect[3]
            w = max_x - min_x
            h = max_y - min_y
            self.cursor_x = int(min_x + max(0.0, min(1.0, norm_x)) * w)
            self.cursor_y = int(min_y + max(0.0, min(1.0, norm_y)) * h)
        else:
            self.cursor_x = int(max(0.0, min(1.0, norm_x)) * self.screen_width)
            self.cursor_y = int(max(0.0, min(1.0, norm_y)) * self.screen_height)
        user32.SetCursorPos(self.cursor_x, self.cursor_y)
        user32.mouse_event(win32con.MOUSEEVENTF_MOVE, 1, 1, 0, 0)

        # Update universal laser dot position
        if self.laser_active:
            self.laser_dot.show(self.cursor_x, self.cursor_y)

        return self.cursor_x, self.cursor_y

    def click(self, button='left'):
        """Simulates mouse click."""
        self._ensure_interactive_desktop()
        if button == 'right':
            down = win32con.MOUSEEVENTF_RIGHTDOWN
            up = win32con.MOUSEEVENTF_RIGHTUP
        else:
            down = win32con.MOUSEEVENTF_LEFTDOWN
            up = win32con.MOUSEEVENTF_LEFTUP

        user32.mouse_event(down, 0, 0, 0, 0)
        time.sleep(0.01)
        user32.mouse_event(up, 0, 0, 0, 0)
