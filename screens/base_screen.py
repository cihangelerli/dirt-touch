# screens/base_screen.py
import pygame


class BaseScreen:
    def __init__(self, app_state_manager):
        self.app = app_state_manager

    def enter(self):
        pass

    def exit(self):
        pass

    def update(self, dt: float):
        pass

    def draw(self, surface: pygame.Surface):
        pass

    def handle_event(self, event: pygame.event.Event):
        pass

    def on_resume(self):
        pass
