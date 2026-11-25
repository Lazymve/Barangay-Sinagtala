import os
import json
import math
import random
from terrain import TerrainType
from tilemap import TileMap, TILE_SIZE
from environment import EnvironmentManager
from animation import AnimationManager

MAP_COLS = 160
MAP_ROWS = 120
CUSTOM_SAVE_FILE = "custom_objects.json"


class BarangaySinagtalaMap:
    """
    Master builder for Barangay Sinagtala (160x120 tiles / 5120x3840 pixels).
    Includes organic multi-grass biome noise and automatic JSON persistence
    for user-placed trees and objects.
    """

    DISTRICT_LANDMARKS = {
        "1": ("CENTRAL TOWN PLAZA",          74 * TILE_SIZE,  58 * TILE_SIZE),
        "2": ("PUBLIC MARKET (PALENGKE)",   132 * TILE_SIZE,  36 * TILE_SIZE),
        "3": ("RESIDENTIAL NEIGHBORHOOD",    82 * TILE_SIZE,  98 * TILE_SIZE),
        "4": ("RIVERSIDE COUNTRYSIDE",       24 * TILE_SIZE,  60 * TILE_SIZE),
        "5": ("AGRICULTURAL DISTRICT",      134 * TILE_SIZE,  92 * TILE_SIZE),
        "6": ("HERITAGE DISTRICT",           28 * TILE_SIZE, 102 * TILE_SIZE),
        "7": ("FOREST & GARDEN EDGE",        26 * TILE_SIZE,  20 * TILE_SIZE),
        "8": ("MUNICIPAL & PALACE DISTRICT", 84 * TILE_SIZE,  20 * TILE_SIZE),
    }

    def __init__(self, asset_loader):
        self.assets = asset_loader
        self.tilemap = TileMap(MAP_COLS, MAP_ROWS, asset_loader)
        self.env = EnvironmentManager(asset_loader)
        self.anim = AnimationManager(asset_loader, MAP_COLS * TILE_SIZE, MAP_ROWS * TILE_SIZE)
        self.custom_objects = []
        self._build_world()

    def get_district_at(self, wx, wy):
        tx, ty = int(wx // TILE_SIZE), int(wy // TILE_SIZE)
        if ty < 39:
            if tx < 55:
                return "FOREST & GARDEN EDGE"
            elif tx < 115:
                return "MUNICIPAL & PALACE DISTRICT"
            else:
                return "PUBLIC MARKET (PALENGKE)"
        elif ty < 79:
            if tx < 45:
                return "RIVERSIDE COUNTRYSIDE"
            elif tx < 105:
                return "CENTRAL TOWN PLAZA"
            else:
                return "PUBLIC MARKET (PALENGKE)"
        else:
            if tx < 55:
                return "HERITAGE DISTRICT"
            elif tx < 110:
                return "RESIDENTIAL NEIGHBORHOOD"
            else:
                return "AGRICULTURAL DISTRICT"

    def _build_world(self):
        self._stage3_terrain()
        self._stage4_environment()
        self._load_custom_objects()
        self._stage6_animations()
        self.tilemap.bake_chunks()
        self.env.finalize_sorting()

    def save_custom_object(self, x, y, sprite_key, light_source=False):
        """Saves a newly placed object to custom_objects.json so it persists after closing."""
        entry = {"x": int(x), "y": int(y), "key": sprite_key, "light": bool(light_source)}
        self.custom_objects.append(entry)
        try:
            with open(CUSTOM_SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.custom_objects, f, indent=2)
        except Exception as e:
            print(f"[Save Notice] {e}")

    def remove_last_custom_object(self):
        if self.custom_objects:
            self.custom_objects.pop()
            try:
                with open(CUSTOM_SAVE_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.custom_objects, f, indent=2)
            except Exception as e:
                print(f"[Save Notice] {e}")

    def _load_custom_objects(self):
        if os.path.isfile(CUSTOM_SAVE_FILE):
            try:
                with open(CUSTOM_SAVE_FILE, "r", encoding="utf-8") as f:
                    self.custom_objects = json.load(f)
                for obj in self.custom_objects:
                    self.env.add_object(obj["x"], obj["y"], obj["key"], light_source=obj.get("light", False))
                print(f"[Loaded] Restored {len(self.custom_objects)} saved objects from {CUSTOM_SAVE_FILE}.")
            except Exception as e:
                print(f"[Load Notice] {e}")

    def add_tree_grove(self, start_col, start_row, width_cols, height_rows, tree_keys, density=0.45, seed=42):
        rng = random.Random(seed)
        for r in range(start_row, start_row + height_rows, 3):
            for c in range(start_col, start_col + width_cols, 3):
                t_type = self.tilemap.base_grid[min(r, MAP_ROWS - 1)][min(c, MAP_COLS - 1)]
                if int(t_type) in (0, 13, 14, 15, 16, 17):
                    continue
                if rng.random() < density:
                    px = c * TILE_SIZE + rng.randint(-10, 10)
                    py = r * TILE_SIZE + rng.randint(-10, 10)
                    tkey = rng.choice(tree_keys)
                    self.env.add_object(px, py, tkey)
                    if rng.random() < 0.45:
                        sub_key = rng.choice(["bush_flowering", "bush_round", "rock_large"])
                        self.env.add_object(px + rng.randint(-16, 24), py + rng.randint(18, 36), sub_key)

    def add_prop_line(self, start_col, start_row, count, step_col, step_row, sprite_key, light_source=False):
        for i in range(count):
            cx = (start_col + i * step_col) * TILE_SIZE
            cy = (start_row + i * step_row) * TILE_SIZE
            self.env.add_object(cx, cy, sprite_key, light_source=light_source)

    # ------------------------------------------------------------------
    # STAGE 3: ORGANIC MULTI-GRASS TERRAIN & BIOME CONSTRUCTION
    # ------------------------------------------------------------------
    def _stage3_terrain(self):
        tm = self.tilemap

        # 1. Organic Multi-Grass Base (Blends Short Grass, Dense Grass, and Flowering Grass naturally)
        for ty in range(MAP_ROWS):
            for tx in range(MAP_COLS):
                n1 = math.sin(tx * 0.14 + ty * 0.09) + math.cos(tx * 0.08 - ty * 0.16)
                n2 = math.sin(tx * 0.31 - ty * 0.27) * 0.5
                h = ((tx * 374761393 + ty * 668265263) ^ 0x5BF03635) & 0xFF
                score = n1 + n2 + (h / 255.0) * 0.8

                if score > 1.35:
                    tm.set_terrain(tx, ty, TerrainType.FLOWERING_GRASS)
                elif score > 0.45:
                    tm.set_terrain(tx, ty, TerrainType.DENSE_GRASS)
                else:
                    tm.set_terrain(tx, ty, TerrainType.SHORT_GRASS)

        # 2. Area G: Forest & Garden Edge (Rich mossy floor + wildflower clearings)
        for ty in range(0, 39):
            for tx in range(0, 55):
                w = math.sin(tx * 0.18) * math.cos(ty * 0.18)
                if w > 0.35:
                    tm.set_terrain(tx, ty, TerrainType.FLOWERING_GRASS)
                elif w > -0.2:
                    tm.set_terrain(tx, ty, TerrainType.FOREST_GROUND)
                else:
                    tm.set_terrain(tx, ty, TerrainType.DENSE_GRASS)
        tm.fill_ellipse(26, 18, 11, 7, TerrainType.FLOWERING_GRASS)

        # 3. Area H: Municipal & Palace District formal grounds
        tm.fill_rect(64, 4, 40, 28, TerrainType.STONE_PATHWAY)
        tm.fill_rect(68, 18, 12, 10, TerrainType.GARDEN_TERRAIN)
        tm.fill_rect(88, 18, 12, 10, TerrainType.GARDEN_TERRAIN)
        tm.fill_rect(72, 6, 24, 10, TerrainType.BRICK_FLOORING)

        # 4. Area A: Central Town Plaza (Reference Image 2 Layout)
        tm.fill_rect(56, 46, 36, 24, TerrainType.STONE_PATHWAY)
        tm.fill_ellipse(74, 58, 18, 12, TerrainType.STONE_PATHWAY)
        tm.fill_ellipse(74, 58, 6, 5, TerrainType.COBBLESTONE)
        tm.fill_rect(71, 30, 6, 60, TerrainType.STONE_PATHWAY)
        tm.fill_rect(32, 55, 86, 6, TerrainType.STONE_PATHWAY)
        tm.fill_rect(54, 44, 40, 2, TerrainType.CONCRETE)
        tm.fill_rect(54, 70, 40, 2, TerrainType.CONCRETE)
        tm.fill_rect(84, 47, 10, 6, TerrainType.GARDEN_TERRAIN)
        tm.fill_rect(56, 47, 8, 5, TerrainType.FLOWERING_GRASS)
        tm.fill_rect(56, 64, 8, 5, TerrainType.FLOWERING_GRASS)
        tm.fill_rect(84, 64, 10, 5, TerrainType.FLOWERING_GRASS)

        # 5. Area B: Public Market (Palengke)
        tm.fill_rect(108, 14, 46, 48, TerrainType.COBBLESTONE)
        tm.fill_rect(112, 20, 38, 6, TerrainType.CONCRETE)
        tm.fill_rect(112, 34, 38, 6, TerrainType.STONE_PATHWAY)
        tm.fill_rect(112, 48, 38, 6, TerrainType.BRICK_FLOORING)
        tm.fill_rect(128, 14, 6, 48, TerrainType.STONE_PATHWAY)

        # 6. Area C: Residential Neighborhood (Lush mixed lawns & gardens)
        tm.fill_rect(60, 86, 46, 4, TerrainType.CONCRETE)
        tm.fill_rect(60, 104, 46, 4, TerrainType.CONCRETE)
        tm.fill_rect(80, 78, 5, 38, TerrainType.STONE_PATHWAY)
        for gx in [62, 74, 88, 98]:
            tm.fill_rect(gx, 81, 6, 4, TerrainType.GARDEN_TERRAIN)
            tm.fill_rect(gx, 98, 6, 4, TerrainType.FLOWERING_GRASS)

        # 7. Area E: Agricultural District (Central Luzon Rice Paddies & Irrigation)
        tm.fill_rect(110, 65, 50, 55, TerrainType.DIRT)
        tm.fill_rect(114, 70, 42, 3, TerrainType.MUD)
        tm.fill_rect(114, 71, 42, 1, TerrainType.WATER)
        tm.fill_rect(114, 94, 42, 3, TerrainType.MUD)
        tm.fill_rect(114, 95, 42, 1, TerrainType.WATER)
        tm.fill_rect(115, 75, 18, 16, TerrainType.RICE_FIELD)
        tm.fill_rect(136, 75, 18, 16, TerrainType.RICE_FIELD)
        tm.fill_rect(115, 99, 18, 14, TerrainType.RICE_FIELD)
        tm.fill_rect(136, 99, 18, 14, TerrainType.AGRICULTURAL_SOIL)

        # 8. Area F: Heritage District (Reference Image 1 Elevated Stone Terraces & Scattered Pavers)
        tm.fill_rect(12, 88, 32, 12, TerrainType.ELEVATED_STONE)
        for tx in range(12, 44):
            tm.set_detail(tx, 100, "cliff_wall_face")
        for stx in range(26, 30):
            tm.set_detail(stx, 100, "stone_stairs")
        for py in range(102, 114):
            for px in range(10, 46):
                if ((px * 19 + py * 31) % 5) in (0, 1) or abs(py - 107) <= 1 or abs(px - 28) <= 1:
                    tm.set_terrain(px, py, TerrainType.STONE_PATHWAY)

        # 9. Area D: Winding Sinagtala River, Sandy Shorelines, Waterfall Pond & Bridges
        tm.fill_ellipse(24, 42, 9, 6, TerrainType.WATER)
        for ry in range(0, MAP_ROWS):
            rcx = int(24 + 6 * math.sin(ry * 0.09))
            for dx in range(-6, 7):
                tx = rcx + dx
                if 0 <= tx < MAP_COLS:
                    if abs(dx) <= 3:
                        tm.set_terrain(tx, ry, TerrainType.WATER)
                    elif abs(dx) == 4:
                        tm.set_terrain(tx, ry, TerrainType.SANDY_GROUND)
                    elif abs(dx) == 5:
                        tm.set_terrain(tx, ry, TerrainType.GRAVEL)

        for by in range(56, 59):
            for bx in range(21, 31):
                tm.set_terrain(bx, by, TerrainType.WOODEN_FLOORING)
        for by in range(24, 27):
            for bx in range(16, 26):
                tm.set_terrain(bx, by, TerrainType.WOODEN_FLOORING)
        for by in range(96, 99):
            for bx in range(22, 32):
                tm.set_terrain(bx, by, TerrainType.WOODEN_FLOORING)

        tm.fill_rect(25, 24, 40, 3, TerrainType.DIRT)
        tm.fill_rect(30, 96, 32, 3, TerrainType.COBBLESTONE)

    # ------------------------------------------------------------------
    # STAGE 4: ENVIRONMENT CONSTRUCTION
    # ------------------------------------------------------------------
    def _stage4_environment(self):
        env = self.env

        # Lush Groves along Riverside, Forest Edge, and Plaza Borders
        self.add_tree_grove(
            start_col=4, start_row=32, width_cols=16, height_rows=20,
            tree_keys=["tree_coconut", "tree_mango", "tree_banana", "tree_caballero_pink"],
            density=0.60, seed=101
        )
        self.add_tree_grove(
            start_col=36, start_row=36, width_cols=16, height_rows=16,
            tree_keys=["tree_acacia_large", "tree_mango", "tree_caballero_pink"],
            density=0.50, seed=202
        )

        # North-South Avenue Lamps & Planters
        self.add_prop_line(
            start_col=70, start_row=32, count=6, step_col=0, step_row=2,
            sprite_key="street_lamp", light_source=True
        )
        self.add_prop_line(
            start_col=77, start_row=32, count=6, step_col=0, step_row=2,
            sprite_key="flower_bed_box"
        )

        # --- AREA A: CENTRAL TOWN PLAZA ---
        env.add_object(73 * TILE_SIZE - 16, 57 * TILE_SIZE - 16, "fountain")
        env.add_object(62 * TILE_SIZE, 40 * TILE_SIZE, "house_teal_plaza")
        env.add_object(80 * TILE_SIZE, 40 * TILE_SIZE, "house_terracotta_plaza")
        env.add_object(52 * TILE_SIZE, 49 * TILE_SIZE, "sari_sari_store")
        env.add_object(94 * TILE_SIZE, 49 * TILE_SIZE, "carinderia_stall")
        env.add_object(81 * TILE_SIZE, 60 * TILE_SIZE, "notice_board")
        env.add_object(95 * TILE_SIZE, 47 * TILE_SIZE, "stone_well")

        for bx, by in [(64, 52), (82, 52), (64, 63), (82, 63), (48, 54)]:
            env.add_object(bx * TILE_SIZE, by * TILE_SIZE, "bench_h")
        for lx, ly in [(69, 44), (78, 44), (60, 54), (88, 54), (69, 66), (78, 66)]:
            env.add_object(lx * TILE_SIZE, ly * TILE_SIZE, "street_lamp", light_source=True)
        for fx, fy in [(62, 46), (79, 46), (62, 66), (79, 66), (85, 65)]:
            env.add_object(fx * TILE_SIZE, fy * TILE_SIZE, "flower_bed_box")
        for hx in [85, 87, 89]:
            env.add_object(hx * TILE_SIZE, 62 * TILE_SIZE, "beehive")
        env.add_object(58 * TILE_SIZE, 58 * TILE_SIZE, "wooden_crate")
        env.add_object(59 * TILE_SIZE, 58 * TILE_SIZE + 8, "barrel")
        env.add_object(57 * TILE_SIZE + 12, 59 * TILE_SIZE, "potted_bougainvillea")
        env.add_object(79 * TILE_SIZE, 61 * TILE_SIZE, "potted_fern")

        for tx, ty, tkey in [
            (55, 39, "tree_acacia_large"), (75, 39, "tree_caballero_pink"), (92, 39, "tree_mango"),
            (84, 57, "tree_pine_tropical"), (90, 56, "tree_mango"), (54, 62, "tree_pine_tropical"),
            (65, 67, "tree_acacia_large"), (88, 67, "tree_caballero_pink"),
        ]:
            env.add_object(tx * TILE_SIZE, ty * TILE_SIZE, tkey)

        # --- AREA B: PUBLIC MARKET (PALENGKE) ---
        stall_layout = [
            (113, 16, "market_stall_produce"),  (121, 16, "market_stall_drygoods"),
            (135, 16, "sari_sari_store"),       (144, 16, "market_stall_produce"),
            (113, 28, "carinderia_stall"),      (122, 28, "market_stall_produce"),
            (135, 28, "market_stall_drygoods"), (144, 28, "carinderia_stall"),
            (113, 41, "sari_sari_store"),       (122, 41, "market_stall_produce"),
            (135, 41, "market_stall_produce"),  (144, 41, "market_stall_drygoods"),
        ]
        for sx, sy, skey in stall_layout:
            env.add_object(sx * TILE_SIZE, sy * TILE_SIZE, skey)
            env.add_object((sx + 3) * TILE_SIZE, (sy + 1) * TILE_SIZE, "wooden_crate")
            env.add_object((sx - 1) * TILE_SIZE, (sy + 2) * TILE_SIZE, "barrel")
        for lx in [111, 127, 134, 150]:
            for ly in [19, 33, 47]:
                env.add_object(lx * TILE_SIZE, ly * TILE_SIZE, "street_lamp", light_source=True)

        # --- AREA C: RESIDENTIAL NEIGHBORHOOD ---
        homes = [
            (60, 79, "house_colorful_ochre"),   (72, 79, "house_colorful_mint"),
            (86, 79, "house_bahay_na_bato_1"),  (98, 79, "house_colorful_coral"),
            (60, 96, "house_bahay_na_bato_2"),  (72, 96, "house_teal_plaza"),
            (86, 96, "house_terracotta_plaza"), (98, 96, "house_colorful_ochre"),
        ]
        for hx, hy, hkey in homes:
            env.add_object(hx * TILE_SIZE, hy * TILE_SIZE, hkey)
            env.add_object((hx + 4) * TILE_SIZE, (hy + 2) * TILE_SIZE, "potted_bougainvillea")
            env.add_object((hx - 2) * TILE_SIZE, (hy + 1) * TILE_SIZE, "tree_coconut")
        env.add_object(66 * TILE_SIZE, 91 * TILE_SIZE, "clothesline")
        env.add_object(92 * TILE_SIZE, 91 * TILE_SIZE, "clothesline")
        for fx in range(58, 106, 2):
            if fx not in range(79, 86):
                env.add_object(fx * TILE_SIZE, 85 * TILE_SIZE, "fence_h")
                env.add_object(fx * TILE_SIZE, 103 * TILE_SIZE, "fence_h")

        pole_coords = [(58, 86), (70, 86), (84, 86), (98, 86), (56, 54), (70, 54), (88, 54), (104, 54)]
        for px, py in pole_coords:
            env.add_object(px * TILE_SIZE, (py - 2) * TILE_SIZE, "utility_pole")
        for i in range(3):
            env.add_wire_span(
                pole_coords[i][0] * TILE_SIZE + 16, (pole_coords[i][1] - 2) * TILE_SIZE + 16,
                pole_coords[i + 1][0] * TILE_SIZE + 16, (pole_coords[i + 1][1] - 2) * TILE_SIZE + 16
            )
            env.add_wire_span(
                pole_coords[i + 4][0] * TILE_SIZE + 16, (pole_coords[i + 4][1] - 2) * TILE_SIZE + 16,
                pole_coords[i + 5][0] * TILE_SIZE + 16, (pole_coords[i + 5][1] - 2) * TILE_SIZE + 16
            )

        # --- AREA D: RIVERSIDE COUNTRYSIDE ---
        env.add_object(21 * TILE_SIZE, 55 * TILE_SIZE, "arched_bridge", layer="ground")
        env.add_object(16 * TILE_SIZE, 23 * TILE_SIZE, "arched_bridge", layer="ground")
        env.add_object(22 * TILE_SIZE, 95 * TILE_SIZE, "arched_bridge", layer="ground")
        env.add_object(28 * TILE_SIZE, 48 * TILE_SIZE, "wooden_dock", layer="ground")
        env.add_object(28 * TILE_SIZE, 70 * TILE_SIZE, "wooden_dock", layer="ground")

        for lx, ly in [(23, 44), (25, 50), (27, 63), (24, 72), (26, 80)]:
            env.add_object(lx * TILE_SIZE, ly * TILE_SIZE, "lilypad", layer="ground")
        for cx, cy in [(12, 42), (14, 52), (34, 46), (36, 62), (14, 68), (34, 76), (16, 80)]:
            env.add_object(cx * TILE_SIZE, cy * TILE_SIZE, "tree_coconut")
            env.add_object((cx + 2) * TILE_SIZE, (cy + 2) * TILE_SIZE, "tree_banana")
            env.add_object((cx - 1) * TILE_SIZE, (cy + 3) * TILE_SIZE, "rock_large")

        # --- AREA E: AGRICULTURAL DISTRICT ---
        env.add_object(116 * TILE_SIZE, 64 * TILE_SIZE, "house_nipa_farm")
        env.add_object(142 * TILE_SIZE, 64 * TILE_SIZE, "house_nipa_farm")
        env.add_object(146 * TILE_SIZE, 90 * TILE_SIZE, "house_nipa_farm")
        for fx in range(114, 154, 3):
            env.add_object(fx * TILE_SIZE, 73 * TILE_SIZE, "fence_h")
        for cx, cy in [(112, 68), (134, 68), (154, 74), (112, 96), (154, 98)]:
            env.add_object(cx * TILE_SIZE, cy * TILE_SIZE, "tree_coconut")
            env.add_object((cx + 1) * TILE_SIZE, (cy + 2) * TILE_SIZE, "tree_banana")

        # --- AREA F: HERITAGE DISTRICT ---
        env.add_object(26 * TILE_SIZE + 16, 89 * TILE_SIZE, "heritage_altar")
        env.add_object(10 * TILE_SIZE, 86 * TILE_SIZE, "house_bahay_na_bato_1")
        env.add_object(38 * TILE_SIZE, 86 * TILE_SIZE, "house_bahay_na_bato_2")
        env.add_object(11 * TILE_SIZE, 103 * TILE_SIZE, "heritage_statue")
        env.add_object(43 * TILE_SIZE, 103 * TILE_SIZE, "heritage_statue")
        for px, py in [(12, 99), (24, 99), (31, 99), (43, 99), (16, 112), (38, 112)]:
            env.add_object(px * TILE_SIZE, py * TILE_SIZE, "stone_pillar")
            env.add_object((px + 1) * TILE_SIZE, (py + 1) * TILE_SIZE, "clay_jar")
        for tx, ty in [(15, 92), (36, 92), (8, 106), (45, 106)]:
            env.add_object(tx * TILE_SIZE, ty * TILE_SIZE, "tree_narra_gold")
            env.add_object((tx + 2) * TILE_SIZE, (ty + 3) * TILE_SIZE, "rock_large")
        for lx in [20, 35]:
            env.add_object(lx * TILE_SIZE, 104 * TILE_SIZE, "street_lamp", light_source=True)

        # --- AREA G: FOREST & GARDEN EDGE ---
        for row in range(4, 34, 5):
            for col in range(4, 50, 6):
                if (col in range(20, 32) and row in range(14, 26)):
                    continue
                tkey = ["tree_acacia_large", "tree_mango", "tree_pine_tropical", "tree_caballero_pink"][(row + col) % 4]
                env.add_object(col * TILE_SIZE, row * TILE_SIZE, tkey)
                if (row + col) % 2 == 0:
                    env.add_object((col + 2) * TILE_SIZE, (row + 3) * TILE_SIZE, "bush_flowering")
        env.add_object(25 * TILE_SIZE, 16 * TILE_SIZE, "heritage_statue")

        # --- AREA H: MUNICIPAL & PALACE DISTRICT ---
        env.add_object(76 * TILE_SIZE, 4 * TILE_SIZE, "municipio_palace")
        env.add_object(69 * TILE_SIZE, 19 * TILE_SIZE, "fountain")
        env.add_object(89 * TILE_SIZE, 19 * TILE_SIZE, "fountain")
        for gx in [66, 74, 86, 94]:
            env.add_object(gx * TILE_SIZE, 28 * TILE_SIZE, "flower_bed_box")
            env.add_object(gx * TILE_SIZE, 31 * TILE_SIZE, "stone_pillar")
            env.add_object((gx + 1) * TILE_SIZE, 26 * TILE_SIZE, "street_lamp", light_source=True)
        for tx in [60, 102]:
            for ty in [8, 18, 28]:
                env.add_object(tx * TILE_SIZE, ty * TILE_SIZE, "tree_acacia_large")

    # ------------------------------------------------------------------
    # STAGE 6: LIVE ENVIRONMENTAL ANIMATIONS
    # ------------------------------------------------------------------
    def _stage6_animations(self):
        self.anim.add_node(23 * TILE_SIZE, 37 * TILE_SIZE, "waterfall", fps=8.0, layer="ground")
        self.anim.add_node(73 * TILE_SIZE - 16, 57 * TILE_SIZE - 16, "fountain", fps=5.0, layer="mid")
        self.anim.add_node(69 * TILE_SIZE, 19 * TILE_SIZE, "fountain", fps=5.0, phase=1.2, layer="mid")
        self.anim.add_node(89 * TILE_SIZE, 19 * TILE_SIZE, "fountain", fps=5.0, phase=2.4, layer="mid")

        for i in range(95):
            fx = ((i * 19 + 11) % (MAP_COLS - 10)) + 5
            fy = ((i * 29 + 7) % (MAP_ROWS - 10)) + 5
            if self.tilemap.base_grid[fy][fx] in (
                TerrainType.SHORT_GRASS, TerrainType.FLOWERING_GRASS, TerrainType.GARDEN_TERRAIN, TerrainType.DENSE_GRASS
            ):
                self.anim.add_node(fx * TILE_SIZE, fy * TILE_SIZE, "swaying_flower", fps=4.0, phase=i * 0.4, layer="ground")

        fauna_spawns = [
            (66, 88, "anim_chicken_brown", 28), (70, 90, "anim_chicken_white", 24),
            (92, 88, "anim_dog", 42),           (76, 61, "anim_dog_yellow", 36),
            (63, 45, "anim_cat_orange", 16),    (118, 24, "anim_cat_white", 18),
            (122, 80, "anim_cow", 32),          (142, 82, "anim_cow", 30),
            (126, 104, "anim_pig", 24),         (24, 48, "anim_fish", 20),
            (25, 66, "anim_frog", 14),          (28, 18, "anim_parrot_red", 48),
            (34, 22, "anim_parrot_blue", 48),
        ]
        for fx, fy, akey, rad in fauna_spawns:
            self.anim.add_node(fx * TILE_SIZE, fy * TILE_SIZE, akey, fps=5.5, phase=fx * 0.3, layer="mid", patrol_radius=rad)