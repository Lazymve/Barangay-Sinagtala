from enum import IntEnum


class TerrainType(IntEnum):
    WATER = 0
    RIVERBANK = 1
    MUD = 2
    SANDY_GROUND = 3
    AGRICULTURAL_SOIL = 4
    RICE_FIELD = 5
    FOREST_GROUND = 6
    SHORT_GRASS = 7
    DENSE_GRASS = 8
    FLOWERING_GRASS = 9
    GARDEN_TERRAIN = 10
    DIRT = 11
    GRAVEL = 12
    STONE_PATHWAY = 13
    COBBLESTONE = 14
    BRICK_FLOORING = 15
    CONCRETE = 16
    WOODEN_FLOORING = 17
    ELEVATED_STONE = 18


TERRAIN_METADATA = {
    TerrainType.WATER:             {"key": "water",             "walkable": False, "border_rgb": (38, 114, 186)},
    TerrainType.RIVERBANK:         {"key": "riverbank",         "walkable": False, "border_rgb": (118, 92, 62)},
    TerrainType.MUD:               {"key": "mud",               "walkable": True,  "border_rgb": (94, 68, 46)},
    TerrainType.SANDY_GROUND:      {"key": "sandy_ground",      "walkable": True,  "border_rgb": (204, 178, 122)},
    TerrainType.AGRICULTURAL_SOIL: {"key": "agricultural_soil", "walkable": True,  "border_rgb": (88, 60, 38)},
    TerrainType.RICE_FIELD:        {"key": "rice_field",        "walkable": True,  "border_rgb": (108, 92, 58)},
    TerrainType.FOREST_GROUND:     {"key": "forest_ground",     "walkable": True,  "border_rgb": (48, 94, 38)},
    TerrainType.SHORT_GRASS:       {"key": "short_grass",       "walkable": True,  "border_rgb": (78, 144, 54)},
    TerrainType.DENSE_GRASS:       {"key": "dense_grass",       "walkable": True,  "border_rgb": (62, 126, 44)},
    TerrainType.FLOWERING_GRASS:   {"key": "flowering_grass",   "walkable": True,  "border_rgb": (84, 152, 58)},
    TerrainType.GARDEN_TERRAIN:    {"key": "garden_terrain",    "walkable": True,  "border_rgb": (96, 68, 42)},
    TerrainType.DIRT:              {"key": "dirt",              "walkable": True,  "border_rgb": (148, 112, 74)},
    TerrainType.GRAVEL:            {"key": "gravel",            "walkable": True,  "border_rgb": (128, 124, 116)},
    TerrainType.STONE_PATHWAY:     {"key": "stone_pathway",     "walkable": True,  "border_rgb": (166, 186, 128)},
    TerrainType.COBBLESTONE:       {"key": "cobblestone",       "walkable": True,  "border_rgb": (128, 124, 116)},
    TerrainType.BRICK_FLOORING:    {"key": "brick_flooring",    "walkable": True,  "border_rgb": (148, 82, 62)},
    TerrainType.CONCRETE:          {"key": "concrete",          "walkable": True,  "border_rgb": (164, 162, 156)},
    TerrainType.WOODEN_FLOORING:   {"key": "wooden_flooring",   "walkable": True,  "border_rgb": (118, 78, 42)},
    TerrainType.ELEVATED_STONE:    {"key": "elevated_stone",    "walkable": True,  "border_rgb": (176, 172, 162)},
}
