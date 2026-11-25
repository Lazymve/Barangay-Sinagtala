"""
PyOpenGL 3D Rendering Pipeline for Barangay Sinagtala 3D.
Handles perspective projection, depth buffering, GTA III/IV atmospheric distance fog,
directional/ambient lighting, 3D rain particle effects, and 2D Orthographic HUD overlays.
"""

import math
import random
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *


class RainSystem:
    """3D volumetric falling rain streaks centered dynamically around the player."""

    def __init__(self, count: int = 550, box_size: float = 38.0):
        self.count = count
        self.box_size = box_size
        self.particles = []
        rng = random.Random(42)
        for _ in range(count):
            rx = rng.uniform(-box_size, box_size)
            ry = rng.uniform(-box_size, box_size)
            rz = rng.uniform(0.1, 18.0)
            spd = rng.uniform(22.0, 32.0)
            length = rng.uniform(0.4, 0.7)
            self.particles.append([rx, ry, rz, spd, length])

    def update(self, dt: float, player_x: float, player_y: float):
        half_box = self.box_size
        for p in self.particles:
            p[2] -= p[3] * dt
            # If hit ground, respawn above player
            if p[2] <= 0.05:
                p[2] = random.uniform(14.0, 20.0)
                p[0] = random.uniform(-half_box, half_box)
                p[1] = random.uniform(-half_box, half_box)

    def render_gl(self, player_x: float, player_y: float):
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.72, 0.78, 0.88, 0.45)
        glLineWidth(1.2)

        glBegin(GL_LINES)
        for rx, ry, rz, _, length in self.particles:
            wx = player_x + rx
            wy = player_y + ry
            glVertex3f(wx, wy, rz)
            glVertex3f(wx - 0.06, wy - 0.06, rz - length)
        glEnd()

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)


