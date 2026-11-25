"""
3D Urban Environment and Collision System for Barangay Sinagtala 3D.
Constructs a GTA III / IV inspired Liberty City district with multi-story buildings,
intersections, roads, raised sidewalks, streetlamps, rooftop props, and AABB physics collision.
"""

import math
from OpenGL.GL import *
from OpenGL.GLU import *


class AABB:
    """Axis-Aligned Bounding Box for 3D physics collision and camera spring-arm raycasts."""
    __slots__ = ("min_x", "min_y", "min_z", "max_x", "max_y", "max_z")

    def __init__(self, min_x, min_y, min_z, max_x, max_y, max_z):
        self.min_x = float(min_x)
        self.min_y = float(min_y)
        self.min_z = float(min_z)
        self.max_x = float(max_x)
        self.max_y = float(max_y)
        self.max_z = float(max_z)

    def intersects_circle_2d(self, cx: float, cy: float, radius: float) -> bool:
        closest_x = max(self.min_x, min(cx, self.max_x))
        closest_y = max(self.min_y, min(cy, self.max_y))
        dist_sq = (cx - closest_x) ** 2 + (cy - closest_y) ** 2
        return dist_sq < (radius * radius)

    def ray_intersect(self, p0, p1) -> float:
        """
        Calculates line segment intersection t in [0, 1] using slab method.
        Returns closest t or 1.0 if no hit.
        """
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        dz = p1[2] - p0[2]

        tmin = 0.0
        tmax = 1.0

        for p_start, d, b_min, b_max in [
            (p0[0], dx, self.min_x, self.max_x),
            (p0[1], dy, self.min_y, self.max_y),
            (p0[2], dz, self.min_z, self.max_z),
        ]:
            if abs(d) < 1e-7:
                if p_start < b_min or p_start > b_max:
                    return 1.0
            else:
                ood = 1.0 / d
                t1 = (b_min - p_start) * ood
                t2 = (b_max - p_start) * ood
                if t1 > t2:
                    t1, t2 = t2, t1
                tmin = max(tmin, t1)
                tmax = min(tmax, t2)
                if tmin > tmax:
                    return 1.0

        return tmin if tmin >= 0.0 else 1.0


class Building:
    def __init__(self, x, y, width, depth, height, style="brick"):
        self.x = x
        self.y = y
        self.width = width
        self.depth = depth
        self.height = height
        self.style = style  # "brick" or "tower"
        self.aabb = AABB(x, y, 0.0, x + width, y + depth, height)


class StreetLamp:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.height = 4.2


