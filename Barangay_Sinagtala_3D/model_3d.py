"""
3D Polygonal Mesh Generator and GTA-Style Kinematics for the White Bean Character.
Includes tactical aiming stance, lateral strafe leg kinematics,
and banking lean during turns.
"""

import math

# Directional light in world space (shining from top-front-left)
LIGHT_DIR = (0.577, -0.577, 0.577)


class Polygon3D:
    """Represents a 3D polygon face with vertices, normal, and base color."""
    __slots__ = ("vertices", "base_color", "normal", "depth")

    def __init__(self, vertices, base_color):
        self.vertices = vertices  # List of (x, y, z) tuples
        self.base_color = base_color
        self.normal = self._compute_normal()
        self.depth = 0.0

    def _compute_normal(self):
        if len(self.vertices) < 3:
            return (0.0, 0.0, 1.0)
        v0, v1, v2 = self.vertices[0], self.vertices[1], self.vertices[2]
        ax, ay, az = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
        bx, by, bz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]
        nx = ay * bz - az * by
        ny = az * bx - ax * bz
        nz = ax * by - ay * bx
        length = math.hypot(math.hypot(nx, ny), nz)
        if length > 0:
            return (nx / length, ny / length, nz / length)
        return (0.0, 0.0, 1.0)


def _rotate_z(x, y, z, angle):
    """Rotates around vertical Z axis (heading)."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return (x * cos_a - y * sin_a, x * sin_a + y * cos_a, z)


def _rotate_x(x, y, z, angle):
    """Rotates around X axis (banking lean / roll)."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return (x, y * cos_a - z * sin_a, y * sin_a + z * cos_a)


def create_capsule_mesh(cx, cy, cz, radius, height, num_lat=6, num_long=10, color=(240, 240, 242)):
    """Creates a 3D capsule mesh with hemisphere top, cylinder mid, and hemisphere bottom."""
    polygons = []
    half_h = height / 2.0
    cyl_top = cz + half_h
    cyl_bot = cz - half_h
    rings = []

    # Top hemisphere
    lat_steps = num_lat // 2
    for i in range(lat_steps + 1):
        phi = (math.pi / 2.0) * (i / float(lat_steps))
        z_offset = radius * math.sin(phi)
        r = radius * math.cos(phi)
        z = cyl_top + z_offset
        ring = []
        for j in range(num_long):
            theta = 2.0 * math.pi * (j / float(num_long))
            ring.append((cx + r * math.cos(theta), cy + r * math.sin(theta), z))
        rings.append(ring)

    # Bottom hemisphere
    for i in range(lat_steps + 1):
        phi = (math.pi / 2.0) * (i / float(lat_steps))
        z_offset = radius * math.sin(phi)
        r = radius * math.cos(phi)
        z = cyl_bot - z_offset
        ring = []
        for j in range(num_long):
            theta = 2.0 * math.pi * (j / float(num_long))
            ring.append((cx + r * math.cos(theta), cy + r * math.sin(theta), z))
        rings.append(ring)

    # Connect adjacent rings with quad faces
    for r_idx in range(len(rings) - 1):
        r1 = rings[r_idx]
        r2 = rings[r_idx + 1]
        for j in range(num_long):
            j_next = (j + 1) % num_long
            v0 = r1[j]
            v1 = r1[j_next]
            v2 = r2[j_next]
            v3 = r2[j]
            polygons.append(Polygon3D([v0, v1, v2, v3], color))

    return polygons


def create_ellipsoid_mesh(cx, cy, cz, rx, ry, rz, num_lat=4, num_long=8, color=(240, 240, 242)):
    """Creates a 3D ellipsoid mesh for floating hands and feet."""
    polygons = []
    rings = []
    for i in range(num_lat + 1):
        phi = -math.pi / 2.0 + math.pi * (i / float(num_lat))
        z = cz + rz * math.sin(phi)
        r_mult = math.cos(phi)
        ring = []
        for j in range(num_long):
            theta = 2.0 * math.pi * (j / float(num_long))
            ring.append((cx + rx * r_mult * math.cos(theta), cy + ry * r_mult * math.sin(theta), z))
        rings.append(ring)

    for r_idx in range(len(rings) - 1):
        r1 = rings[r_idx]
        r2 = rings[r_idx + 1]
        for j in range(num_long):
            j_next = (j + 1) % num_long
            v0 = r1[j]
            v1 = r1[j_next]
            v2 = r2[j_next]
            v3 = r2[j]
            polygons.append(Polygon3D([v0, v1, v2, v3], color))

    return polygons


def create_visor_mesh(cx, cy, cz, radius, width_angle=math.pi * 0.48, height=0.065, color=(24, 28, 38)):
    """Creates a sleek dark-glass sensor visor band curved along the front face (+X direction)."""
    polygons = []
    num_segs = 6
    half_angle = width_angle / 2.0
    r_outer = radius * 1.025
    z_top = cz + height / 2.0
    z_bot = cz - height / 2.0
    top_ring = []
    bot_ring = []

    for i in range(num_segs + 1):
        theta = -half_angle + width_angle * (i / float(num_segs))
        top_ring.append((cx + r_outer * math.cos(theta), cy + r_outer * math.sin(theta), z_top))
        bot_ring.append((cx + r_outer * math.cos(theta), cy + r_outer * math.sin(theta), z_bot))

    for i in range(num_segs):
        v0 = top_ring[i]
        v1 = top_ring[i + 1]
        v2 = bot_ring[i + 1]
        v3 = bot_ring[i]
        polygons.append(Polygon3D([v0, v1, v2, v3], color))

    return polygons


