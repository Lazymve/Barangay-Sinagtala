import pygame
from terrain import TerrainType, TERRAIN_METADATA
from autotile import Autotiler

TILE_SIZE = 32
CHUNK_TILES = 16
CHUNK_PIXELS = CHUNK_TILES * TILE_SIZE


class TileMap:
    """
    Manages the 160x120 multi-layer terrain grid with 2D spatial-hashed
    tile variant picking (16 grass variants, 8 ground variants) and decal overlays.
    """

    def __init__(self, width, height, asset_loader):
        self.width = width
        self.height = height
        self.pixel_width = width * TILE_SIZE
        self.pixel_height = height * TILE_SIZE
        self.assets = asset_loader
        self.autotiler = Autotiler()

        self.base_grid = [[TerrainType.SHORT_GRASS for _ in range(width)] for _ in range(height)]
        self.detail_grid = [[None for _ in range(width)] for _ in range(height)]
        self.collision_grid = [[False for _ in range(width)] for _ in range(height)]
        self.water_positions = []
        self.chunk_cache = {}

    @staticmethod
    def _hash2d(x, y, salt=0):
        """Non-repeating 2D spatial hash so grass tiles never form diagonal stripes."""
        h = (x * 374761393 + y * 668265263 + salt * 1442695041) & 0xFFFFFFFF
        h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
        return (h ^ (h >> 16)) & 0xFFFFFFFF

    def set_terrain(self, x, y, t_type):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.base_grid[y][x] = t_type
            self.collision_grid[y][x] = not TERRAIN_METADATA[t_type]["walkable"]

    def fill_rect(self, x, y, w, h, t_type):
        for ty in range(max(0, y), min(self.height, y + h)):
            for tx in range(max(0, x), min(self.width, x + w)):
                self.set_terrain(tx, ty, t_type)

    def fill_ellipse(self, cx, cy, rx, ry, t_type):
        for ty in range(max(0, cy - ry), min(self.height, cy + ry + 1)):
            for tx in range(max(0, cx - rx), min(self.width, cx + rx + 1)):
                if ((tx - cx) / max(1, rx)) ** 2 + ((ty - cy) / max(1, ry)) ** 2 <= 1.0:
                    self.set_terrain(tx, ty, t_type)

    def set_detail(self, x, y, sprite_key):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.detail_grid[y][x] = sprite_key

    def bake_chunks(self):
        """Pre-renders 16x16 tile chunks with randomized grass picks, decals, and autotiling."""
        self.chunk_cache.clear()
        self.water_positions.clear()
        chunks_x = (self.width + CHUNK_TILES - 1) // CHUNK_TILES
        chunks_y = (self.height + CHUNK_TILES - 1) // CHUNK_TILES

        grass_types = (
            TerrainType.SHORT_GRASS,
            TerrainType.DENSE_GRASS,
            TerrainType.FLOWERING_GRASS,
            TerrainType.FOREST_GROUND,
        )

        for cy in range(chunks_y):
            for cx in range(chunks_x):
                chunk_surf = pygame.Surface((CHUNK_PIXELS, CHUNK_PIXELS), pygame.SRCALPHA)
                for ly in range(CHUNK_TILES):
                    gy = cy * CHUNK_TILES + ly
                    if gy >= self.height:
                        continue
                    for lx in range(CHUNK_TILES):
                        gx = cx * CHUNK_TILES + lx
                        if gx >= self.width:
                            continue
                        t_type = self.base_grid[gy][gx]
                        t_key = TERRAIN_METADATA[t_type]["key"]

                        # Pick from 16 variants for grass types, 8 for other terrains
                        h_val = self._hash2d(gx, gy, salt=1)
                        num_vars = 16 if t_type in grass_types else 8
                        variant = h_val % num_vars
                        sprite = (
                            self.assets.sprites.get(f"{t_key}_{variant}")
                            or self.assets.sprites.get(f"{t_key}_{variant % 4}")
                            or self.assets.sprites.get(f"{t_key}_0")
                        )

                        px, py = lx * TILE_SIZE, ly * TILE_SIZE
                        if sprite:
                            chunk_surf.blit(sprite, (px, py))

                        # Extra grass tuft decal stamp from TX Tileset Grass.png on 35% of grass tiles
                        if t_type in grass_types and self.assets.grass_decals:
                            h_decal = self._hash2d(gx, gy, salt=99)
                            if (h_decal % 100) < 35:
                                decal = self.assets.grass_decals[h_decal % len(self.assets.grass_decals)]
                                chunk_surf.blit(decal, (px, py))

                        # Autotile transition overlay
                        mask = self.autotiler.compute_bitmask(self.base_grid, gx, gy, self.width, self.height)
                        overlay = self.autotiler.get_transition_overlay(t_type, mask)
                        if overlay:
                            chunk_surf.blit(overlay, (px, py))

                        # Ground detail layer (cliff walls, stairs)
                        det_key = self.detail_grid[gy][gx]
                        if det_key and det_key in self.assets.sprites:
                            chunk_surf.blit(self.assets.sprites[det_key], (px, py))

                        if t_type == TerrainType.WATER:
                            self.water_positions.append((gx, gy, mask))

                self.chunk_cache[(cx, cy)] = chunk_surf

    def render_visible(self, target_surf, camera, water_frame_idx=0):
        view_rect = camera.get_world_viewport()
        start_cx = max(0, int(view_rect.left // CHUNK_PIXELS))
        end_cx = min((self.width - 1) // CHUNK_TILES, int(view_rect.right // CHUNK_PIXELS))
        start_cy = max(0, int(view_rect.top // CHUNK_PIXELS))
        end_cy = min((self.height - 1) // CHUNK_TILES, int(view_rect.bottom // CHUNK_PIXELS))

        for cy in range(start_cy, end_cy + 1):
            for cx in range(start_cx, end_cx + 1):
                chunk = self.chunk_cache.get((cx, cy))
                if chunk:
                    wx, wy = cx * CHUNK_PIXELS, cy * CHUNK_PIXELS
                    sx, sy = camera.world_to_screen(wx, wy)
                    target_surf.blit(chunk, (sx, sy))

        water_sprite = self.assets.sprites.get(f"water_{water_frame_idx % 4}")
        if water_sprite:
            start_tx = max(0, int(view_rect.left // TILE_SIZE))
            end_tx = min(self.width - 1, int(view_rect.right // TILE_SIZE))
            start_ty = max(0, int(view_rect.top // TILE_SIZE))
            end_ty = min(self.height - 1, int(view_rect.bottom // TILE_SIZE))
            for ty in range(start_ty, end_ty + 1):
                row = self.base_grid[ty]
                for tx in range(start_tx, end_tx + 1):
                    if row[tx] == TerrainType.WATER:
                        wx, wy = tx * TILE_SIZE, ty * TILE_SIZE
                        sx, sy = camera.world_to_screen(wx, wy)
                        target_surf.blit(water_sprite, (sx, sy))
                        mask = self.autotiler.compute_bitmask(self.base_grid, tx, ty, self.width, self.height)
                        ov = self.autotiler.get_transition_overlay(TerrainType.WATER, mask)
                        if ov:
                            target_surf.blit(ov, (sx, sy))