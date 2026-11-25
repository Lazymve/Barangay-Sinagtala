"""
High-performance DDA 3D Raycasting Engine with Dynamic FOV, Pitch Shifting,
and 3D Software Polygon Rasterizer for Barangay Sinagtala 3D.
"""

import math
import pygame
from map_data import get_tile, MAP_COLS, MAP_ROWS
from textures import TextureManager, TEXTURE_SIZE
from model_3d import LIGHT_DIR


class Raycaster:
    def __init__(self, render_w: int = 640, render_h: int = 360, fov_deg: float = 65.0):
        self.render_w = render_w
        self.render_h = render_h
        self.current_fov_deg = fov_deg
        self.fov = math.radians(fov_deg)
        self.half_fov = self.fov / 2.0
        self.num_rays = render_w
        self.delta_angle = self.fov / float(self.num_rays)
        self.dist_to_proj = (self.render_w / 2.0) / math.tan(self.half_fov)

        self.texture_mgr = TextureManager()
        self.surface = pygame.Surface((self.render_w, self.render_h))
        self.z_buffer = [9999.0] * self.num_rays

        # Sky and floor base colors
        self.sky_top = (45, 95, 165)
        self.sky_bottom = (160, 200, 235)
        self.floor_near = (60, 52, 45)
        self.floor_far = (30, 26, 22)

    def _set_fov(self, fov_deg: float):
        """Dynamically adjusts projection geometry when sprinting or aiming."""
        if abs(self.current_fov_deg - fov_deg) > 0.15:
            self.current_fov_deg = fov_deg
            self.fov = math.radians(fov_deg)
            self.half_fov = self.fov / 2.0
            self.delta_angle = self.fov / float(self.num_rays)
            self.dist_to_proj = (self.render_w / 2.0) / math.tan(self.half_fov)

    def _draw_background(self, pitch_offset: int):
        horizon_y = max(0, min(self.render_h, (self.render_h // 2) + pitch_offset))

        # Sky gradient above horizon
        if horizon_y > 0:
            for y in range(horizon_y):
                t = y / float(max(1, horizon_y))
                r = int(self.sky_top[0] * (1.0 - t) + self.sky_bottom[0] * t)
                g = int(self.sky_top[1] * (1.0 - t) + self.sky_bottom[1] * t)
                b = int(self.sky_top[2] * (1.0 - t) + self.sky_bottom[2] * t)
                pygame.draw.line(self.surface, (r, g, b), (0, y), (self.render_w, y))

        # Floor gradient below horizon
        if horizon_y < self.render_h:
            floor_span = float(self.render_h - horizon_y)
            for y in range(horizon_y, self.render_h):
                t = (y - horizon_y) / floor_span
                r = int(self.floor_far[0] * (1.0 - t) + self.floor_near[0] * t)
                g = int(self.floor_far[1] * (1.0 - t) + self.floor_near[1] * t)
                b = int(self.floor_far[2] * (1.0 - t) + self.floor_near[2] * t)
                pygame.draw.line(self.surface, (r, g, b), (0, y), (self.render_w, y))

    def render(self, camera, character=None) -> pygame.Surface:
        # 1. Update dynamic FOV from camera
        if hasattr(camera, "current_fov"):
            self._set_fov(camera.current_fov)

        pitch_offset = int(camera.pitch * self.dist_to_proj)

        # 2. Draw dynamic horizon background
        self._draw_background(pitch_offset)

        cam_x = camera.x
        cam_y = camera.y
        start_angle = camera.angle - self.half_fov

        # 3. Cast one ray per screen column & fill Z-Buffer
        for ray_idx in range(self.num_rays):
            ray_angle = start_angle + ray_idx * self.delta_angle
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            sin_safe = sin_a if sin_a != 0 else 0.000001
            cos_safe = cos_a if cos_a != 0 else 0.000001

            map_x = int(cam_x)
            map_y = int(cam_y)

            delta_dist_x = abs(1.0 / cos_safe)
            delta_dist_y = abs(1.0 / sin_safe)

            if cos_safe < 0:
                step_x = -1
                side_dist_x = (cam_x - map_x) * delta_dist_x
            else:
                step_x = 1
                side_dist_x = (map_x + 1.0 - cam_x) * delta_dist_x

            if sin_safe < 0:
                step_y = -1
                side_dist_y = (cam_y - map_y) * delta_dist_y
            else:
                step_y = 1
                side_dist_y = (map_y + 1.0 - cam_y) * delta_dist_y

            hit_tile = 0
            side = 0
            max_depth = 22
            depth = 0

            while hit_tile == 0 and depth < max_depth:
                if side_dist_x < side_dist_y:
                    side_dist_x += delta_dist_x
                    map_x += step_x
                    side = 0
                else:
                    side_dist_y += delta_dist_y
                    map_y += step_y
                    side = 1

                hit_tile = get_tile(map_x, map_y)
                depth += 1

            if hit_tile == 0:
                self.z_buffer[ray_idx] = 9999.0
                continue

            if side == 0:
                perp_dist = (map_x - cam_x + (1 - step_x) / 2) / cos_safe
                wall_hit_u = cam_y + perp_dist * sin_a
            else:
                perp_dist = (map_y - cam_y + (1 - step_y) / 2) / sin_safe
                wall_hit_u = cam_x + perp_dist * cos_a

            perp_dist = max(0.05, perp_dist)
            self.z_buffer[ray_idx] = perp_dist
            wall_hit_u -= math.floor(wall_hit_u)

            slice_h = int(self.dist_to_proj / perp_dist)
            top_y = (self.render_h - slice_h) // 2 + pitch_offset

            tex_x = int(wall_hit_u * TEXTURE_SIZE)
            if (side == 0 and cos_safe > 0) or (side == 1 and sin_safe < 0):
                tex_x = TEXTURE_SIZE - tex_x - 1

            tex = self.texture_mgr.get_texture(hit_tile, is_ew_face=(side == 0))
            tex_col = tex.subsurface((tex_x, 0, 1, TEXTURE_SIZE))

            scaled_stripe = pygame.transform.scale(tex_col, (1, slice_h))

            fog_factor = min(210, int(perp_dist * 20))
            if fog_factor > 0:
                fog_surf = pygame.Surface((1, slice_h))
                fog_surf.fill((18, 22, 28))
                fog_surf.set_alpha(fog_factor)
                scaled_stripe.blit(fog_surf, (0, 0))

            self.surface.blit(scaled_stripe, (ray_idx, top_y))

        # 4. Render 3D Articulated White Bean Mesh in Third-Person Mode
        if character is not None and camera.mode == camera.THIRD_PERSON:
            self._render_3d_character_mesh(camera, character, pitch_offset)

        return self.surface

    def _render_3d_character_mesh(self, camera, character, pitch_offset: int):
        cam_x = camera.x
        cam_y = camera.y
        cam_z = 0.5
        cos_c = math.cos(camera.angle)
        sin_c = math.sin(camera.angle)

        half_w = self.render_w / 2.0
        half_h = self.render_h / 2.0

        # 1. 3D Ground Shadow under character
        dx = character.x - cam_x
        dy = character.y - cam_y
        shadow_depth = dx * cos_c + dy * sin_c
        if shadow_depth > 0.25:
            shadow_u = dy * cos_c - dx * sin_c
            sx = int(half_w + (shadow_u / shadow_depth) * self.dist_to_proj)
            sy = int(half_h - ((0.01 - cam_z) / shadow_depth) * self.dist_to_proj) + pitch_offset
            sw = max(4, int((self.dist_to_proj / shadow_depth) * 0.44))
            sh = max(2, int((self.dist_to_proj / shadow_depth) * 0.20))
            shadow_rect = pygame.Rect(sx - sw // 2, sy - sh // 2, sw, sh)
            s_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.ellipse(s_surf, (15, 18, 24, 150), (0, 0, sw, sh))
            self.surface.blit(s_surf, shadow_rect.topleft)

        # 2. Retrieve world-space 3D polygons from the character
        world_polys = character.get_world_polygons()
        projected_polys = []
        lx, ly, lz = LIGHT_DIR

        for poly in world_polys:
            cam_verts = []
            screen_pts = []
            sum_z = 0.0
            all_valid = True

            for wx, wy, wz in poly.vertices:
                vx = wx - cam_x
                vy = wy - cam_y
                vz = wz - cam_z

                z_cam = vx * cos_c + vy * sin_c
                x_cam = vy * cos_c - vx * sin_c
                y_cam = vz

                if z_cam < 0.12:
                    all_valid = False
                    break

                sum_z += z_cam
                cam_verts.append((x_cam, y_cam, z_cam))

                # Perspective division to screen coordinates + pitch offset
                px = half_w + (x_cam / z_cam) * self.dist_to_proj
                py = half_h - (y_cam / z_cam) * self.dist_to_proj + pitch_offset
                screen_pts.append((px, py))

            if not all_valid or len(screen_pts) < 3:
                continue

            avg_depth = sum_z / float(len(poly.vertices))

            # Screen bounds check
            xs = [p[0] for p in screen_pts]
            min_x = int(min(xs))
            max_x = int(max(xs))

            if max_x < 0 or min_x >= self.render_w:
                continue

            # Z-Buffer Occlusion check against walls
            sample_step = max(1, (max_x - min_x) // 5)
            behind_wall = True
            for test_x in range(max(0, min_x), min(self.render_w, max_x + 1), sample_step):
                if avg_depth < self.z_buffer[test_x]:
                    behind_wall = False
                    break

            if behind_wall:
                continue

            # 3D Normal & Directional Lighting
            nx, ny, nz = poly.normal
            dot = nx * lx + ny * ly + nz * lz
            diffuse = max(0.0, dot)
            intensity = 0.42 + 0.58 * diffuse

            # Distance fog on character
            fog = max(0.0, 1.0 - (avg_depth / 16.0))
            intensity *= fog

            br, bg, bb = poly.base_color
            lit_r = min(255, int(br * intensity))
            lit_g = min(255, int(bg * intensity))
            lit_b = min(255, int(bb * intensity))

            projected_polys.append((avg_depth, (lit_r, lit_g, lit_b), screen_pts))

        # 3. Sort polygons back-to-front (Painter's Algorithm)
        projected_polys.sort(key=lambda item: item[0], reverse=True)

        # 4. Rasterize shaded 3D polygons
        for _, color, pts in projected_polys:
            pygame.draw.polygon(self.surface, color, pts)
            outline_r = max(0, color[0] - 28)
            outline_g = max(0, color[1] - 28)
            outline_b = max(0, color[2] - 28)
            pygame.draw.polygon(self.surface, (outline_r, outline_g, outline_b), pts, 1)
