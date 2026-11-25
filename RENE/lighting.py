import math
import pygame


DISTRICT_MOODS = {
    "CENTRAL TOWN PLAZA":          {"mult": (255, 244, 224), "add": (26, 18, 8)},
    "PUBLIC MARKET (PALENGKE)":    {"mult": (255, 238, 212), "add": (32, 20, 6)},
    "RESIDENTIAL NEIGHBORHOOD":    {"mult": (252, 240, 220), "add": (22, 14, 8)},
    "RIVERSIDE COUNTRYSIDE":       {"mult": (232, 244, 255), "add": (14, 22, 28)},
    "AGRICULTURAL DISTRICT":       {"mult": (255, 252, 236), "add": (24, 22, 10)},
    "HERITAGE DISTRICT":           {"mult": (244, 228, 198), "add": (28, 18, 6)},
    "FOREST & GARDEN EDGE":        {"mult": (222, 242, 218), "add": (10, 20, 8)},
    "MUNICIPAL & PALACE DISTRICT": {"mult": (252, 246, 234), "add": (22, 18, 12)},
}


class LightingSystem:
    """
    Renders district-aware late-afternoon color grading, dappled sunbeams,
    and warm street-lamp halos while keeping pixel-art colors crisp and vibrant.
    """

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.mult_surf = pygame.Surface((screen_w, screen_h))
        self.add_surf = pygame.Surface((screen_w, screen_h))
        self.current_mult = [255.0, 244.0, 224.0]
        self.current_add = [24.0, 16.0, 8.0]
        self.lamp_glow = self._build_radial_glow(96, (55, 38, 12))
        self.sun_ray = self._build_sunbeam_surface(220, 480)

    @staticmethod
    def _build_radial_glow(radius, peak_rgb):
        surf = pygame.Surface((radius * 2, radius * 2))
        for r in range(radius, 0, -4):
            t = (1.0 - (r / radius)) ** 1.8
            col = (int(peak_rgb[0] * t), int(peak_rgb[1] * t), int(peak_rgb[2] * t))
            pygame.draw.circle(surf, col, (radius, radius), r)
        return surf

    @staticmethod
    def _build_sunbeam_surface(w, h):
        surf = pygame.Surface((w, h))
        pts = [(0, 0), (w // 2, 0), (w, h), (w // 2, h)]
        pygame.draw.polygon(surf, (18, 14, 6), pts)
        return surf

    def resize(self, w, h):
        if w != self.screen_w or h != self.screen_h:
            self.screen_w = w
            self.screen_h = h
            self.mult_surf = pygame.Surface((w, h))
            self.add_surf = pygame.Surface((w, h))

    def apply(self, target_surf, camera, district_name, light_positions, time_sec=0.0):
        w, h = target_surf.get_size()
        self.resize(w, h)

        target_mood = DISTRICT_MOODS.get(district_name, DISTRICT_MOODS["CENTRAL TOWN PLAZA"])
        for i in range(3):
            self.current_mult[i] += (target_mood["mult"][i] - self.current_mult[i]) * 0.08
            self.current_add[i] += (target_mood["add"][i] - self.current_add[i]) * 0.08

        # 1. Soft multiplicative mood tint
        self.mult_surf.fill(tuple(int(c) for c in self.current_mult))
        target_surf.blit(self.mult_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        # 2. Additive golden highlights, sunbeams, and flickering street lamps
        self.add_surf.fill(tuple(int(c) for c in self.current_add))

        # Diagonal warm late-afternoon sunbeams
        for i in range(3):
            beam_x = ((i * 420 + int(time_sec * 12)) % (w + 300)) - 150
            self.add_surf.blit(self.sun_ray, (beam_x, 0), special_flags=pygame.BLEND_RGB_ADD)

        # Flickering street lamp halos
        view = camera.get_world_viewport().inflate(180, 180)
        flicker = 0.92 + 0.08 * math.sin(time_sec * 7.5)
        rad = int(96 * flicker)
        for lx, ly in light_positions:
            if view.collidepoint(lx, ly):
                sx, sy = camera.world_to_screen(lx, ly)
                self.add_surf.blit(self.lamp_glow, (sx - rad, sy - rad), special_flags=pygame.BLEND_RGB_ADD)

        target_surf.blit(self.add_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
