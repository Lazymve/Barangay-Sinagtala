"""
OpenGL GPU Texture Manager for Barangay Sinagtala 3D.
Generates and binds high-resolution textures for urban GTA-style city environments:
asphalt roads with lane stripes, concrete sidewalks, brick building facades with window grids,
modern skyscraper panels, weathered stone, and rooftop metals.
"""

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

TEXTURE_SIZE = 256


def _create_asphalt_road_texture() -> pygame.Surface:
    """Asphalt roadway with double yellow center lines and white edge lines."""
    surf = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
    surf.fill((38, 40, 44))  # Dark asphalt

    # Asphalt aggregate noise
    import random
    rng = random.Random(42)
    for _ in range(1200):
        x = rng.randint(0, TEXTURE_SIZE - 1)
        y = rng.randint(0, TEXTURE_SIZE - 1)
        shade = rng.randint(-15, 15)
        surf.set_at((x, y), (max(0, 38 + shade), max(0, 40 + shade), max(0, 44 + shade)))

    # White edge lines
    pygame.draw.line(surf, (220, 220, 220), (12, 0), (12, TEXTURE_SIZE), 4)
    pygame.draw.line(surf, (220, 220, 220), (TEXTURE_SIZE - 12, 0), (TEXTURE_SIZE - 12, TEXTURE_SIZE), 4)

    # Double yellow center dividing line (dashed)
    dash_h = TEXTURE_SIZE // 4
    for i in range(4):
        y_start = i * dash_h + 8
        y_end = (i + 1) * dash_h - 12
        pygame.draw.line(surf, (240, 195, 40), (TEXTURE_SIZE // 2 - 4, y_start), (TEXTURE_SIZE // 2 - 4, y_end), 3)
        pygame.draw.line(surf, (240, 195, 40), (TEXTURE_SIZE // 2 + 4, y_start), (TEXTURE_SIZE // 2 + 4, y_end), 3)

    return surf


def _create_sidewalk_texture() -> pygame.Surface:
    """Concrete sidewalk paving slabs with curb edges."""
    surf = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
    surf.fill((165, 168, 172))

    slab_w = TEXTURE_SIZE // 4
    slab_h = TEXTURE_SIZE // 4
    joint_col = (90, 92, 96)

    for x in range(0, TEXTURE_SIZE, slab_w):
        pygame.draw.line(surf, joint_col, (x, 0), (x, TEXTURE_SIZE), 2)
    for y in range(0, TEXTURE_SIZE, slab_h):
        pygame.draw.line(surf, joint_col, (0, y), (TEXTURE_SIZE, y), 2)

    import random
    rng = random.Random(101)
    for _ in range(1500):
        nx = rng.randint(0, TEXTURE_SIZE - 1)
        ny = rng.randint(0, TEXTURE_SIZE - 1)
        s = rng.randint(-20, 20)
        c = surf.get_at((nx, ny))
        surf.set_at((nx, ny), (max(0, min(255, c.r + s)), max(0, min(255, c.g + s)), max(0, min(255, c.b + s))))

    return surf


def _create_brick_building_texture() -> pygame.Surface:
    """GTA III / IV style brownstone brick building with illuminated and dark windows."""
    surf = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
    surf.fill((125, 55, 45))  # Weathered red-brown brick

    # Brick mortar
    for y in range(0, TEXTURE_SIZE, 8):
        pygame.draw.line(surf, (70, 40, 35), (0, y), (TEXTURE_SIZE, y), 1)

    # Window grids (4 rows x 4 cols of windows)
    win_w = 28
    win_h = 38
    step_x = TEXTURE_SIZE // 4
    step_y = TEXTURE_SIZE // 4

    import random
    rng = random.Random(202)

    for r in range(4):
        for c in range(4):
            wx = c * step_x + (step_x - win_w) // 2
            wy = r * step_y + (step_y - win_h) // 2

            # Window frame sill
            pygame.draw.rect(surf, (40, 40, 45), (wx - 2, wy - 2, win_w + 4, win_h + 4))

            # Glass: some lit warm yellow, some dark reflective blue-gray
            is_lit = rng.random() < 0.40
            glass_col = (255, 230, 140) if is_lit else (35, 45, 60)
            pygame.draw.rect(surf, glass_col, (wx, wy, win_w, win_h))

            # Window muntin cross bars
            pygame.draw.line(surf, (30, 30, 35), (wx + win_w // 2, wy), (wx + win_w // 2, wy + win_h), 2)
            pygame.draw.line(surf, (30, 30, 35), (wx, wy + win_h // 2), (wx + win_w, wy + win_h // 2), 2)

    return surf


def _create_modern_tower_texture() -> pygame.Surface:
    """Steel & glass modern skyscraper facade."""
    surf = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
    surf.fill((45, 52, 65))  # Dark slate steel

    step = TEXTURE_SIZE // 8
    for i in range(8):
        y = i * step
        pygame.draw.line(surf, (75, 85, 100), (0, y), (TEXTURE_SIZE, y), 2)
        for j in range(8):
            x = j * step
            pygame.draw.line(surf, (75, 85, 100), (x, 0), (x, TEXTURE_SIZE), 2)
            # Tinted glass pane
            glass_rect = pygame.Rect(x + 2, y + 2, step - 4, step - 4)
            pygame.draw.rect(surf, (30, 42, 58), glass_rect)

    return surf


def _create_rooftop_texture() -> pygame.Surface:
    """Gravel & tar rooftop with metal seams."""
    surf = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
    surf.fill((65, 68, 72))

    import random
    rng = random.Random(303)
    for _ in range(2000):
        x = rng.randint(0, TEXTURE_SIZE - 1)
        y = rng.randint(0, TEXTURE_SIZE - 1)
        s = rng.randint(-25, 25)
        surf.set_at((x, y), (max(0, 65 + s), max(0, 68 + s), max(0, 72 + s)))

    return surf


def _surface_to_gl_texture(surf: pygame.Surface) -> int:
    """Converts a Pygame surface to an OpenGL 2D texture ID with linear mipmaps."""
    tex_data = pygame.image.tostring(surf, "RGBA", True)
    width, height = surf.get_size()

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, width, height, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)

    return tex_id


class GLTextureManager:
    """Manages GPU texture objects and bindings."""

    def __init__(self):
        self.tex_road = 0
        self.tex_sidewalk = 0
        self.tex_brick = 0
        self.tex_tower = 0
        self.tex_roof = 0
        self._init_textures()

    def _init_textures(self):
        self.tex_road = _surface_to_gl_texture(_create_asphalt_road_texture())
        self.tex_sidewalk = _surface_to_gl_texture(_create_sidewalk_texture())
        self.tex_brick = _surface_to_gl_texture(_create_brick_building_texture())
        self.tex_tower = _surface_to_gl_texture(_create_modern_tower_texture())
        self.tex_roof = _surface_to_gl_texture(_create_rooftop_texture())

    def bind(self, tex_id: int):
        glBindTexture(GL_TEXTURE_2D, tex_id)
