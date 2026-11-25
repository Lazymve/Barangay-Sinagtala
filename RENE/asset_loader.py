import os
import zipfile
import math
import pygame

TILE_SIZE = 32
GRASS_VARIANTS = 16


class AssetLoader:
    """
    Loads, slices, scales, and caches original PNG textures from:
      1. Pixel Art Top Down - Basic v1.2.3 (native 32x32)
      2. FreeEnvironment / FreePack.png (16x16 scaled 2x -> 32x32)
      3. Ninja Adventure - Asset Pack (16x16 scaled 2x -> 32x32)
    Builds 16 rich tile variations for grass and terrain so the ground
    looks lush, organic, and non-repetitive.
    """

    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.sheets = {}
        self.sprites = {}
        self.anim_frames = {}
        self.grass_decals = []
        self._ensure_archives_extracted()
        self._discover_and_load_sheets()
        self._build_asset_manifest()

    def _ensure_archives_extracted(self):
        search_dirs = [self.base_dir, os.path.join(self.base_dir, "assets")]
        for d in search_dirs:
            if not os.path.isdir(d):
                continue
            for fname in os.listdir(d):
                if fname.lower().endswith(".zip"):
                    zpath = os.path.join(d, fname)
                    out_dir = os.path.join(self.base_dir, "assets", os.path.splitext(fname)[0])
                    if not os.path.exists(out_dir):
                        try:
                            with zipfile.ZipFile(zpath, "r") as zf:
                                zf.extractall(out_dir)
                        except Exception as e:
                            print(f"[AssetLoader] Notice extracting {fname}: {e}")

    def _find_file(self, relative_candidates):
        for rel in relative_candidates:
            rel_norm = os.path.normpath(rel)
            for root_dir in [self.base_dir, os.path.join(self.base_dir, "assets")]:
                if not os.path.isdir(root_dir):
                    continue
                direct = os.path.join(root_dir, rel_norm)
                if os.path.isfile(direct):
                    return direct
                target_base = os.path.basename(rel_norm).lower()
                parent_hint = os.path.basename(os.path.dirname(rel_norm)).lower()
                for r, _, files in os.walk(root_dir):
                    for f in files:
                        if f.lower() == target_base:
                            if not parent_hint or parent_hint in r.lower():
                                return os.path.join(r, f)
        return None

    def _load_sheet(self, key, candidates, scale=1):
        path = self._find_file(candidates)
        if path and os.path.isfile(path):
            try:
                surf = pygame.image.load(path).convert_alpha()
                if scale != 1:
                    w, h = surf.get_size()
                    surf = pygame.transform.scale(surf, (int(w * scale), int(h * scale)))
                self.sheets[key] = surf
                return surf
            except Exception as e:
                print(f"[AssetLoader] Failed loading {path}: {e}")
        return None

    def _discover_and_load_sheets(self):
        # Pack 1: Cainos Pixel Art Top Down - Basic (Native 32x32)
        self._load_sheet("tx_grass", ["Texture/TX Tileset Grass.png", "TX Tileset Grass.png"], scale=1)
        self._load_sheet("tx_stone", ["Texture/TX Tileset Stone Ground.png", "TX Tileset Stone Ground.png"], scale=1)
        self._load_sheet("tx_wall", ["Texture/TX Tileset Wall.png", "TX Tileset Wall.png"], scale=1)
        self._load_sheet("tx_struct", ["Texture/TX Struct.png", "TX Struct.png"], scale=1)
        self._load_sheet("tx_plant", ["Texture/Extra/TX Plant with Shadow.png", "Texture/TX Plant.png"], scale=1)
        self._load_sheet("tx_props", ["Texture/Extra/TX Props with Shadow.png", "Texture/TX Props.png"], scale=1)
        self._load_sheet("tx_shadow", ["Texture/TX Shadow.png", "TX Shadow.png"], scale=1)
        self._load_sheet("tx_shadow_plant", ["Texture/TX Shadow Plant.png", "TX Shadow Plant.png"], scale=1)

        # Pack 2: FreeEnvironment (16x16 upscaled 2x to 32x32)
        self._load_sheet("free_pack", ["FreeEnvironment/FreePack.png", "FreePack.png"], scale=2)

        # Pack 3: Ninja Adventure Environmental & Fauna Sheets (16x16 upscaled 2x to 32x32)
        na_sheets = {
            "na_field": ["Backgrounds/Tilesets/TilesetField.png", "TilesetField.png"],
            "na_floor": ["Backgrounds/Tilesets/TilesetFloor.png", "TilesetFloor.png"],
            "na_floor_b": ["Backgrounds/Tilesets/TilesetFloorB.png", "TilesetFloorB.png"],
            "na_floor_detail": ["Backgrounds/Tilesets/TilesetFloorDetail.png", "TilesetFloorDetail.png"],
            "na_nature": ["Backgrounds/Tilesets/TilesetNature.png", "TilesetNature.png"],
            "na_water": ["Backgrounds/Tilesets/TilesetWater.png", "TilesetWater.png"],
            "na_relief": ["Backgrounds/Tilesets/TilesetRelief.png", "TilesetRelief.png"],
            "na_house": ["Backgrounds/Tilesets/TilesetHouse.png", "TilesetHouse.png"],
            "anim_chicken_brown": ["Actor/Animal/Chicken/SpriteSheetBrown.png"],
            "anim_chicken_white": ["Actor/Animal/Chicken/SpriteSheetWhite.png"],
            "anim_dog": ["Actor/Animal/Dog/SpriteSheet.png"],
            "anim_dog_yellow": ["Actor/Animal/DogYellow/SpriteSheet.png"],
            "anim_cat_orange": ["Actor/Animal/CatOrange/SpriteSheet.png"],
            "anim_cat_white": ["Actor/Animal/CatWhite/SpriteSheet.png"],
            "anim_cow": ["Actor/Animal/Cow/SpriteSheetWhite.png"],
            "anim_pig": ["Actor/Animal/Pig/SpriteSheetPink.png"],
            "anim_frog": ["Actor/Animal/Frog/SpriteSheet.png"],
            "anim_fish": ["Actor/Animal/Fish/SpriteSheetRed.png"],
            "anim_parrot_red": ["Actor/Animal/Parrot/SpriteSheetRed.png"],
            "anim_parrot_blue": ["Actor/Animal/Parrot/SpriteSheetBlue.png"],
        }
        for k, paths in na_sheets.items():
            self._load_sheet(k, paths, scale=2)

    def crop(self, sheet_key, x, y, w, h):
        sheet = self.sheets.get(sheet_key)
        if sheet is not None:
            sw, sh = sheet.get_size()
            if x + w <= sw and y + h <= sh:
                sub = sheet.subsurface(pygame.Rect(x, y, w, h)).copy()
                if pygame.mask.from_surface(sub).count() > 8:
                    return sub
        return None

    def _build_asset_manifest(self):
        self._build_terrain_tiles()
        self._build_vegetation_sprites()
        self._build_prop_sprites()
        self._build_philippine_architecture()
        self._build_animated_sprites()

    # ------------------------------------------------------------------
    # RICH PIXEL-ART GRASS & TERRAIN BUILDER (16 Variants for Grass)
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_grass_blade_cluster(surf, x, y, dark_col, mid_col, light_col, style=0):
        """Draws a crisp pixel-art grass tuft, clover, or blade cluster."""
        if style == 0:
            # V-shaped tall tuft
            pygame.draw.rect(surf, dark_col, (x, y + 4, 6, 2))
            pygame.draw.rect(surf, mid_col, (x - 2, y + 2, 2, 2))
            pygame.draw.rect(surf, mid_col, (x + 2, y, 2, 4))
            pygame.draw.rect(surf, mid_col, (x + 6, y + 2, 2, 2))
            pygame.draw.rect(surf, light_col, (x + 2, y, 2, 2))
        elif style == 1:
            # 3-leaf clover patch
            pygame.draw.rect(surf, dark_col, (x + 2, y + 2, 4, 4))
            pygame.draw.rect(surf, mid_col, (x, y + 2, 2, 2))
            pygame.draw.rect(surf, mid_col, (x + 4, y + 2, 2, 2))
            pygame.draw.rect(surf, light_col, (x + 2, y, 2, 2))
        elif style == 2:
            # Swept wind blades
            pygame.draw.rect(surf, dark_col, (x, y + 4, 8, 2))
            pygame.draw.rect(surf, mid_col, (x + 2, y + 2, 6, 2))
            pygame.draw.rect(surf, light_col, (x + 4, y, 4, 2))
        else:
            # Double sprout
            pygame.draw.rect(surf, dark_col, (x, y + 2, 2, 4))
            pygame.draw.rect(surf, light_col, (x, y, 2, 2))
            pygame.draw.rect(surf, dark_col, (x + 4, y + 4, 2, 2))
            pygame.draw.rect(surf, mid_col, (x + 4, y + 2, 2, 2))

    def _make_textured_tile(self, base_rgb, noise_offsets, pattern="speckle", seed=0):
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        surf.fill(base_rgb)
        for py in range(0, TILE_SIZE, 2):
            for px in range(0, TILE_SIZE, 2):
                h = ((px * 374761393 + py * 668265263 + seed * 1442695041) & 0xFFFFFFFF)
                idx = (h >> 11) % len(noise_offsets)
                dc = noise_offsets[idx]

                # Add organic macro-patchiness (sunlit vs shaded grass patches within the tile)
                macro = int(math.sin((px + seed * 7) * 0.22) * math.cos((py + seed * 11) * 0.22) * 8)
                r = max(0, min(255, base_rgb[0] + dc[0] + macro))
                g = max(0, min(255, base_rgb[1] + dc[1] + macro))
                b = max(0, min(255, base_rgb[2] + dc[2] + (macro // 2)))

                if pattern == "cobble":
                    gx, gy = (px // 2) % 8, (py // 2) % 8
                    row_shift = 4 if ((py // 16) % 2 == 1) else 0
                    gx = (gx + row_shift) % 8
                    if gx == 0 or gy == 0:
                        r, g, b = max(0, base_rgb[0] - 28), max(0, base_rgb[1] - 26), max(0, base_rgb[2] - 22)
                    elif gx == 1 or gy == 1:
                        r, g, b = min(255, base_rgb[0] + 16), min(255, base_rgb[1] + 15), min(255, base_rgb[2] + 12)
                elif pattern == "brick":
                    gx, gy = px // 2, py // 2
                    shift = 4 if ((gy // 4) % 2 == 1) else 0
                    if gy % 4 == 0 or (gx + shift) % 8 == 0:
                        r, g, b = max(0, base_rgb[0] - 32), max(0, base_rgb[1] - 26), max(0, base_rgb[2] - 20)
                elif pattern == "wood":
                    gx, gy = px // 2, py // 2
                    if gy % 4 == 0:
                        r, g, b = max(0, base_rgb[0] - 26), max(0, base_rgb[1] - 22), max(0, base_rgb[2] - 18)
                    elif (gx + (gy // 4) * 5) % 15 == 0:
                        r, g, b = max(0, base_rgb[0] - 20), max(0, base_rgb[1] - 16), max(0, base_rgb[2] - 12)
                elif pattern == "rice_paddy":
                    gx, gy = px // 2, py // 2
                    if (gx % 4 in (1, 2)) and (gy % 4 in (1, 2)):
                        r, g, b = (92, 186, 64) if (gx + gy + seed) % 2 == 0 else (68, 152, 48)
                elif pattern == "agri_soil":
                    gy = (py // 2) % 4
                    if gy in (0, 1):
                        r, g, b = max(0, r - 18), max(0, g - 15), max(0, b - 12)
                pygame.draw.rect(surf, (r, g, b), (px, py, 2, 2))
        return surf

    def _extract_cainos_grass_Subtiles(self):
        """Extracts all solid grass tiles & decorative tuft overlays from TX Tileset Grass.png."""
        solid_tiles = []
        decal_tiles = []
        sheet = self.sheets.get("tx_grass")
        if sheet is not None:
            sw, sh = sheet.get_size()
            for y in range(0, sh, 32):
                for x in range(0, sw, 32):
                    sub = sheet.subsurface(pygame.Rect(x, y, 32, 32)).copy()
                    opaque_px = pygame.mask.from_surface(sub).count()
                    if opaque_px >= 980:  # Full 32x32 grass tile (1024 px total)
                        solid_tiles.append(sub)
                    elif 40 <= opaque_px < 900 and y >= 128:  # Bottom-half grass tufts/flowers
                        decal_tiles.append(sub)
        return solid_tiles, decal_tiles

    def _build_terrain_tiles(self):
        cainos_solids, cainos_decals = self._extract_cainos_grass_Subtiles()
        self.grass_decals = cainos_decals

        # 1. SHORT GRASS — 16 Distinct Lush Variations
        for v in range(GRASS_VARIANTS):
            base = self._make_textured_tile(
                (102, 178, 68),
                [(0, 0, 0), (10, 16, 6), (-10, -14, -6), (14, 20, 8), (-6, -10, -4), (4, 8, 2)],
                seed=v * 17 + 10
            )
            if cainos_solids:
                c_tile = cainos_solids[v % len(cainos_solids)].copy()
                c_tile.set_alpha(150)
                base.blit(c_tile, (0, 0))
            if cainos_decals and v % 2 == 1:
                base.blit(cainos_decals[(v * 3) % len(cainos_decals)], (0, 0))

            # Add 3 to 6 varied pixel-art grass tufts & clovers per tile
            tuft_count = 3 + (v % 4)
            for i in range(tuft_count):
                tx = ((v * 11 + i * 7 + 3) % 12) * 2 + 2
                ty = ((v * 7 + i * 13 + 5) % 12) * 2 + 2
                self._draw_grass_blade_cluster(
                    base, tx, ty,
                    dark_col=(62, 132, 42),
                    mid_col=(84, 162, 56),
                    light_col=(136, 208, 88),
                    style=(v + i) % 4
                )
            # Occasional tiny pebble or warm sunlit clover speck
            if v % 3 == 0:
                px = ((v * 5 + 4) % 12) * 2 + 4
                py = ((v * 9 + 6) % 12) * 2 + 4
                pygame.draw.rect(base, (154, 152, 140), (px, py, 4, 2))
                pygame.draw.rect(base, (192, 190, 178), (px, py, 2, 2))
            self.sprites[f"short_grass_{v}"] = base

        # 2. DENSE GRASS — 16 Rich Meadow / Undergrowth Variations
        for v in range(GRASS_VARIANTS):
            tile = self._make_textured_tile(
                (76, 148, 52),
                [(0, 0, 0), (-12, -16, -8), (12, 18, 6), (-8, -12, -4), (16, 22, 8)],
                seed=v * 23 + 200
            )
            if cainos_decals:
                tile.blit(cainos_decals[v % len(cainos_decals)], (0, 0))
            for i in range(8):
                tx = ((v * 9 + i * 5 + 1) % 12) * 2 + 2
                ty = ((v * 13 + i * 7 + 2) % 12) * 2 + 2
                self._draw_grass_blade_cluster(
                    tile, tx, ty,
                    dark_col=(46, 106, 32),
                    mid_col=(68, 138, 46),
                    light_col=(118, 194, 76),
                    style=(v + i) % 4
                )
            self.sprites[f"dense_grass_{v}"] = tile

        # 3. FLOWERING GRASS — 16 Wildflower Meadow Variations
        flower_palettes = [
            ((255, 228, 76), (255, 168, 36)),   # Golden buttercup
            ((255, 122, 164), (255, 240, 180)), # Bougainvillea pink
            ((245, 250, 255), (255, 225, 90)),  # Sampaguita white
            ((186, 136, 255), (255, 238, 120)), # Tropical lilac
            ((255, 154, 72), (255, 236, 140)),  # Caballero orange
        ]
        for v in range(GRASS_VARIANTS):
            tile = self.sprites[f"short_grass_{v}"].copy()
            flower_count = 3 + (v % 4)
            for i in range(flower_count):
                fx = ((v * 7 + i * 9 + 2) % 11) * 2 + 4
                fy = ((v * 11 + i * 5 + 3) % 11) * 2 + 4
                petal_col, center_col = flower_palettes[(v + i) % len(flower_palettes)]
                # Leaf base
                pygame.draw.rect(tile, (52, 122, 38), (fx - 2, fy + 2, 8, 2))
                # Petals (cross or cluster shape)
                pygame.draw.rect(tile, petal_col, (fx, fy - 2, 4, 6))
                pygame.draw.rect(tile, petal_col, (fx - 2, fy, 8, 2))
                pygame.draw.rect(tile, center_col, (fx, fy, 2, 2))
            self.sprites[f"flowering_grass_{v}"] = tile

        # 4. Dirt (8 variations)
        for v in range(8):
            self.sprites[f"dirt_{v}"] = self._make_textured_tile(
                (186, 142, 96),
                [(0, 0, 0), (10, 8, 5), (-12, -9, -6), (14, 10, 6), (-8, -6, -4)],
                seed=v + 40
            )

        # 5. Sandy Ground (8 variations)
        for v in range(8):
            self.sprites[f"sandy_ground_{v}"] = self._make_textured_tile(
                (232, 206, 148),
                [(0, 0, 0), (12, 10, 6), (-10, -8, -5), (8, 6, 4)],
                seed=v + 50
            )

        # 6. Stone Pathway (8 variations)
        for v in range(8):
            tile = self._make_textured_tile(
                (232, 216, 188),
                [(0, 0, 0), (8, 7, 5), (-8, -7, -5), (5, 4, 3)],
                pattern="cobble",
                seed=v + 60
            )
            stone_crop = self.crop("tx_stone", (v % 4) * 32, 32, 32, 32)
            if stone_crop is not None:
                stone_tint = stone_crop.copy()
                stone_tint.fill((245, 232, 210, 95), special_flags=pygame.BLEND_RGBA_MULT)
                tile.blit(stone_tint, (0, 0))
            self.sprites[f"stone_pathway_{v}"] = tile

        # 7. Cobblestone (8 variations)
        for v in range(8):
            self.sprites[f"cobblestone_{v}"] = self._make_textured_tile(
                (168, 162, 152),
                [(0, 0, 0), (14, 14, 12), (-16, -16, -14), (10, 9, 8)],
                pattern="cobble",
                seed=v + 70
            )

        # 8. Brick Flooring (8 variations)
        for v in range(8):
            self.sprites[f"brick_flooring_{v}"] = self._make_textured_tile(
                (196, 114, 88),
                [(0, 0, 0), (14, 9, 7), (-14, -9, -7), (9, 5, 5)],
                pattern="brick",
                seed=v + 80
            )

        # 9. Concrete (8 variations)
        for v in range(8):
            tile = self._make_textured_tile(
                (204, 202, 196),
                [(0, 0, 0), (6, 6, 6), (-7, -7, -7), (4, 4, 4)],
                seed=v + 90
            )
            pygame.draw.line(tile, (182, 180, 174), (0, 31), (31, 31), 1)
            pygame.draw.line(tile, (218, 216, 210), (0, 0), (31, 0), 1)
            self.sprites[f"concrete_{v}"] = tile

        # 10. Wooden Flooring (8 variations)
        for v in range(8):
            self.sprites[f"wooden_flooring_{v}"] = self._make_textured_tile(
                (166, 114, 68),
                [(0, 0, 0), (12, 8, 5), (-12, -8, -5), (7, 5, 3)],
                pattern="wood",
                seed=v + 100
            )

        # 11. Water (Animated frames 0..3)
        for f in range(4):
            tile = self._make_textured_tile(
                (52, 148, 226),
                [(0, 0, 0), (10, 16, 20), (-8, -12, -14), (6, 12, 16)],
                seed=110
            )
            offset = (f * 4) % 16
            for wy in (6, 18, 26):
                wx = (wy * 3 + offset) % 24
                pygame.draw.rect(tile, (135, 206, 250), (wx, wy, 6, 2))
                pygame.draw.rect(tile, (210, 242, 255), (wx + 2, wy, 2, 2))
            self.sprites[f"water_{f}"] = tile

        # 12. Riverbank (8 variations)
        for v in range(8):
            tile = self._make_textured_tile(
                (156, 126, 88),
                [(0, 0, 0), (-16, -12, -8), (14, 10, 6), (-8, -6, -4)],
                seed=v + 120
            )
            for rx in range(0, 32, 8):
                pygame.draw.rect(tile, (124, 98, 66), (rx, 20, 6, 8))
                pygame.draw.rect(tile, (184, 152, 110), (rx + 1, 18, 4, 4))
            self.sprites[f"riverbank_{v}"] = tile

        # 13. Mud (8 variations)
        for v in range(8):
            self.sprites[f"mud_{v}"] = self._make_textured_tile(
                (118, 88, 62),
                [(0, 0, 0), (-10, -8, -6), (8, 6, 4), (-6, -5, -4)],
                seed=v + 130
            )

        # 14. Gravel (8 variations)
        for v in range(8):
            self.sprites[f"gravel_{v}"] = self._make_textured_tile(
                (158, 154, 146),
                [(0, 0, 0), (18, 18, 16), (-18, -18, -16), (10, 10, 8), (-12, -12, -10)],
                seed=v + 140
            )

        # 15. Agricultural Soil (8 variations)
        for v in range(8):
            self.sprites[f"agricultural_soil_{v}"] = self._make_textured_tile(
                (112, 78, 52),
                [(0, 0, 0), (8, 6, 4), (-8, -6, -4)],
                pattern="agri_soil",
                seed=v + 150
            )

        # 16. Rice Field Terrain (8 variations)
        for v in range(8):
            self.sprites[f"rice_field_{v}"] = self._make_textured_tile(
                (76, 146, 134),
                [(0, 0, 0), (8, 14, 10), (-6, -10, -8)],
                pattern="rice_paddy",
                seed=v + 160
            )

        # 17. Garden Terrain (8 variations)
        for v in range(8):
            tile = self._make_textured_tile(
                (128, 92, 60),
                [(0, 0, 0), (10, 8, 5), (-10, -7, -5)],
                pattern="agri_soil",
                seed=v + 170
            )
            pygame.draw.rect(tile, (96, 66, 40), (0, 0, 32, 32), 2)
            self.sprites[f"garden_terrain_{v}"] = tile

        # 18. Forest Ground — 16 Deep Mossy Tropical Humus Variations
        for v in range(GRASS_VARIANTS):
            tile = self._make_textured_tile(
                (58, 114, 46),
                [(0, 0, 0), (-10, -14, -6), (12, 16, 6), (-14, -18, -8), (8, 12, 4)],
                seed=v * 19 + 180
            )
            for i in range(6):
                tx = ((v * 13 + i * 7 + 2) % 12) * 2 + 2
                ty = ((v * 5 + i * 11 + 4) % 12) * 2 + 2
                self._draw_grass_blade_cluster(
                    tile, tx, ty,
                    dark_col=(36, 82, 28),
                    mid_col=(52, 112, 40),
                    light_col=(92, 164, 62),
                    style=(v + i) % 4
                )
            # Fallen leaf or forest mushroom speck
            if v % 2 == 0:
                lx = ((v * 7 + 3) % 12) * 2 + 4
                ly = ((v * 11 + 5) % 12) * 2 + 4
                pygame.draw.rect(tile, (168, 112, 54), (lx, ly, 4, 2))
            self.sprites[f"forest_ground_{v}"] = tile

        # 19. Elevated Stone Terrain (8 variations, Reference Image 1 warm olive moss)
        for v in range(8):
            tile = self._make_textured_tile(
                (144, 158, 68),
                [(0, 0, 0), (10, 12, 4), (-10, -12, -4), (6, 8, 2)],
                seed=v + 190
            )
            for i in range(4):
                tx = ((v * 7 + i * 9) % 12) * 2 + 2
                ty = ((v * 5 + i * 7) % 10) * 2 + 8
                self._draw_grass_blade_cluster(
                    tile, tx, ty,
                    dark_col=(98, 118, 42),
                    mid_col=(128, 146, 56),
                    light_col=(172, 186, 82),
                    style=(v + i) % 4
                )
            pygame.draw.rect(tile, (176, 174, 166), (0, 0, 32, 6))
            pygame.draw.rect(tile, (132, 130, 122), (0, 6, 32, 2))
            self.sprites[f"elevated_stone_{v}"] = tile

        wall_face = self._make_textured_tile(
            (146, 142, 134),
            [(0, 0, 0), (10, 10, 8), (-12, -12, -10)],
            pattern="brick",
            seed=205
        )
        pygame.draw.rect(wall_face, (186, 184, 176), (0, 0, 32, 4))
        pygame.draw.rect(wall_face, (96, 124, 58), (6, 14, 8, 4))
        self.sprites["cliff_wall_face"] = wall_face

        stairs = pygame.Surface((32, 32), pygame.SRCALPHA)
        for step in range(4):
            sy = step * 8
            pygame.draw.rect(stairs, (188, 184, 174), (0, sy, 32, 6))
            pygame.draw.rect(stairs, (132, 128, 118), (0, sy + 6, 32, 2))
            pygame.draw.rect(stairs, (152, 148, 138), (0, sy, 4, 8))
            pygame.draw.rect(stairs, (152, 148, 138), (28, sy, 4, 8))
        pygame.draw.rect(stairs, (112, 152, 62), (10, 12, 6, 4))
        self.sprites["stone_stairs"] = stairs

    # ------------------------------------------------------------------
    # VEGETATION & TROPICAL FLORA
    # ------------------------------------------------------------------
    def _build_vegetation_sprites(self):
        cainos_tree_1 = self.crop("tx_plant", 0, 0, 160, 160)
        cainos_tree_2 = self.crop("tx_plant", 160, 0, 128, 160)
        cainos_tree_3 = self.crop("tx_plant", 288, 0, 128, 160)

        self.sprites["tree_acacia_large"] = self._create_lush_tree(
            128, 144,
            [(38, 92, 42), (54, 126, 56), (78, 162, 68), (116, 196, 86)],
            trunk_rgb=(108, 74, 48),
            base_sprite=cainos_tree_1
        )
        self.sprites["tree_mango"] = self._create_lush_tree(
            112, 128,
            [(44, 108, 48), (64, 144, 62), (96, 178, 76), (138, 208, 92)],
            trunk_rgb=(98, 68, 44),
            fruit_rgb=(255, 196, 46),
            base_sprite=cainos_tree_2
        )
        self.sprites["tree_narra_gold"] = self._create_lush_tree(
            112, 128,
            [(126, 138, 38), (162, 168, 48), (198, 196, 68), (232, 224, 96)],
            trunk_rgb=(116, 84, 56),
            base_sprite=cainos_tree_3
        )
        self.sprites["tree_caballero_pink"] = self._create_lush_tree(
            96, 112,
            [(168, 64, 108), (212, 92, 142), (244, 134, 178), (255, 182, 212)],
            trunk_rgb=(104, 72, 52)
        )
        self.sprites["tree_pine_tropical"] = self._create_pine_tree(80, 112)
        self.sprites["tree_coconut"] = self._create_coconut_palm(96, 128)
        self.sprites["tree_banana"] = self._create_banana_plant(64, 80)

        self.sprites["bush_round"] = self._create_bush(48, 44, [(42, 108, 46), (68, 148, 62), (104, 184, 84)])
        self.sprites["bush_flowering"] = self._create_bush(
            48, 44, [(42, 108, 46), (68, 148, 62), (104, 184, 84)], flower_rgb=(255, 112, 156)
        )
        self.sprites["flower_bed_box"] = self._create_flower_planter(64, 36, [(255, 92, 128), (255, 214, 64), (138, 112, 248)])
        self.sprites["potted_fern"] = self._create_potted_plant((72, 168, 68), flower_rgb=None)
        self.sprites["potted_bougainvillea"] = self._create_potted_plant((64, 148, 58), flower_rgb=(242, 72, 136))
        self.sprites["lilypad"] = self._create_lilypad()

    def _create_lush_tree(self, w, h, palette, trunk_rgb=(104, 72, 46), fruit_rgb=None, base_sprite=None):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (16, 24, 18, 95), (w // 6, h - 28, (w * 2) // 3, 24))
        if base_sprite is not None:
            scaled = pygame.transform.scale(base_sprite, (w, h))
            surf.blit(scaled, (0, 0))
            if fruit_rgb:
                for fx, fy in [(w // 3, h // 3), (w // 2 + 12, h // 3 + 8), (w // 2 - 14, h // 2 - 6), (w // 2 + 6, h // 2 - 12)]:
                    pygame.draw.circle(surf, fruit_rgb, (fx, fy), 4)
                    pygame.draw.circle(surf, (255, 240, 150), (fx - 1, fy - 1), 2)
            return surf

        tw = max(12, w // 7)
        tx = w // 2 - tw // 2
        pygame.draw.rect(surf, trunk_rgb, (tx, h - 46, tw, 36), border_radius=3)
        pygame.draw.rect(surf, (max(0, trunk_rgb[0] - 24), max(0, trunk_rgb[1] - 20), max(0, trunk_rgb[2] - 16)), (tx, h - 46, 4, 36))

        clusters = [
            (w // 2, h // 2 - 4, w // 3 + 4),
            (w // 3, h // 2 + 2, w // 4 + 2),
            ((w * 2) // 3, h // 2 + 2, w // 4 + 2),
            (w // 2 - 10, h // 3, w // 4 + 4),
            (w // 2 + 10, h // 3, w // 4 + 4),
            (w // 2, h // 4 + 4, w // 4),
        ]
        for layer_idx, col in enumerate(palette):
            shrink = layer_idx * 4
            shift_y = -layer_idx * 3
            for cx, cy, cr in clusters:
                r = max(6, cr - shrink)
                pygame.draw.circle(surf, col, (cx, cy + shift_y), r)
        if fruit_rgb:
            for fx, fy in [(w // 3 + 4, h // 3 + 6), (w // 2 + 14, h // 3 + 10), (w // 2 - 8, h // 2 - 4), (w // 2 + 6, h // 4 + 12)]:
                pygame.draw.circle(surf, fruit_rgb, (fx, fy), 4)
        return surf

    def _create_pine_tree(self, w, h):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (16, 24, 18, 95), (10, h - 24, w - 20, 20))
        pygame.draw.rect(surf, (96, 64, 42), (w // 2 - 6, h - 30, 12, 22))
        tiers = [(h - 26, w - 12, 34), (h - 46, w - 22, 32), (h - 66, w - 34, 30), (h - 84, w - 46, 26)]
        for by, bw, bh in tiers:
            pts = [(w // 2, by - bh), (w // 2 - bw // 2, by), (w // 2 + bw // 2, by)]
            pygame.draw.polygon(surf, (36, 96, 54), pts)
            pts_inner = [(w // 2, by - bh + 3), (w // 2 - bw // 2 + 4, by - 3), (w // 2 + bw // 2 - 4, by - 3)]
            pygame.draw.polygon(surf, (58, 138, 72), pts_inner)
            pts_hi = [(w // 2, by - bh + 5), (w // 2 - bw // 4, by - 8), (w // 2 + bw // 4, by - 8)]
            pygame.draw.polygon(surf, (92, 174, 94), pts_hi)
        return surf

    def _create_coconut_palm(self, w, h):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (16, 24, 18, 85), (w // 4, h - 22, w // 2, 18))
        cx = w // 2
        for seg in range(10):
            sy = h - 18 - seg * 7
            sx = cx + int(math.sin(seg * 0.35) * 6)
            sw = max(6, 12 - seg // 3)
            pygame.draw.rect(surf, (132, 96, 62), (sx - sw // 2, sy - 7, sw, 8), border_radius=2)
            pygame.draw.line(surf, (98, 68, 42), (sx - sw // 2, sy - 1), (sx + sw // 2, sy - 1), 2)
        top_x = cx + int(math.sin(9 * 0.35) * 6)
        top_y = h - 18 - 9 * 7
        for n_off in [(-5, 2), (4, 3), (0, 6)]:
            pygame.draw.circle(surf, (92, 62, 32), (top_x + n_off[0], top_y + n_off[1]), 5)
        frond_angles = [-155, -120, -70, -25, 20, 65, 115, 155]
        for ang in frond_angles:
            rad = math.radians(ang)
            pts = [(top_x, top_y)]
            for step in range(1, 7):
                px = top_x + int(math.cos(rad) * step * 6)
                py = top_y + int(math.sin(rad) * step * 4) + (step * step) // 2
                pts.append((px, py))
            pygame.draw.lines(surf, (46, 124, 48), False, pts, 5)
            pygame.draw.lines(surf, (98, 184, 72), False, pts[:-1], 3)
        return surf

    def _create_banana_plant(self, w, h):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (16, 24, 18, 80), (12, h - 16, w - 24, 14))
        cx, cy = w // 2, h - 18
        pygame.draw.rect(surf, (88, 138, 52), (cx - 5, cy - 22, 10, 22))
        leaves = [(-22, -26, 24, 12), (4, -26, 24, 12), (-26, -14, 24, 10), (6, -14, 24, 10), (-10, -38, 20, 16)]
        for lx, ly, lw, lh in leaves:
            pygame.draw.ellipse(surf, (72, 158, 54), (cx + lx, cy + ly, lw, lh))
            pygame.draw.ellipse(surf, (118, 198, 78), (cx + lx + 2, cy + ly + 2, lw - 4, lh - 4))
        pygame.draw.circle(surf, (248, 214, 54), (cx + 6, cy - 12), 5)
        return surf

    def _create_bush(self, w, h, palette, flower_rgb=None):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (16, 24, 18, 85), (4, h - 12, w - 8, 10))
        blobs = [(w // 2, h // 2, 14), (w // 3, h // 2 + 4, 12), ((w * 2) // 3, h // 2 + 4, 12), (w // 2, h // 3 + 2, 11)]
        for idx, col in enumerate(palette):
            for bx, by, br in blobs:
                pygame.draw.circle(surf, col, (bx, by - idx * 2), max(4, br - idx * 3))
        if flower_rgb:
            for fx, fy in [(w // 3, h // 2), (w // 2 + 6, h // 3 + 4), (w // 2 - 4, h // 3 + 2), ((w * 2) // 3 - 2, h // 2 + 2)]:
                pygame.draw.circle(surf, flower_rgb, (fx, fy), 3)
                pygame.draw.circle(surf, (255, 244, 160), (fx, fy), 1)
        return surf

    def _create_flower_planter(self, w, h, flower_colors):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (20, 26, 20, 90), (2, h - 8, w - 4, 8), border_radius=3)
        pygame.draw.rect(surf, (148, 94, 52), (2, 10, w - 4, h - 12), border_radius=3)
        pygame.draw.rect(surf, (182, 122, 72), (4, 12, w - 8, h - 16), border_radius=2)
        pygame.draw.rect(surf, (88, 58, 36), (6, 12, w - 12, 8))
        for x in range(8, w - 8, 8):
            pygame.draw.circle(surf, (62, 148, 56), (x + 2, 12), 6)
            pygame.draw.circle(surf, (98, 182, 76), (x + 2, 10), 4)
            col = flower_colors[(x // 8) % len(flower_colors)]
            pygame.draw.circle(surf, col, (x + 2, 8), 4)
            pygame.draw.circle(surf, (255, 245, 160), (x + 2, 8), 1)
        return surf

    def _create_potted_plant(self, leaf_rgb, flower_rgb=None):
        surf = pygame.Surface((32, 36), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (18, 24, 18, 85), (6, 26, 20, 8))
        pygame.draw.polygon(surf, (186, 98, 62), [(8, 18), (24, 18), (21, 30), (11, 30)])
        pygame.draw.rect(surf, (208, 114, 74), (7, 15, 18, 4), border_radius=1)
        pygame.draw.circle(surf, (46, 118, 46), (16, 12), 8)
        pygame.draw.circle(surf, leaf_rgb, (16, 10), 6)
        if flower_rgb:
            for fx, fy in [(12, 9), (19, 8), (16, 13)]:
                pygame.draw.circle(surf, flower_rgb, (fx, fy), 3)
        return surf

    def _create_lilypad(self):
        surf = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(surf, (48, 138, 58), (12, 13), 8)
        pygame.draw.circle(surf, (86, 178, 76), (12, 12), 7)
        pygame.draw.polygon(surf, (52, 148, 226), [(12, 12), (20, 9), (20, 15)])
        pygame.draw.circle(surf, (255, 182, 212), (10, 10), 3)
        return surf

    # ------------------------------------------------------------------
    # PUBLIC PROPS, INFRASTRUCTURE & HERITAGE STRUCTURES
    # ------------------------------------------------------------------
    def _build_prop_sprites(self):
        self.anim_frames["fountain"] = []
        for f in range(4):
            surf = pygame.Surface((96, 96), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, (18, 26, 22, 100), (6, 22, 84, 70))
            pygame.draw.ellipse(surf, (142, 138, 132), (8, 18, 80, 68))
            pygame.draw.ellipse(surf, (198, 194, 186), (8, 14, 80, 64))
            pygame.draw.ellipse(surf, (224, 220, 212), (12, 16, 72, 58))
            pygame.draw.ellipse(surf, (48, 156, 236), (18, 22, 60, 46))
            r_rad = 10 + (f * 5)
            pygame.draw.ellipse(surf, (148, 218, 255), (48 - r_rad, 45 - r_rad // 2, r_rad * 2, r_rad), 2)
            pygame.draw.rect(surf, (168, 164, 156), (40, 26, 16, 24), border_radius=3)
            pygame.draw.ellipse(surf, (212, 208, 200), (32, 20, 32, 16))
            pygame.draw.ellipse(surf, (72, 178, 248), (36, 22, 24, 12))
            spout_h = 10 + (f % 2) * 3
            pygame.draw.ellipse(surf, (220, 246, 255), (43, 18 - spout_h, 10, spout_h + 6))
            for angle in range(0, 360, 60):
                rad = math.radians(angle + f * 15)
                dx = 48 + int(math.cos(rad) * (14 + (f % 2) * 3))
                dy = 34 + int(math.sin(rad) * 8)
                pygame.draw.circle(surf, (215, 245, 255), (dx, dy), 2)
            self.anim_frames["fountain"].append(surf)
        self.sprites["fountain"] = self.anim_frames["fountain"][0]

        bench = pygame.Surface((64, 32), pygame.SRCALPHA)
        pygame.draw.rect(bench, (20, 26, 20, 90), (6, 22, 52, 8), border_radius=2)
        pygame.draw.rect(bench, (92, 58, 34), (8, 18, 6, 10))
        pygame.draw.rect(bench, (92, 58, 34), (50, 18, 6, 10))
        pygame.draw.rect(bench, (168, 108, 58), (6, 14, 52, 6), border_radius=2)
        pygame.draw.rect(bench, (188, 126, 72), (6, 6, 52, 6), border_radius=2)
        pygame.draw.rect(bench, (122, 78, 44), (6, 6, 52, 6), 1, border_radius=2)
        self.sprites["bench_h"] = bench

        lamp = pygame.Surface((32, 64), pygame.SRCALPHA)
        pygame.draw.ellipse(lamp, (18, 24, 18, 90), (8, 54, 16, 8))
        pygame.draw.rect(lamp, (54, 62, 68), (12, 48, 8, 10), border_radius=2)
        pygame.draw.rect(lamp, (72, 82, 90), (14, 16, 4, 34))
        pygame.draw.rect(lamp, (54, 62, 68), (10, 8, 12, 10), border_radius=2)
        pygame.draw.rect(lamp, (255, 232, 136), (12, 10, 8, 6))
        pygame.draw.polygon(lamp, (44, 52, 58), [(8, 8), (16, 2), (24, 8)])
        self.sprites["street_lamp"] = lamp

        board = pygame.Surface((64, 56), pygame.SRCALPHA)
        pygame.draw.ellipse(board, (18, 24, 18, 90), (6, 44, 52, 10))
        pygame.draw.rect(board, (124, 78, 42), (10, 28, 6, 22))
        pygame.draw.rect(board, (124, 78, 42), (48, 28, 6, 22))
        pygame.draw.rect(board, (156, 102, 56), (6, 10, 52, 26), border_radius=3)
        pygame.draw.rect(board, (196, 146, 92), (10, 14, 44, 18))
        for nx, col in [(14, (248, 244, 228)), (26, (255, 236, 196)), (38, (236, 246, 255))]:
            pygame.draw.rect(board, col, (nx, 16, 10, 12))
            pygame.draw.circle(board, (220, 64, 64), (nx + 5, 17), 1)
        pygame.draw.polygon(board, (112, 68, 36), [(4, 12), (32, 2), (60, 12)])
        self.sprites["notice_board"] = board

        well = pygame.Surface((56, 64), pygame.SRCALPHA)
        pygame.draw.ellipse(well, (18, 24, 18, 95), (4, 44, 48, 18))
        pygame.draw.ellipse(well, (148, 144, 138), (8, 34, 40, 24))
        pygame.draw.ellipse(well, (188, 184, 176), (8, 28, 40, 22))
        pygame.draw.ellipse(well, (44, 118, 176), (14, 32, 28, 14))
        pygame.draw.rect(well, (132, 84, 46), (12, 10, 4, 26))
        pygame.draw.rect(well, (132, 84, 46), (40, 10, 4, 26))
        pygame.draw.polygon(well, (164, 88, 52), [(6, 14), (28, 2), (50, 14)])
        self.sprites["stone_well"] = well

        crate = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(crate, (20, 24, 18, 85), (4, 22, 24, 8))
        pygame.draw.rect(crate, (164, 112, 62), (4, 6, 24, 22), border_radius=2)
        pygame.draw.rect(crate, (196, 142, 84), (6, 8, 20, 18), 2)
        pygame.draw.line(crate, (138, 92, 48), (6, 8), (26, 26), 2)
        self.sprites["wooden_crate"] = crate

        barrel = pygame.Surface((28, 34), pygame.SRCALPHA)
        pygame.draw.ellipse(barrel, (20, 24, 18, 85), (2, 24, 24, 8))
        pygame.draw.rect(barrel, (148, 94, 50), (4, 6, 20, 22), border_radius=5)
        pygame.draw.ellipse(barrel, (182, 124, 72), (4, 4, 20, 8))
        pygame.draw.rect(barrel, (78, 84, 88), (4, 11, 20, 3))
        pygame.draw.rect(barrel, (78, 84, 88), (4, 20, 20, 3))
        self.sprites["barrel"] = barrel

        clay_jar = pygame.Surface((28, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(clay_jar, (20, 24, 18, 85), (4, 22, 20, 8))
        pygame.draw.ellipse(clay_jar, (172, 104, 68), (4, 10, 20, 18))
        pygame.draw.ellipse(clay_jar, (198, 126, 86), (7, 12, 12, 10))
        pygame.draw.ellipse(clay_jar, (142, 82, 52), (8, 6, 12, 6))
        self.sprites["clay_jar"] = clay_jar

        beehive = pygame.Surface((32, 36), pygame.SRCALPHA)
        pygame.draw.ellipse(beehive, (20, 24, 18, 85), (4, 26, 24, 8))
        pygame.draw.rect(beehive, (186, 134, 68), (6, 10, 20, 20), border_radius=3)
        pygame.draw.polygon(beehive, (214, 162, 86), [(4, 12), (16, 4), (28, 12)])
        pygame.draw.rect(beehive, (52, 38, 22), (13, 18, 6, 6), border_radius=2)
        self.sprites["beehive"] = beehive

        shrine = self.crop("tx_struct", 288, 0, 96, 96)
        if shrine is None:
            shrine = pygame.Surface((96, 96), pygame.SRCALPHA)
            pygame.draw.ellipse(shrine, (168, 164, 154), (8, 16, 80, 68))
            pygame.draw.ellipse(shrine, (204, 200, 190), (16, 22, 64, 54))
            pygame.draw.rect(shrine, (186, 182, 172), (34, 34, 28, 28), border_radius=4)
            for rx, ry in [(46, 18), (46, 72), (14, 45), (76, 45)]:
                pygame.draw.circle(shrine, (98, 228, 255), (rx, ry), 4)
        self.sprites["heritage_altar"] = shrine

        statue = self.crop("tx_props", 384, 160, 32, 64)
        if statue is None:
            statue = pygame.Surface((36, 64), pygame.SRCALPHA)
            pygame.draw.ellipse(statue, (18, 24, 18, 95), (4, 52, 28, 10))
            pygame.draw.rect(statue, (162, 158, 150), (6, 42, 24, 14), border_radius=2)
            pygame.draw.rect(statue, (192, 188, 180), (10, 16, 16, 28), border_radius=5)
            pygame.draw.circle(statue, (206, 202, 194), (18, 12), 7)
        self.sprites["heritage_statue"] = statue

        clothesline = pygame.Surface((96, 48), pygame.SRCALPHA)
        pygame.draw.rect(clothesline, (122, 82, 46), (6, 10, 4, 34))
        pygame.draw.rect(clothesline, (122, 82, 46), (86, 10, 4, 34))
        pygame.draw.line(clothesline, (210, 210, 210), (8, 14), (88, 14), 1)
        shirts = [(18, (244, 92, 92)), (36, (86, 176, 248)), (54, (252, 218, 78)), (70, (248, 248, 248))]
        for sx, scol in shirts:
            pygame.draw.rect(clothesline, scol, (sx, 15, 12, 14), border_radius=1)
        self.sprites["clothesline"] = clothesline

        pole = pygame.Surface((32, 80), pygame.SRCALPHA)
        pygame.draw.ellipse(pole, (18, 24, 18, 85), (8, 68, 16, 8))
        pygame.draw.rect(pole, (108, 82, 56), (13, 8, 6, 66))
        pygame.draw.rect(pole, (92, 68, 46), (4, 14, 24, 4))
        pygame.draw.rect(pole, (92, 68, 46), (6, 24, 20, 3))
        self.sprites["utility_pole"] = pole

        fence_h = pygame.Surface((32, 24), pygame.SRCALPHA)
        pygame.draw.rect(fence_h, (132, 84, 44), (4, 4, 6, 18), border_radius=1)
        pygame.draw.rect(fence_h, (132, 84, 44), (22, 4, 6, 18), border_radius=1)
        pygame.draw.rect(fence_h, (168, 112, 62), (0, 8, 32, 4))
        pygame.draw.rect(fence_h, (168, 112, 62), (0, 15, 32, 4))
        self.sprites["fence_h"] = fence_h

        pillar = pygame.Surface((32, 44), pygame.SRCALPHA)
        pygame.draw.rect(pillar, (156, 152, 144), (4, 10, 24, 32), border_radius=2)
        pygame.draw.rect(pillar, (196, 192, 184), (2, 4, 28, 10), border_radius=2)
        self.sprites["stone_pillar"] = pillar

        bridge = pygame.Surface((128, 80), pygame.SRCALPHA)
        pygame.draw.rect(bridge, (18, 36, 58, 95), (4, 52, 120, 22), border_radius=6)
        for bx in range(8, 120, 10):
            arch_y = int(math.sin((bx / 120.0) * math.pi) * 10)
            pygame.draw.rect(bridge, (172, 116, 64), (bx, 18 - arch_y, 9, 44))
            pygame.draw.rect(bridge, (138, 88, 46), (bx, 18 - arch_y, 9, 44), 1)
        for rx in [6, 38, 64, 90, 116]:
            arch_y = int(math.sin((rx / 120.0) * math.pi) * 10)
            pygame.draw.rect(bridge, (124, 76, 38), (rx, 8 - arch_y, 8, 16), border_radius=2)
            pygame.draw.rect(bridge, (124, 76, 38), (rx, 48 - arch_y, 8, 16), border_radius=2)
        pygame.draw.line(bridge, (194, 134, 76), (6, 14), (64, 6), 5)
        pygame.draw.line(bridge, (194, 134, 76), (64, 6), (122, 14), 5)
        pygame.draw.line(bridge, (194, 134, 76), (6, 54), (64, 46), 5)
        pygame.draw.line(bridge, (194, 134, 76), (64, 46), (122, 54), 5)
        self.sprites["arched_bridge"] = bridge

        dock = pygame.Surface((96, 64), pygame.SRCALPHA)
        for dx in range(8, 88, 10):
            pygame.draw.rect(dock, (158, 106, 58), (dx, 12, 8, 40))
        for px in [8, 44, 80]:
            pygame.draw.rect(dock, (112, 72, 38), (px, 6, 8, 52), border_radius=2)
        self.sprites["wooden_dock"] = dock

        rock = pygame.Surface((48, 36), pygame.SRCALPHA)
        pygame.draw.ellipse(rock, (18, 24, 18, 90), (4, 22, 40, 12))
        pygame.draw.ellipse(rock, (138, 134, 126), (6, 8, 36, 24))
        pygame.draw.ellipse(rock, (176, 172, 164), (10, 10, 26, 14))
        self.sprites["rock_large"] = rock

    # ------------------------------------------------------------------
    # PHILIPPINE ARCHITECTURAL VARIATIONS
    # ------------------------------------------------------------------
    def _build_philippine_architecture(self):
        self.sprites["house_teal_plaza"] = self._create_filipino_house(
            128, 128, roof_rgb=(38, 138, 146), wall_rgb=(238, 222, 192), trim_rgb=(116, 76, 44), style="plaza_gable"
        )
        self.sprites["house_terracotta_plaza"] = self._create_filipino_house(
            128, 128, roof_rgb=(198, 74, 56), wall_rgb=(242, 226, 196), trim_rgb=(122, 78, 46), style="plaza_gable"
        )
        self.sprites["house_bahay_na_bato_1"] = self._create_filipino_house(
            144, 136, roof_rgb=(164, 68, 48), wall_rgb=(228, 206, 168), trim_rgb=(98, 62, 36), style="bahay_na_bato"
        )
        self.sprites["house_bahay_na_bato_2"] = self._create_filipino_house(
            144, 136, roof_rgb=(128, 86, 54), wall_rgb=(236, 224, 198), trim_rgb=(88, 56, 34), style="bahay_na_bato"
        )
        self.sprites["house_colorful_ochre"] = self._create_filipino_house(
            112, 116, roof_rgb=(184, 92, 48), wall_rgb=(248, 214, 132), trim_rgb=(118, 74, 42), style="bungalow"
        )
        self.sprites["house_colorful_mint"] = self._create_filipino_house(
            112, 116, roof_rgb=(54, 126, 98), wall_rgb=(198, 238, 212), trim_rgb=(104, 68, 38), style="bungalow"
        )
        self.sprites["house_colorful_coral"] = self._create_filipino_house(
            112, 116, roof_rgb=(176, 62, 68), wall_rgb=(252, 206, 194), trim_rgb=(112, 68, 40), style="bungalow"
        )
        self.sprites["house_nipa_farm"] = self._create_filipino_house(
            104, 108, roof_rgb=(168, 136, 74), wall_rgb=(194, 158, 98), trim_rgb=(116, 82, 44), style="nipa_hut"
        )
        self.sprites["sari_sari_store"] = self._create_market_stall(
            96, 84, awning_cols=[(228, 64, 64), (248, 238, 220)], goods="sari_sari"
        )
        self.sprites["carinderia_stall"] = self._create_market_stall(
            104, 84, awning_cols=[(52, 138, 214), (252, 218, 78)], goods="carinderia"
        )
        self.sprites["market_stall_produce"] = self._create_market_stall(
            88, 72, awning_cols=[(48, 164, 88), (248, 244, 226)], goods="produce"
        )
        self.sprites["market_stall_drygoods"] = self._create_market_stall(
            88, 72, awning_cols=[(236, 128, 44), (248, 244, 226)], goods="drygoods"
        )
        self.sprites["municipio_palace"] = self._create_municipio_complex(256, 176)

    def _create_filipino_house(self, w, h, roof_rgb, wall_rgb, trim_rgb, style="plaza_gable"):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (16, 22, 18, 95), (8, h - 26, w - 16, 22), border_radius=6)
        wall_top = h // 2 - 4
        wall_h = h - wall_top - 10
        pygame.draw.rect(surf, (156, 148, 138), (12, h - 34, w - 24, 24), border_radius=2)
        for bx in range(16, w - 24, 14):
            pygame.draw.rect(surf, (138, 130, 120), (bx, h - 30, 10, 8), 1)
        pygame.draw.rect(surf, wall_rgb, (14, wall_top, w - 28, wall_h - 18))
        pygame.draw.rect(surf, trim_rgb, (14, wall_top, w - 28, wall_h - 18), 3)

        if style == "bahay_na_bato":
            pygame.draw.rect(surf, trim_rgb, (12, wall_top + 22, w - 24, 6))
            for wx in [24, w - 56]:
                pygame.draw.rect(surf, (86, 54, 32), (wx, wall_top + 6, 32, 18), border_radius=1)
                for cx in range(wx + 3, wx + 29, 6):
                    for cy in range(wall_top + 8, wall_top + 22, 6):
                        pygame.draw.rect(surf, (238, 244, 232), (cx, cy, 4, 4))
        else:
            for wx in [22, w - 46]:
                pygame.draw.rect(surf, (78, 52, 32), (wx, wall_top + 12, 24, 20), border_radius=2)
                pygame.draw.rect(surf, (112, 188, 238), (wx + 3, wall_top + 15, 8, 14))
                pygame.draw.rect(surf, (112, 188, 238), (wx + 13, wall_top + 15, 8, 14))
                pygame.draw.rect(surf, (142, 86, 46), (wx - 2, wall_top + 30, 28, 6))
                pygame.draw.circle(surf, (255, 192, 64), (wx + 6, wall_top + 29), 3)
                pygame.draw.circle(surf, (244, 96, 132), (wx + 18, wall_top + 29), 3)

        dx = w // 2 - 12
        dy = h - 42
        pygame.draw.rect(surf, (214, 206, 192), (dx - 4, h - 14, 32, 8), border_radius=2)
        pygame.draw.rect(surf, (112, 68, 36), (dx, dy, 24, 30), border_radius=4)
        pygame.draw.rect(surf, (148, 94, 52), (dx + 3, dy + 3, 18, 25), border_radius=3)
        pygame.draw.circle(surf, (238, 198, 74), (dx + 18, dy + 16), 2)

        roof_dark = (max(0, roof_rgb[0] - 34), max(0, roof_rgb[1] - 30), max(0, roof_rgb[2] - 26))
        roof_hi = (min(255, roof_rgb[0] + 28), min(255, roof_rgb[1] + 24), min(255, roof_rgb[2] + 20))
        pts = [(6, wall_top + 8), (w // 2, 8), (w - 6, wall_top + 8)]
        pygame.draw.polygon(surf, roof_rgb, pts)
        for rx in range(14, w - 14, 8):
            dist_center = abs(rx - w // 2)
            top_y = 8 + int((dist_center / (w // 2 - 6)) * wall_top)
            pygame.draw.line(surf, roof_dark, (rx, top_y), (rx, wall_top + 6), 2)
            pygame.draw.line(surf, roof_hi, (rx + 2, top_y + 2), (rx + 2, wall_top + 5), 1)
        pygame.draw.polygon(surf, roof_dark, pts, 3)

        if style == "plaza_gable":
            pygame.draw.rect(surf, (186, 182, 174), (w - 36, 14, 16, 22), border_radius=2)
            pygame.draw.rect(surf, (78, 72, 68), (w - 33, 16, 10, 5))
            pygame.draw.rect(surf, trim_rgb, (w // 2 - 12, wall_top - 18, 24, 16), border_radius=2)
            pygame.draw.rect(surf, (112, 188, 238), (w // 2 - 8, wall_top - 14, 16, 10))
        return surf

    def _create_market_stall(self, w, h, awning_cols, goods="produce"):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (18, 24, 18, 95), (4, h - 18, w - 8, 16), border_radius=4)
        pygame.draw.rect(surf, (124, 78, 42), (8, 18, 6, h - 24))
        pygame.draw.rect(surf, (124, 78, 42), (w - 14, 18, 6, h - 24))
        pygame.draw.rect(surf, (166, 112, 62), (6, h - 34, w - 12, 24), border_radius=2)
        pygame.draw.rect(surf, (198, 144, 86), (8, h - 36, w - 16, 10))

        if goods == "produce":
            colors = [(238, 68, 58), (252, 198, 48), (88, 184, 62), (168, 82, 188)]
            for idx, gx in enumerate(range(12, w - 18, 16)):
                pygame.draw.rect(surf, (138, 92, 48), (gx, h - 38, 14, 8))
                pygame.draw.circle(surf, colors[idx % len(colors)], (gx + 4, h - 38), 4)
                pygame.draw.circle(surf, colors[(idx + 1) % len(colors)], (gx + 10, h - 38), 4)
        elif goods == "carinderia":
            for gx in range(14, w - 22, 18):
                pygame.draw.rect(surf, (192, 198, 206), (gx, h - 40, 14, 10), border_radius=2)
                pygame.draw.rect(surf, (224, 92, 54), (gx + 2, h - 42, 10, 3))
        else:
            for gx in range(12, w - 16, 10):
                pygame.draw.rect(surf, (248, 196, 54) if (gx // 10) % 2 == 0 else (236, 78, 92), (gx, 28, 7, 12))

        stripe_w = 10
        for idx, ax in enumerate(range(4, w - 4, stripe_w)):
            col = awning_cols[idx % len(awning_cols)]
            sw = min(stripe_w, w - 4 - ax)
            pygame.draw.rect(surf, col, (ax, 6, sw, 22), border_radius=2)
            pygame.draw.circle(surf, col, (ax + sw // 2, 28), sw // 2)
        pygame.draw.rect(surf, (92, 56, 32), (4, 6, w - 8, 4))
        return surf

    def _create_municipio_complex(self, w, h):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (16, 22, 18, 105), (8, h - 28, w - 16, 24), border_radius=6)
        pygame.draw.rect(surf, (172, 168, 158), (12, h - 38, w - 24, 28), border_radius=3)
        pygame.draw.rect(surf, (244, 236, 216), (16, 52, w - 32, h - 76))
        pygame.draw.rect(surf, (198, 184, 158), (16, 52, w - 32, h - 76), 3)

        for px in range(28, w - 28, 32):
            pygame.draw.rect(surf, (252, 248, 238), (px, 56, 10, h - 84))
            pygame.draw.rect(surf, (212, 202, 182), (px, 56, 10, h - 84), 1)
            if px + 14 < w - 44:
                pygame.draw.rect(surf, (74, 118, 158), (px + 13, 72, 14, 26), border_radius=5)

        cx = w // 2
        pygame.draw.rect(surf, (118, 74, 42), (cx - 22, h - 56, 44, 42), border_radius=6)
        pygame.draw.polygon(surf, (236, 226, 204), [(cx - 56, 56), (cx, 18), (cx + 56, 56)])
        pygame.draw.polygon(surf, (184, 168, 142), [(cx - 56, 56), (cx, 18), (cx + 56, 56)], 3)
        pygame.draw.polygon(surf, (178, 68, 52), [(8, 56), (48, 24), (w - 48, 24), (w - 8, 56)])
        pygame.draw.circle(surf, (238, 196, 68), (cx, 40), 9)
        pygame.draw.circle(surf, (255, 248, 220), (cx, 40), 6)
        return surf

    def _build_animated_sprites(self):
        animal_keys = [
            "anim_chicken_brown", "anim_chicken_white", "anim_dog", "anim_dog_yellow",
            "anim_cat_orange", "anim_cat_white", "anim_cow", "anim_pig", "anim_frog",
            "anim_fish", "anim_parrot_red", "anim_parrot_blue"
        ]
        for ak in animal_keys:
            frames = []
            sheet = self.sheets.get(ak)
            if sheet is not None:
                sw, sh = sheet.get_size()
                fw, fh = 32, 32
                rows = max(1, sh // fh)
                for r in range(min(4, rows)):
                    sub = sheet.subsurface(pygame.Rect(0, r * fh, min(fw, sw), min(fh, sh))).copy()
                    frames.append(sub)
            if not frames:
                for f in range(4):
                    s = pygame.Surface((32, 32), pygame.SRCALPHA)
                    by = 14 + (f % 2) * 2
                    pygame.draw.ellipse(s, (245, 240, 225), (8, by, 16, 12))
                    pygame.draw.circle(s, (220, 64, 52), (20, by - 2), 3)
                    frames.append(s)
            self.anim_frames[ak] = frames

        wf_frames = []
        for f in range(4):
            wf = pygame.Surface((64, 96), pygame.SRCALPHA)
            wf.fill((58, 164, 242))
            for x in range(0, 64, 8):
                for y in range(0, 96, 12):
                    yy = (y + f * 6 + (x % 16)) % 96
                    pygame.draw.rect(wf, (176, 232, 255), (x + 1, yy, 5, 8), border_radius=2)
                    pygame.draw.rect(wf, (238, 252, 255), (x + 2, (yy + 4) % 96, 3, 5))
            for sx in range(6, 58, 10):
                r = 6 + ((sx + f * 3) % 4)
                pygame.draw.circle(wf, (235, 250, 255), (sx, 88), r)
            wf_frames.append(wf)
        self.anim_frames["waterfall"] = wf_frames

        sway_frames = []
        for f in range(4):
            shift = [0, 2, 0, -2][f]
            sf = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.line(sf, (52, 138, 48), (12, 22), (12 + shift, 10), 2)
            pygame.draw.line(sf, (68, 158, 58), (8, 22), (6 + shift, 13), 2)
            pygame.draw.line(sf, (68, 158, 58), (16, 22), (18 + shift, 13), 2)
            pygame.draw.circle(sf, (255, 218, 72), (12 + shift, 9), 4)
            pygame.draw.circle(sf, (255, 118, 64), (12 + shift, 9), 2)
            sway_frames.append(sf)
        self.anim_frames["swaying_flower"] = sway_frames