# screens/home.py
import pygame
from screens.base_screen import BaseScreen
from ui.button import Button
from ui.footer import Footer
from ui.scrollbar import Scrollbar
from utils.discovery import discover_applications
from utils.process import run_application, run_terminal_session

class HomeScreen(BaseScreen):
    def __init__(self, app_state_manager):
        super().__init__(app_state_manager)
        self.footer = Footer(pygame.Rect(0, 444, 640, 36))
        self.scrollbar = Scrollbar(pygame.Rect(600, 0, 40, 444))
        self.buttons = []
        # Dynamic discovery runs strictly ONCE at startup per specification
        self.discovered_apps = discover_applications()
        self.build_grid()

    def build_grid(self):
        self.buttons.clear()
        col_w = 300
        row_h = 88.8  # 444 / 5 grid rows
        
        # Rows 0-2: App Slots (6 slots total)
        for i in range(6):
            r = i // 2
            c = i % 2
            rect = pygame.Rect(int(c * col_w), int(r * row_h), col_w, int(row_h))
            
            if i < len(self.discovered_apps):
                app = self.discovered_apps[i]
                path = app["path"]
                title = app["title"]
                
                def make_launch_cb(app_path):
                    return lambda: self._launch_app(app_path)
                
                btn = Button(
                    rect=rect,
                    text=title,
                    style="APP",
                    callback=make_launch_cb(path)
                )
            else:
                btn = Button(
                    rect=rect,
                    text="[EMPTY]",
                    style="DISABLED",
                    callback=None
                )
            self.buttons.append(btn)

        # Row 3 Col 0: System Settings (Disabled for Phase 1)
        btn_settings = Button(
            rect=pygame.Rect(0, int(3 * row_h), col_w, int(row_h)),
            text="SYSTEM SETTINGS",
            subtitle="UNDER CONSTRUCTION",
            style="DISABLED",
            callback=None
        )
        self.buttons.append(btn_settings)

        # Row 3 Col 1: Terminal Action
        btn_terminal = Button(
            rect=pygame.Rect(col_w, int(3 * row_h), col_w, int(row_h)),
            text="TERMINAL",
            style="SYS",
            callback=self._launch_terminal
        )
        self.buttons.append(btn_terminal)

        # Row 4 Col 0: Restart Action
        btn_restart = Button(
            rect=pygame.Rect(0, int(4 * row_h), col_w, int(row_h)),
            text="RESTART",
            style="SYS",
            callback=lambda: self.app.switch_screen("confirm_restart")
        )
        self.buttons.append(btn_restart)

        # Row 4 Col 1: Shutdown Action
        btn_shutdown = Button(
            rect=pygame.Rect(col_w, int(4 * row_h), col_w, int(row_h)),
            text="SHUTDOWN",
            style="SYS",
            callback=lambda: self.app.switch_screen("confirm_shutdown")
        )
        self.buttons.append(btn_shutdown)

    def _launch_app(self, script_path: str):
        success, err_msg, exit_code = run_application(script_path)
        if not success:
            self.app.switch_screen("error", script=script_path, status=err_msg, code=exit_code)

    def _launch_terminal(self):
        run_terminal_session(self.app)

    def update(self, dt: float):
        self.footer.update(dt)

    def handle_event(self, event: pygame.event.Event):
        for btn in self.buttons:
            if btn.handle_event(event):
                break

    def draw(self, surface: pygame.Surface):
        for btn in self.buttons:
            btn.draw(surface)
        self.scrollbar.draw(surface)
        self.footer.draw(surface)