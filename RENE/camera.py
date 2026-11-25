import pygame


class Camera:
    """Smoothly interpolated 2D top-down camera with world clamping."""

    def __init__(self, screen_w, screen_h, world_w, world_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.world_w = world_w
        self.world_h = world_h
        self.x = float(world_w // 2 - screen_w // 2)
        self.y = float(world_h // 2 - screen_h // 2)
        self.target_x = self.x
        self.target_y = self.y

    def center_on(self, wx, wy, immediate=False):
        self.target_x = max(0.0, min(float(self.world_w - self.screen_w), wx - self.screen_w / 2.0))
        self.target_y = max(0.0, min(float(self.world_h - self.screen_h), wy - self.screen_h / 2.0))
        if immediate:
            self.x = self.target_x
            self.y = self.target_y

    def move_target(self, dx, dy):
        self.target_x = max(0.0, min(float(self.world_w - self.screen_w), self.target_x + dx))
        self.target_y = max(0.0, min(float(self.world_h - self.screen_h), self.target_y + dy))

    def update(self, dt):
        lerp = min(1.0, dt * 8.5)
        self.x += (self.target_x - self.x) * lerp
        self.y += (self.target_y - self.y) * lerp

    def get_world_viewport(self):
        return pygame.Rect(int(self.x), int(self.y), self.screen_w, self.screen_h)

    def world_to_screen(self, wx, wy):
        return int(wx - self.x), int(wy - self.y)
