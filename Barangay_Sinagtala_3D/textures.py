"""
Procedural texture generator for Barangay Sinagtala 3D.
Generates 128x128 pixel-textured surfaces for wall types and environments,
ensuring standalone operation without external asset dependencies.
"""

import pygame
import random

TEXTURE_SIZE = 128


def create_stone_texture() -> pygame.Surface:
    """Colonial stone masonry with cut blocks and dark mortar."""
    surf = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
    surf.fill((165, 155, 140))  # Base sandstone color

    # Add stone block joints (mortar lines)
    mortar_color = (75, 70, 65)
    row_h = TEXTURE_SIZE // 4
    for r in range(4):
        y = r * row_h
        pygame.draw.line(surf, mortar_color, (0, y), (TEXTURE_SIZE, y), 3)
        offset = (TEXTURE_SIZE // 4) if (r % 2 == 1) else 0
        for c in range(4):
            x = (c * (TEXTURE_SIZE // 2) + offset) % TEXTURE_SIZE
            pygame.draw.line(surf, mortar_color, (x, y), (x, y + row_h), 3)

    # Procedural surface texture noise
    rng = random.Random(42)
    for _ in range(600):
        nx = rng.randint(0, TEXTURE_SIZE - 1)
        ny = rng.randint(0, TEXTURE_SIZE - 1)
        shade = rng.randint(-25, 25)
        base = surf.get_at((nx, ny))
        r = max(0, min(255, base.r + shade))
        g = max(0, min(255, base.g + shade))
        b = max(0, min(255, base.b + shade))
        surf.set_at((nx, ny), (r, g, b))

    return surf


def create_brick_texture() -> pygame.Surface:
    """Terracotta / colonial clay brick wall."""
    surf = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
    surf.fill((175, 75, 55))  # Rich terracotta red-orange

    mortar_color = (200, 190, 180)
    brick_h = TEXTURE_SIZE // 8
    brick_w = TEXTURE_SIZE // 4

    for r in range(8):
        y = r * brick_h
        pygame.draw.line(surf, mortar_color, (0, y), (TEXTURE_SIZE, y), 2)
        shift = (brick_w // 2) if (r % 2 == 1) else 0
        for c in range(6):
            x = (c * brick_w + shift) % TEXTURE_SIZE
            pygame.draw.line(surf, mortar_color, (x, y), (x, y + brick_h), 2)

    # Subtle brick weathering
    rng = random.Random(101)
    for _ in range(800):
        nx = rng.randint(0, TEXTURE_SIZE - 1)
        ny = rng.randint(0, TEXTURE_SIZE - 1)
        shade = rng.randint(-30, 20)
        base = surf.get_at((nx, ny))
        r = max(0, min(255, base.r + shade))
        g = max(0, min(255, base.g + shade // 2))
        b = max(0, min(255, base.b + shade // 2))
        surf.set_at((nx, ny), (r, g, b))

    return surf


def create_wood_texture() -> pygame.Surface:
    """Weathered timber planks with woodgrain."""
    surf = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
    surf.fill((110, 72, 42))

    plank_w = TEXTURE_SIZE // 4
    seam_color = (55, 35, 20)
    for c in range(4):
        x = c * plank_w
        pygame.draw.line(surf, seam_color, (x, 0), (x, TEXTURE_SIZE), 3)

    # Vertical grain lines
    rng = random.Random(202)
    for _ in range(700):
        x = rng.randint(0, TEXTURE_SIZE - 1)
        y = rng.randint(0, TEXTURE_SIZE - 1)
        length = rng.randint(4, 18)
        color = (rng.randint(70, 125), rng.randint(45, 80), rng.randint(25, 50))
        pygame.draw.line(surf, color, (x, y), (x, min(TEXTURE_SIZE - 1, y + length)), 1)

    return surf


def create_plaster_texture() -> pygame.Surface:
    """Antique white-washed Spanish colonial plaster."""
    surf = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
    surf.fill((232, 226, 215))

    rng = random.Random(303)
    for _ in range(1200):
        nx = rng.randint(0, TEXTURE_SIZE - 1)
        ny = rng.randint(0, TEXTURE_SIZE - 1)
        shade = rng.randint(-18, 12)
        base = surf.get_at((nx, ny))
        r = max(0, min(255, base.r + shade))
        g = max(0, min(255, base.g + shade))
        b = max(0, min(255, base.b + shade))
        surf.set_at((nx, ny), (r, g, b))

    return surf


class TextureManager:
    """Manages loaded and procedurally generated textures."""

    def __init__(self):
        self.wall_textures = {
            1: create_stone_texture(),
            2: create_brick_texture(),
            3: create_wood_texture(),
            4: create_plaster_texture(),
        }
        # Pre-darkened textures for East-West walls (creates dynamic depth & directional light)
        self.wall_textures_dark = {}
        for tid, surf in self.wall_textures.items():
            dark = surf.copy()
            dark_overlay = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
            dark_overlay.fill((0, 0, 0))
            dark_overlay.set_alpha(65)
            dark.blit(dark_overlay, (0, 0))
            self.wall_textures_dark[tid] = dark

    def get_texture(self, tile_id: int, is_ew_face: bool = False) -> pygame.Surface:
        textures = self.wall_textures_dark if is_ew_face else self.wall_textures
        return textures.get(tile_id, self.wall_textures[1])
