import ctypes
import time
import win32api
import win32con

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class InputHandler:
    def __init__(self):
        self._ensure_interactive_desktop()
        self.screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        self.screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        self.cursor_x = self.screen_width // 2
        self.cursor_y = self.screen_height // 2
        self.laser_active = False

    def _ensure_interactive_desktop(self):
        """Attaches current thread to interactive user desktop ('default')."""
        try:
            hdesk = user32.OpenDesktopW("default", 0, False, 0x10000000)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
        except Exception:
            pass

    def find_target_presentation_hwnd(self) -> int:
        """Finds PowerPoint SlideShow (screenClass), Presenter View, or Main Window (PPTFrameClass)."""
        self._ensure_interactive_desktop()

        # 1. Active PowerPoint Fullscreen Slide Show
        h_slideshow = user32.FindWindowW("screenClass", None)
        if h_slideshow and user32.IsWindowVisible(h_slideshow):
            return h_slideshow

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
            return candidate_hwnd

        # 3. PowerPoint Main Application window (exact class PPTFrameClass)
        h_ppt = user32.FindWindowW("PPTFrameClass", None)
        if h_ppt and user32.IsWindowVisible(h_ppt):
            return h_ppt

        # 4. Canva presentation (browser window with Canva)
        canva_hwnd = 0
        def canva_cb(hwnd, _):
            nonlocal canva_hwnd
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            if "Canva" in title:
                canva_hwnd = hwnd
                return False
            return True

        user32.EnumWindows(
            ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong, ctypes.c_long)(canva_cb),
            0
        )
        return canva_hwnd

    def focus_target_window(self) -> int:
        """Brings the target presentation window to the foreground."""
        self._ensure_interactive_desktop()
        target_hwnd = self.find_target_presentation_hwnd()
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
        return target_hwnd

    def _send_key_with_focus(self, vk_code: int):
        """Sends keystroke with focus and dual injection (PageDown, PageUp, etc.)."""
        target_hwnd = self.focus_target_window()

        if target_hwnd:
            # Post directly to window
            user32.PostMessageW(target_hwnd, win32con.WM_KEYDOWN, vk_code, 0)
            user32.PostMessageW(target_hwnd, win32con.WM_KEYUP, vk_code, 0)

        # Global keybd_event injection
        user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.01)
        user32.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)

    def next_slide(self):
        """Advances slide (PageDown / VK_NEXT)."""
        self._send_key_with_focus(win32con.VK_NEXT)

    def prev_slide(self):
        """Reverses slide (PageUp / VK_PRIOR)."""
        self._send_key_with_focus(win32con.VK_PRIOR)

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
        """Activates PowerPoint native laser pointer (Ctrl+L) or reverts to arrow (Ctrl+A)."""
        if visible and not self.laser_active:
            self.laser_active = True
            self.focus_target_window()
            # Send Ctrl + L (PowerPoint native Laser Pointer)
            user32.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            user32.keybd_event(ord('L'), 0, 0, 0)
            time.sleep(0.01)
            user32.keybd_event(ord('L'), 0, win32con.KEYEVENTF_KEYUP, 0)
            user32.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

        elif not visible and self.laser_active:
            self.laser_active = False
            self.focus_target_window()
            # Send Ctrl + A (Revert to standard arrow cursor)
            user32.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            user32.keybd_event(ord('A'), 0, 0, 0)
            time.sleep(0.01)
            user32.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
            user32.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

    def move_cursor_relative(self, dx: float, dy: float, sensitivity: float = 1.8):
        """Moves cursor coordinates on screen smoothly."""
        self._ensure_interactive_desktop()
        self.cursor_x = max(0, min(self.screen_width, self.cursor_x + int(dx * sensitivity)))
        self.cursor_y = max(0, min(self.screen_height, self.cursor_y + int(dy * sensitivity)))
        user32.SetCursorPos(self.cursor_x, self.cursor_y)
        return self.cursor_x, self.cursor_y

    def set_cursor_normalized(self, norm_x: float, norm_y: float):
        """Sets cursor position using normalized coordinates (0.0 to 1.0)."""
        self._ensure_interactive_desktop()
        self.cursor_x = int(max(0.0, min(1.0, norm_x)) * self.screen_width)
        self.cursor_y = int(max(0.0, min(1.0, norm_y)) * self.screen_height)
        user32.SetCursorPos(self.cursor_x, self.cursor_y)
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
