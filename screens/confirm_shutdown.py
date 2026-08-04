# screens/confirm_shutdown.py
import pygame
from screens.base_screen import BaseScreen
from ui.button import Button

class ConfirmShutdownScreen(BaseScreen):
    def __init__(self, app_state_manager):
        super().__init__(app_state_manager)
        
        self.btn_confirm = Button(
            rect=pygame.Rect(80, 260, 220, 100),
            text="CONFIRM SHUTDOWN",
            style="SYS",
            callback=lambda: self.app.system_shutdown()
        )
        self.btn_cancel = Button(
            rect=pygame.Rect(340, 260, 220, 100),
            text="CANCEL",
            style="APP",
            callback=lambda: self.app.switch_screen("home")
        )
        self.buttons = [self.btn_confirm, self.btn_cancel]

    def handle_event(self, event: pygame.event.Event):
        for btn in self.buttons:
            if btn.handle_event(event):
                break

    def update(self, dt: float):
        pass

    def draw(self, surface: pygame.Surface):
        for btn in self.buttons:
            btn.draw(surface)