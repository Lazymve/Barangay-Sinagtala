"""
Minimap radar overlay for Barangay Sinagtala 3D.
Displays 2D overhead layout, character position, camera position, and viewing frustum.
"""

import math
import pygame
from map_data import WORLD_MAP, MAP_ROWS, MAP_COLS


class MiniMap:
    def __init__(self, tile_size: int = 8, border: int = 16):
        self.tile_size = tile_size
        self.border = border
        self.width = MAP_COLS * self.tile_size
        self.height = MAP_ROWS * self.tile_size
        self.surface = pygame.Surface((self.width, self.height))
        self.surface.set_alpha(225)

        self.wall_colors = {
            1: (150, 140, 130),  # Stone
            2: (170, 75, 55),    # Brick
            3: (110, 75, 45),    # Wood
            4: (220, 215, 205),  # Plaster
        }

    def render(self, dest_surface: pygame.Surface, camera, character, fov_rad: float):
        self.surface.fill((20, 24, 30))

        # Draw grid walls
        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                tile = WORLD_MAP[r][c]
                if tile > 0:
                    color = self.wall_colors.get(tile, (120, 120, 120))
                    rect = pygame.Rect(
                        c * self.tile_size,
                        r * self.tile_size,
                        self.tile_size,
                        self.tile_size,
                    )
                    pygame.draw.rect(self.surface, color, rect)
                    pygame.draw.rect(self.surface, (40, 45, 55), rect, 1)

        # Draw Character (White Bean) position in clean white
        char_x = character.x * self.tile_size
        char_y = character.y * self.tile_size
        pygame.draw.circle(self.surface, (245, 245, 250), (int(char_x), int(char_y)), 4)

        # Draw Character Facing Heading
        head_len = 8.0
        hx = char_x + math.cos(character.heading) * head_len
        hy = char_y + math.sin(character.heading) * head_len
        pygame.draw.line(self.surface, (255, 255, 255), (char_x, char_y), (hx, hy), 2)

        # Draw Camera position in Yellow
        cam_x = camera.x * self.tile_size
        cam_y = camera.y * self.tile_size
        pygame.draw.circle(self.surface, (255, 220, 40), (int(cam_x), int(cam_y)), 3)

        # Draw Camera Viewing Frustum
        cone_len = 22.0
        left_angle = camera.angle - fov_rad / 2.0
        right_angle = camera.angle + fov_rad / 2.0

        lx = cam_x + math.cos(left_angle) * cone_len
        ly = cam_y + math.sin(left_angle) * cone_len
        rx = cam_x + math.cos(right_angle) * cone_len
        ry = cam_y + math.sin(right_angle) * cone_len

        pygame.draw.line(self.surface, (255, 230, 80), (cam_x, cam_y), (lx, ly), 1)
        pygame.draw.line(self.surface, (255, 230, 80), (cam_x, cam_y), (rx, ry), 1)

        # Connect camera to character with subtle tether line in 3rd person
        if camera.mode == camera.THIRD_PERSON:
            pygame.draw.line(self.surface, (120, 150, 180), (cam_x, cam_y), (char_x, char_y), 1)

        # Border
        dest_surface.blit(self.surface, (self.border, self.border))
        border_rect = pygame.Rect(self.border - 1, self.border - 1, self.width + 2, self.height + 2)
        pygame.draw.rect(dest_surface, (200, 180, 130), border_rect, 1)
