"""
World Map data and collision helpers for Barangay Sinagtala 3D.
Grid cells:
  0 = Empty / Walkable floor
  1 = Spanish-colonial stone wall (Pared de Piedra)
  2 = Terracotta brick wall (Ladrillo)
  3 = Weathered timber wall (Kahoy)
  4 = White plaster wall (Plaster colonial)
"""

WORLD_MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 2, 2, 2, 0, 0, 0, 3, 3, 3, 0, 0, 0, 1],
    [1, 0, 0, 2, 0, 2, 0, 0, 0, 3, 0, 3, 0, 0, 0, 1],
    [1, 0, 0, 2, 0, 2, 0, 0, 0, 3, 0, 3, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 4, 4, 4, 4, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 4, 0, 0, 4, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

MAP_ROWS = len(WORLD_MAP)
MAP_COLS = len(WORLD_MAP[0])

# Starting player position in map grid coordinates
PLAYER_START_X = 2.5
PLAYER_START_Y = 2.5
PLAYER_START_ANGLE = 0.0  # Facing East (towards the walls)


def get_tile(map_x: int, map_y: int) -> int:
    """Returns the tile ID at integer map coordinates."""
    if 0 <= map_x < MAP_COLS and 0 <= map_y < MAP_ROWS:
        return WORLD_MAP[map_y][map_x]
    return 1  # Out of bounds treated as solid wall


def is_wall(x: float, y: float) -> bool:
    """Checks whether the given continuous world coordinates hit a solid wall."""
    map_x = int(x)
    map_y = int(y)
    return get_tile(map_x, map_y) > 0