class CityEnvironment:
    """
    Manages the 3D urban map layout, display lists, materials,
    street networks, and collision detection.
    """

    def __init__(self):
        self.city_size = 80.0
        self.buildings = []
        self.colliders = []
        self.street_lamps = []
        self.display_list = 0
        self._build_city_layout()

    def _build_city_layout(self):
        # 1. City Blocks with varied building heights and styles
        blocks = [
            # Block 1 (North-West)
            (Building(8, 8, 12, 10, 9.0, "brick")),
            (Building(22, 8, 10, 10, 15.0, "tower")),
            (Building(8, 20, 10, 12, 11.5, "brick")),
            (Building(20, 20, 12, 12, 18.0, "tower")),

            # Block 2 (North-East)
            (Building(46, 8, 14, 10, 14.0, "tower")),
            (Building(62, 8, 10, 10, 7.5, "brick")),
            (Building(46, 20, 10, 12, 8.5, "brick")),
            (Building(58, 20, 14, 12, 16.5, "tower")),

            # Block 3 (South-West)
            (Building(8, 46, 11, 12, 10.0, "brick")),
            (Building(21, 46, 11, 12, 13.0, "tower")),
            (Building(8, 60, 12, 10, 7.0, "brick")),
            (Building(22, 60, 10, 10, 11.0, "brick")),

            # Block 4 (South-East)
            (Building(46, 46, 12, 12, 12.0, "tower")),
            (Building(60, 46, 12, 12, 17.5, "tower")),
            (Building(46, 60, 14, 10, 8.0, "brick")),
            (Building(62, 60, 10, 10, 9.5, "brick")),

            # Perimeter Boundary Wall Buildings (keeps player inside play area)
            (Building(0, 0, 80, 4, 12.0, "brick")),
            (Building(0, 76, 80, 4, 12.0, "brick")),
            (Building(0, 0, 4, 80, 12.0, "brick")),
            (Building(76, 0, 4, 80, 12.0, "brick")),
        ]
        self.buildings.extend(blocks)
        for b in self.buildings:
            self.colliders.append(b.aabb)

        # 2. Street Lamps along Central Avenue (X = 38-42) and Cross Streets (Y = 38-42)
        lamp_positions = [
            (35.5, 12.0), (44.5, 12.0),
            (35.5, 26.0), (44.5, 26.0),
            (35.5, 52.0), (44.5, 52.0),
            (35.5, 66.0), (44.5, 66.0),
            (14.0, 35.5), (26.0, 35.5),
            (52.0, 35.5), (64.0, 35.5),
            (14.0, 44.5), (26.0, 44.5),
            (52.0, 44.5), (64.0, 44.5),
        ]
        for lx, ly in lamp_positions:
            self.street_lamps.append(StreetLamp(lx, ly, 0.0))
            # Lamp post collision
            self.colliders.append(AABB(lx - 0.25, ly - 0.25, 0.0, lx + 0.25, ly + 0.25, 4.2))

    def init_gl_geometry(self, tex_mgr):
        """Compiles the static city geometry into an OpenGL Display List for maximum GPU speed."""
        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)

        # 1. Ground & Road Plane
        tex_mgr.bind(tex_mgr.tex_road)
        glEnable(GL_TEXTURE_2D)
        glColor3f(1.0, 1.0, 1.0)

        # Main Avenue (running Y from 0 to 80, X from 36 to 44)
        road_tiles = 10
        glBegin(GL_QUADS)
        glNormal3f(0.0, 0.0, 1.0)
        glTexCoord2f(0.0, 0.0); glVertex3f(36.0, 0.0, 0.01)
        glTexCoord2f(1.0, 0.0); glVertex3f(44.0, 0.0, 0.01)
        glTexCoord2f(1.0, road_tiles); glVertex3f(44.0, 80.0, 0.01)
        glTexCoord2f(0.0, road_tiles); glVertex3f(36.0, 80.0, 0.01)

        # Cross Street (running X from 0 to 80, Y from 36 to 44)
        glTexCoord2f(0.0, 0.0); glVertex3f(0.0, 36.0, 0.012)
        glTexCoord2f(road_tiles, 0.0); glVertex3f(80.0, 36.0, 0.012)
        glTexCoord2f(road_tiles, 1.0); glVertex3f(80.0, 44.0, 0.012)
        glTexCoord2f(0.0, 1.0); glVertex3f(0.0, 44.0, 0.012)
        glEnd()

        # 2. Raised Sidewalks around Blocks
        tex_mgr.bind(tex_mgr.tex_sidewalk)
        sidewalk_blocks = [
            (4.0, 4.0, 31.0, 31.0),
            (45.0, 4.0, 72.0, 31.0),
            (4.0, 45.0, 31.0, 72.0),
            (45.0, 45.0, 72.0, 72.0),
        ]
        sw_h = 0.22
        for x1, y1, x2, y2 in sidewalk_blocks:
            # Sidewalk top
            glBegin(GL_QUADS)
            glNormal3f(0.0, 0.0, 1.0)
            u_len = (x2 - x1) / 3.0
            v_len = (y2 - y1) / 3.0
            glTexCoord2f(0.0, 0.0); glVertex3f(x1, y1, sw_h)
            glTexCoord2f(u_len, 0.0); glVertex3f(x2, y1, sw_h)
            glTexCoord2f(u_len, v_len); glVertex3f(x2, y2, sw_h)
            glTexCoord2f(0.0, v_len); glVertex3f(x1, y2, sw_h)
            glEnd()

            # Sidewalk curb edges
            glDisable(GL_TEXTURE_2D)
            glColor3f(0.55, 0.56, 0.58)
            glBegin(GL_QUADS)
            # South edge
            glNormal3f(0.0, -1.0, 0.0)
            glVertex3f(x1, y1, 0.0); glVertex3f(x2, y1, 0.0)
            glVertex3f(x2, y1, sw_h); glVertex3f(x1, y1, sw_h)
            # North edge
            glNormal3f(0.0, 1.0, 0.0)
            glVertex3f(x2, y2, 0.0); glVertex3f(x1, y2, 0.0)
            glVertex3f(x1, y2, sw_h); glVertex3f(x2, y2, sw_h)
            # West edge
            glNormal3f(-1.0, 0.0, 0.0)
            glVertex3f(x1, y2, 0.0); glVertex3f(x1, y1, 0.0)
            glVertex3f(x1, y1, sw_h); glVertex3f(x1, y2, sw_h)
            # East edge
            glNormal3f(1.0, 0.0, 0.0)
            glVertex3f(x2, y1, 0.0); glVertex3f(x2, y2, 0.0)
            glVertex3f(x2, y2, sw_h); glVertex3f(x2, y1, sw_h)
            glEnd()
            glEnable(GL_TEXTURE_2D)
            glColor3f(1.0, 1.0, 1.0)

        # 3. 3D Buildings (Walls & Rooftops)
        for b in self.buildings:
            tex = tex_mgr.tex_tower if b.style == "tower" else tex_mgr.tex_brick
            tex_mgr.bind(tex)

            x1, y1 = b.x, b.y
            x2, y2 = b.x + b.width, b.y + b.depth
            h = b.height

            u_w = b.width / 4.0
            u_d = b.depth / 4.0
            v_h = h / 3.0

            glBegin(GL_QUADS)
            # Front (South, -Y)
            glNormal3f(0.0, -1.0, 0.0)
            glTexCoord2f(0.0, 0.0); glVertex3f(x1, y1, 0.0)
            glTexCoord2f(u_w, 0.0); glVertex3f(x2, y1, 0.0)
            glTexCoord2f(u_w, v_h); glVertex3f(x2, y1, h)
            glTexCoord2f(0.0, v_h); glVertex3f(x1, y1, h)

            # Back (North, +Y)
            glNormal3f(0.0, 1.0, 0.0)
            glTexCoord2f(0.0, 0.0); glVertex3f(x2, y2, 0.0)
            glTexCoord2f(u_w, 0.0); glVertex3f(x1, y2, 0.0)
            glTexCoord2f(u_w, v_h); glVertex3f(x1, y2, h)
            glTexCoord2f(0.0, v_h); glVertex3f(x2, y2, h)

            # Left (West, -X)
            glNormal3f(-1.0, 0.0, 0.0)
            glTexCoord2f(0.0, 0.0); glVertex3f(x1, y2, 0.0)
            glTexCoord2f(u_d, 0.0); glVertex3f(x1, y1, 0.0)
            glTexCoord2f(u_d, v_h); glVertex3f(x1, y1, h)
            glTexCoord2f(0.0, v_h); glVertex3f(x1, y2, h)

            # Right (East, +X)
            glNormal3f(1.0, 0.0, 0.0)
            glTexCoord2f(0.0, 0.0); glVertex3f(x2, y1, 0.0)
            glTexCoord2f(u_d, 0.0); glVertex3f(x2, y2, 0.0)
            glTexCoord2f(u_d, v_h); glVertex3f(x2, y2, h)
            glTexCoord2f(0.0, v_h); glVertex3f(x2, y1, h)
            glEnd()

            # Rooftop
            tex_mgr.bind(tex_mgr.tex_roof)
            glBegin(GL_QUADS)
            glNormal3f(0.0, 0.0, 1.0)
            glTexCoord2f(0.0, 0.0); glVertex3f(x1, y1, h)
            glTexCoord2f(u_w, 0.0); glVertex3f(x2, y1, h)
            glTexCoord2f(u_w, u_d); glVertex3f(x2, y2, h)
            glTexCoord2f(0.0, u_d); glVertex3f(x1, y2, h)
            glEnd()

        # 4. Street Lamps
        glDisable(GL_TEXTURE_2D)
        for lamp in self.street_lamps:
            self._render_street_lamp(lamp.x, lamp.y, lamp.z)

        glEndList()

    def _render_street_lamp(self, x, y, z):
        # Steel dark pole
        glColor3f(0.25, 0.28, 0.32)
        glBegin(GL_QUADS)
        r = 0.08
        h = 4.2
        # Simple square prism pole
        glVertex3f(x - r, y - r, z); glVertex3f(x + r, y - r, z); glVertex3f(x + r, y - r, z + h); glVertex3f(x - r, y - r, z + h)
        glVertex3f(x + r, y - r, z); glVertex3f(x + r, y + r, z); glVertex3f(x + r, y + r, z + h); glVertex3f(x + r, y - r, z + h)
        glVertex3f(x + r, y + r, z); glVertex3f(x - r, y + r, z); glVertex3f(x - r, y + r, z + h); glVertex3f(x + r, y + r, z + h)
        glVertex3f(x - r, y + r, z); glVertex3f(x - r, y - r, z); glVertex3f(x - r, y - r, z + h); glVertex3f(x - r, y + r, z + h)
        glEnd()

        # Curved top arm
        glBegin(GL_QUADS)
        glVertex3f(x - r, y - r, z + h); glVertex3f(x + 0.8, y - r, z + h + 0.4); glVertex3f(x + 0.8, y + r, z + h + 0.4); glVertex3f(x - r, y + r, z + h)
        glEnd()

        # Glowing lantern bulb (warm GTA yellow)
        glColor3f(1.0, 0.92, 0.55)
        glBegin(GL_QUADS)
        bx, by, bz = x + 0.7, y, z + h + 0.25
        br = 0.16
        glVertex3f(bx - br, by - br, bz); glVertex3f(bx + br, by - br, bz); glVertex3f(bx + br, by + br, bz); glVertex3f(bx - br, by + br, bz)
        glVertex3f(bx - br, by - br, bz - br); glVertex3f(bx + br, by - br, bz - br); glVertex3f(bx + br, by - br, bz); glVertex3f(bx - br, by - br, bz)
        glEnd()

    def render(self):
        """Renders the compiled city geometry instantly with 1 draw call."""
        if self.display_list != 0:
            glCallList(self.display_list)

    def resolve_player_collision(self, px: float, py: float, radius: float) -> tuple:
        """
        Tests player cylinder against all building AABBs and resolves sliding movement.
        """
        resolved_x = px
        resolved_y = py

        for aabb in self.colliders:
            if aabb.intersects_circle_2d(resolved_x, resolved_y, radius):
                # Push player out along axis of least penetration
                closest_x = max(aabb.min_x, min(resolved_x, aabb.max_x))
                closest_y = max(aabb.min_y, min(resolved_y, aabb.max_y))
                diff_x = resolved_x - closest_x
                diff_y = resolved_y - closest_y
                dist = math.hypot(diff_x, diff_y)
                if dist > 0.0001:
                    push = radius - dist
                    resolved_x += (diff_x / dist) * push
                    resolved_y += (diff_y / dist) * push
                else:
                    # Inside box: push out to nearest edge
                    d_left = abs(resolved_x - aabb.min_x)
                    d_right = abs(aabb.max_x - resolved_x)
                    d_bot = abs(resolved_y - aabb.min_y)
                    d_top = abs(aabb.max_y - resolved_y)
                    m = min(d_left, d_right, d_bot, d_top)
                    if m == d_left: resolved_x = aabb.min_x - radius
                    elif m == d_right: resolved_x = aabb.max_x + radius
                    elif m == d_bot: resolved_y = aabb.min_y - radius
                    else: resolved_y = aabb.max_y + radius

        return resolved_x, resolved_y

    def raycast_camera_spring_arm(self, p_start: tuple, p_end: tuple) -> float:
        """
        Casts a ray from pivot (character eye/chest) to camera target.
        Returns closest intersection factor t in [0, 1].
        """
        closest_t = 1.0
        for aabb in self.colliders:
            t = aabb.ray_intersect(p_start, p_end)
            if t < closest_t:
                closest_t = t
        return closest_t
