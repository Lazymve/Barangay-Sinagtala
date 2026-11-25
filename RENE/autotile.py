import pygame
from terrain import TerrainType, TERRAIN_METADATA

TILE_SIZE = 32


class Autotiler:
    """
    Computes cardinal neighbor bitmasks (N=1, E=2, S=4, W=8) and renders
    organic pixel-art transition edges (such as the mint-green grass & stone
    curb borders around pathways in Reference Image 2, and stepped earthen
    shorelines along rivers).
    """

    def __init__(self):
        self.edge_cache = {}

    @staticmethod
    def compute_bitmask(grid, x, y, width, height):
        current = grid[y][x]
        mask = 0
        # North (1), East (2), South (4), West (8)
        if y == 0 or grid[y - 1][x] == current:
            mask |= 1
        if x == width - 1 or grid[y][x + 1] == current:
            mask |= 2
        if y == height - 1 or grid[y + 1][x] == current:
            mask |= 4
        if x == 0 or grid[y][x - 1] == current:
            mask |= 8
        return mask

    def get_transition_overlay(self, terrain_type, mask):
        if mask == 15:
            return None
        cache_key = (int(terrain_type), mask)
        if cache_key in self.edge_cache:
            return self.edge_cache[cache_key]

        surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        border_rgb = TERRAIN_METADATA[terrain_type]["border_rgb"]
        outer_rgb = (max(0, border_rgb[0] - 28), max(0, border_rgb[1] - 26), max(0, border_rgb[2] - 22), 230)
        inner_rgb = (min(255, border_rgb[0] + 22), min(255, border_rgb[1] + 22), min(255, border_rgb[2] + 18), 210)

        # Pathway & plaza curb lip (Reference Image 2 double-toned border)
        if terrain_type in (
            TerrainType.STONE_PATHWAY, TerrainType.COBBLESTONE, TerrainType.CONCRETE,
            TerrainType.BRICK_FLOORING, TerrainType.DIRT, TerrainType.RICE_FIELD,
            TerrainType.GARDEN_TERRAIN, TerrainType.ELEVATED_STONE
        ):
            if not (mask & 1):  # North edge open
                pygame.draw.rect(surf, outer_rgb, (0, 0, TILE_SIZE, 2))
                pygame.draw.rect(surf, inner_rgb, (0, 2, TILE_SIZE, 2))
            if not (mask & 4):  # South edge open
                pygame.draw.rect(surf, outer_rgb, (0, TILE_SIZE - 2, TILE_SIZE, 2))
                pygame.draw.rect(surf, inner_rgb, (0, TILE_SIZE - 4, TILE_SIZE, 2))
            if not (mask & 8):  # West edge open
                pygame.draw.rect(surf, outer_rgb, (0, 0, 2, TILE_SIZE))
                pygame.draw.rect(surf, inner_rgb, (2, 0, 2, TILE_SIZE))
            if not (mask & 2):  # East edge open
                pygame.draw.rect(surf, outer_rgb, (TILE_SIZE - 2, 0, 2, TILE_SIZE))
                pygame.draw.rect(surf, inner_rgb, (TILE_SIZE - 4, 0, 2, TILE_SIZE))

        elif terrain_type == TerrainType.WATER:
            # Shoreline foam & stepped bank shadow
            foam = (195, 238, 255, 215)
            bank = (142, 112, 74, 245)
            if not (mask & 1):
                pygame.draw.rect(surf, bank, (0, 0, TILE_SIZE, 4))
                pygame.draw.rect(surf, foam, (0, 4, TILE_SIZE, 2))
            if not (mask & 4):
                pygame.draw.rect(surf, foam, (0, TILE_SIZE - 4, TILE_SIZE, 2))
                pygame.draw.rect(surf, bank, (0, TILE_SIZE - 2, TILE_SIZE, 2))
            if not (mask & 8):
                pygame.draw.rect(surf, bank, (0, 0, 3, TILE_SIZE))
                pygame.draw.rect(surf, foam, (3, 0, 2, TILE_SIZE))
            if not (mask & 2):
                pygame.draw.rect(surf, foam, (TILE_SIZE - 5, 0, 2, TILE_SIZE))
                pygame.draw.rect(surf, bank, (TILE_SIZE - 3, 0, 3, TILE_SIZE))

        self.edge_cache[cache_key] = surf
        return surf