class RendererGL:
    """
    Main OpenGL 3D Render Engine.
    Configures projection matrices, lighting, atmospheric fog,
    renders city & character, and draws 2D HUD.
    """

    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.aspect = width / float(height)

        # GTA Liberty City overcast fog color (slate blue-gray)
        self.fog_color = [0.18, 0.22, 0.27, 1.0]
        self.rain = RainSystem(count=550)
        self.rain_enabled = True

        self._init_gl_state()

    def _init_gl_state(self):
        glClearColor(self.fog_color[0], self.fog_color[1], self.fog_color[2], 1.0)
        glClearDepth(1.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        # Lighting setup
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [0.45, -0.65, 0.85, 0.0])  # Directional sun
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.85, 0.85, 0.90, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.45, 0.45, 0.45, 1.0])
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.38, 0.40, 0.46, 1.0])

        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # GTA Atmospheric Distance Fog
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_EXP2)
        glFogfv(GL_FOG_COLOR, self.fog_color)
        glFogf(GL_FOG_DENSITY, 0.022)
        glHint(GL_FOG_HINT, GL_NICEST)

    def begin_frame(self, camera):
        """Clears buffers and sets up the 3D perspective projection and camera view."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # 3D Perspective Projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(camera.current_fov, self.aspect, 0.15, 120.0)

        # Camera View Matrix (gluLookAt)
        camera.apply_view()

    def render_world(self, city_env, character, camera, dt: float, show_debug: bool = True):
        """Renders the 3D City, Character, and Atmospheric effects."""
        # 1. 3D City Architecture
        glEnable(GL_LIGHTING)
        city_env.render()

        # 2. 3D Character Model (only in third-person mode)
        if camera.mode == camera.THIRD_PERSON:
            character.render_gl()

        # 3. 3D Atmospheric Rain
        if self.rain_enabled:
            self.rain.update(dt, character.x, character.y)
            self.rain.render_gl(character.x, character.y)

        # 4. Optional 3D Debug Direction Vectors
        if show_debug:
            self._render_3d_debug_vectors(character, camera)

    def _render_3d_debug_vectors(self, character, camera):
        """Renders colorful 3D vector arrows around player to visually verify coordinate math."""
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_FOG)
        glLineWidth(3.5)

        px, py, pz = character.x, character.y, character.z + 0.12

        cos_c = math.cos(camera.yaw)
        sin_c = math.sin(camera.yaw)

        glBegin(GL_LINES)
        # 1. Camera Forward Vector (CYAN, length 2.2m)
        glColor3f(0.0, 0.85, 1.0)
        glVertex3f(px, py, pz); glVertex3f(px + cos_c * 2.2, py + sin_c * 2.2, pz)

        # 2. Camera Right Vector (MAGENTA, length 2.2m) [sin_c, -cos_c]
        glColor3f(1.0, 0.15, 0.55)
        glVertex3f(px, py, pz); glVertex3f(px + sin_c * 2.2, py - cos_c * 2.2, pz)

        # 3. Character Facing Vector (BRIGHT GREEN, length 2.5m)
        cos_f = math.cos(character.facing_yaw)
        sin_f = math.sin(character.facing_yaw)
        glColor3f(0.15, 1.0, 0.25)
        glVertex3f(px, py, pz + 0.05); glVertex3f(px + cos_f * 2.5, py + sin_f * 2.5, pz + 0.05)

        # 4. Movement Input Vector (YELLOW, length 2.0m)
        if character.has_movement_input:
            glColor3f(1.0, 0.95, 0.1)
            glVertex3f(px, py, pz + 0.10)
            glVertex3f(px + character.movement_dir_x * 2.0, py + character.movement_dir_y * 2.0, pz + 0.10)

        # 5. Velocity Vector (ORANGE, scaled)
        if character.current_speed > 0.15:
            glColor3f(1.0, 0.5, 0.05)
            glVertex3f(px, py, pz + 0.15)
            glVertex3f(px + character.vx * 0.5, py + character.vy * 0.5, pz + 0.15)
        glEnd()

        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)

    def draw_2d_hud(self, camera, character, fps: int, show_minimap: bool, mouse_locked: bool, show_debug: bool = True):
        """Switches to 2D Orthographic mode to render dynamic reticle, minimap, and HUD text."""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0.0, self.width, self.height, 0.0, -1.0, 1.0)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # 1. Dynamic GTA Reticle in screen center
        cx, cy = self.width // 2, self.height // 2
        spread = min(14, int(character.current_speed * 2.0))
        gap = 5 if character.is_aiming else (7 + spread)
        length = 4 if character.is_aiming else 5

        glColor4f(1.0, 1.0, 1.0, 0.90 if character.is_aiming else 0.70)
        glLineWidth(1.6)
        glBegin(GL_LINES)
        glVertex2f(cx - gap - length, cy); glVertex2f(cx - gap, cy)
        glVertex2f(cx + gap, cy); glVertex2f(cx + gap + length, cy)
        glVertex2f(cx, cy - gap - length); glVertex2f(cx, cy - gap)
        glVertex2f(cx, cy + gap); glVertex2f(cx, cy + gap + length)
        glEnd()

        # Center dot
        glColor4f(1.0, 1.0, 1.0, 0.95)
        glPointSize(3.0)
        glBegin(GL_POINTS)
        glVertex2f(cx, cy)
        glEnd()

        # 2. 2D Minimap Radar
        if show_minimap:
            self._draw_minimap_gl(camera, character)

        # 3. 2D Debug Diagnostics Card
        if show_debug:
            self._draw_debug_overlay_2d(camera, character, fps)

        # Restore 3D OpenGL State
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def _draw_minimap_gl(self, camera, character):
        """Draws a clean 2D radar in the top-left corner."""
        mx, my = 20.0, 20.0
        size = 140.0
        half = size / 2.0

        # Radar circular / square dark backing
        glColor4f(0.08, 0.10, 0.14, 0.85)
        glBegin(GL_QUADS)
        glVertex2f(mx, my)
        glVertex2f(mx + size, my)
        glVertex2f(mx + size, my + size)
        glVertex2f(mx, my + size)
        glEnd()

        # Radar border (gold GTA accent)
        glColor4f(0.82, 0.75, 0.55, 0.95)
        glLineWidth(1.4)
        glBegin(GL_LINE_LOOP)
        glVertex2f(mx, my)
        glVertex2f(mx + size, my)
        glVertex2f(mx + size, my + size)
        glVertex2f(mx, my + size)
        glEnd()

        # Center player icon
        cx = mx + half
        cy = my + half

        # Player heading arrow
        hx = cx + math.cos(character.heading) * 12.0
        hy = cy + math.sin(character.heading) * 12.0
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glVertex2f(cx, cy)
        glVertex2f(hx, hy)
        glEnd()

        # Player dot (white)
        glPointSize(6.0)
        glBegin(GL_POINTS)
        glVertex2f(cx, cy)
        glEnd()

        # Camera viewing cone
        cone_len = 24.0
        fov_half = math.radians(camera.current_fov) / 2.0
        lx = cx + math.cos(camera.yaw - fov_half) * cone_len
        ly = cy + math.sin(camera.yaw - fov_half) * cone_len
        rx = cx + math.cos(camera.yaw + fov_half) * cone_len
        ry = cy + math.sin(camera.yaw + fov_half) * cone_len

        glColor4f(0.95, 0.85, 0.35, 0.75)
        glLineWidth(1.2)
        glBegin(GL_LINES)
        glVertex2f(cx, cy); glVertex2f(lx, ly)
        glVertex2f(cx, cy); glVertex2f(rx, ry)
        glEnd()

    def _draw_debug_overlay_2d(self, camera, character, fps: int):
        """Renders an intuitive vector HUD card in the top-right corner."""
        bx = self.width - 330.0
        by = 20.0
        bw = 310.0
        bh = 175.0

        # Background card
        glColor4f(0.06, 0.08, 0.12, 0.88)
        glBegin(GL_QUADS)
        glVertex2f(bx, by)
        glVertex2f(bx + bw, by)
        glVertex2f(bx + bw, by + bh)
        glVertex2f(bx, by + bh)
        glEnd()

        # Border
        glColor4f(0.35, 0.55, 0.85, 0.90)
        glLineWidth(1.5)
        glBegin(GL_LINE_LOOP)
        glVertex2f(bx, by)
        glVertex2f(bx + bw, by)
        glVertex2f(bx + bw, by + bh)
        glVertex2f(bx, by + bh)
        glEnd()

        # Color legend entries: (color, label_indicator)
        # Entry 1: CYAN - Camera Forward
        glColor3f(0.0, 0.85, 1.0)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glVertex2f(bx + 15, by + 25); glVertex2f(bx + 45, by + 25)
        glEnd()

        # Entry 2: MAGENTA - Camera Right [D Key]
        glColor3f(1.0, 0.15, 0.55)
        glBegin(GL_LINES)
        glVertex2f(bx + 15, by + 50); glVertex2f(bx + 45, by + 50)
        glEnd()

        # Entry 3: GREEN - Character Heading
        glColor3f(0.15, 1.0, 0.25)
        glBegin(GL_LINES)
        glVertex2f(bx + 15, by + 75); glVertex2f(bx + 45, by + 75)
        glEnd()

        # Entry 4: YELLOW - Input Vector
        glColor3f(1.0, 0.95, 0.1)
        glBegin(GL_LINES)
        glVertex2f(bx + 15, by + 100); glVertex2f(bx + 45, by + 100)
        glEnd()

        # Entry 5: ORANGE - Physical Velocity
        glColor3f(1.0, 0.5, 0.05)
        glBegin(GL_LINES)
        glVertex2f(bx + 15, by + 125); glVertex2f(bx + 45, by + 125)
        glEnd()

        # Mini orientation compass widget in bottom right of card
        compass_cx = bx + bw - 50.0
        compass_cy = by + 75.0
        compass_r = 30.0

        glColor4f(0.2, 0.25, 0.35, 0.6)
        glLineWidth(1.0)
        glBegin(GL_LINE_LOOP)
        for i in range(16):
            th = 2.0 * math.pi * i / 16.0
            glVertex2f(compass_cx + math.cos(th) * compass_r, compass_cy + math.sin(th) * compass_r)
        glEnd()

        # Compass Needle: Camera Forward (CYAN)
        cos_c = math.cos(camera.yaw)
        sin_c = math.sin(camera.yaw)
        glColor3f(0.0, 0.85, 1.0)
        glLineWidth(2.5)
        glBegin(GL_LINES)
        glVertex2f(compass_cx, compass_cy)
        glVertex2f(compass_cx + cos_c * compass_r, compass_cy + sin_c * compass_r)
        glEnd()

        # Compass Needle: Camera Right (MAGENTA)
        glColor3f(1.0, 0.15, 0.55)
        glBegin(GL_LINES)
        glVertex2f(compass_cx, compass_cy)
        glVertex2f(compass_cx + sin_c * (compass_r * 0.8), compass_cy - cos_c * (compass_r * 0.8))
        glEnd()

        # Compass Needle: Character Facing (GREEN)
        cos_h = math.cos(character.facing_yaw)
        sin_h = math.sin(character.facing_yaw)
        glColor3f(0.15, 1.0, 0.25)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glVertex2f(compass_cx, compass_cy)
        glVertex2f(compass_cx + cos_h * (compass_r * 0.9), compass_cy + sin_h * (compass_r * 0.9))
        glEnd()