class WhiteBean3DModel:
    """
    True 3D Articulated White Bean Character Model with GTA 6-style
    locomotion kinematics, aiming stance, and bank-leaning.
    """

    def __init__(self):
        self.body_radius = 0.165
        self.body_height = 0.22
        self.total_center_z = 0.44

    def build_world_polygons(self, world_x: float, world_y: float, heading: float,
                             is_moving: bool, anim_time: float,
                             is_aiming: bool = False, banking_roll: float = 0.0,
                             strafe_side: float = 0.0) -> list:
        polygons = []

        if is_moving:
            stride_angle = math.sin(anim_time) * 0.36
            leg_lift = max(0.0, math.cos(anim_time)) * 0.04
            arm_swing = -math.sin(anim_time) * 0.40
            body_bounce = abs(math.sin(anim_time * 2.0)) * 0.02
        else:
            stride_angle = 0.0
            leg_lift = 0.0
            arm_swing = 0.0
            body_bounce = 0.0

        white_pearl = (242, 243, 246)
        charcoal_glass = (25, 30, 42)
        limb_white = (235, 236, 240)
        foot_sole = (70, 75, 88)

        body_z = self.total_center_z + body_bounce

        # 1. Main White Bean Body
        torso_polys = create_capsule_mesh(
            0.0, 0.0, body_z,
            radius=self.body_radius,
            height=self.body_height,
            num_lat=6,
            num_long=10,
            color=white_pearl
        )
        polygons.extend(torso_polys)

        # 2. Sleek Dark Visor Band
        visor_z = body_z + 0.12
        visor_polys = create_visor_mesh(
            0.0, 0.0, visor_z,
            radius=self.body_radius,
            width_angle=math.pi * 0.48,
            height=0.065,
            color=charcoal_glass
        )
        polygons.extend(visor_polys)

        # 3. 3D Floating Left & Right Hands (Aim Stance vs Free-Roam Swing)
        hand_r = 0.045
        hand_dist_y = self.body_radius + 0.065
        hand_base_z = body_z - 0.02

        if is_aiming:
            # GTA Aim Stance: Hands raised forward pointing at crosshair
            lh_x = 0.22
            lh_y = 0.05
            lh_z = body_z + 0.06
            l_hand = create_ellipsoid_mesh(lh_x, lh_y, lh_z, hand_r, hand_r, hand_r * 1.25, color=limb_white)
            polygons.extend(l_hand)

            rh_x = 0.24
            rh_y = -0.04
            rh_z = body_z + 0.055
            r_hand = create_ellipsoid_mesh(rh_x, rh_y, rh_z, hand_r, hand_r, hand_r * 1.25, color=limb_white)
            polygons.extend(r_hand)
        else:
            lh_x = math.sin(arm_swing) * 0.12
            lh_y = hand_dist_y
            lh_z = hand_base_z + math.cos(arm_swing) * 0.02
            l_hand = create_ellipsoid_mesh(lh_x, lh_y, lh_z, hand_r, hand_r, hand_r * 1.25, color=limb_white)
            polygons.extend(l_hand)

            rh_x = math.sin(-arm_swing) * 0.12
            rh_y = -hand_dist_y
            rh_z = hand_base_z + math.cos(-arm_swing) * 0.02
            r_hand = create_ellipsoid_mesh(rh_x, rh_y, rh_z, hand_r, hand_r, hand_r * 1.25, color=limb_white)
            polygons.extend(r_hand)

        # 4. 3D Floating Left & Right Feet
        foot_rx = 0.08
        foot_ry = 0.045
        foot_rz = 0.035
        foot_dist_y = 0.085
        foot_base_z = 0.045

        strafe_offset_l = strafe_side * 0.06 if is_aiming else 0.0
        strafe_offset_r = -strafe_side * 0.06 if is_aiming else 0.0

        lf_x = math.sin(stride_angle) * 0.14
        lf_y = foot_dist_y + strafe_offset_l
        lf_z = foot_base_z + (leg_lift if stride_angle > 0 else 0.0)
        l_foot = create_ellipsoid_mesh(lf_x, lf_y, lf_z, foot_rx, foot_ry, foot_rz, color=foot_sole)
        polygons.extend(l_foot)

        rf_x = math.sin(-stride_angle) * 0.14
        rf_y = -foot_dist_y + strafe_offset_r
        rf_z = foot_base_z + (leg_lift if stride_angle < 0 else 0.0)
        r_foot = create_ellipsoid_mesh(rf_x, rf_y, rf_z, foot_rx, foot_ry, foot_rz, color=foot_sole)
        polygons.extend(r_foot)

        # 5. Transform all polygons to 3D World Space
        world_polygons = []
        for poly in polygons:
            world_verts = []
            for vx, vy, vz in poly.vertices:
                if banking_roll != 0.0:
                    vx, vy, vz = _rotate_x(vx, vy, vz, banking_roll)

                rx, ry, rz = _rotate_z(vx, vy, vz, heading)
                wx = world_x + rx
                wy = world_y + ry
                wz = rz
                world_verts.append((wx, wy, wz))

            world_poly = Polygon3D(world_verts, poly.base_color)
            world_polygons.append(world_poly)

        return world_polygons
