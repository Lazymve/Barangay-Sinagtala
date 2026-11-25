"""
GTA-Style Character Controller for Barangay Sinagtala 3D.
Features momentum & friction physics, 3-tier locomotion (Walk/Jog/Sprint),
and dual-mode locomotion (Free-Roam rotation vs. Combat Aim Strafing).
"""

import math
import pygame
from map_data import is_wall, PLAYER_START_X, PLAYER_START_Y
from model_3d import WhiteBean3DModel


def _is_pressed(keys, k) -> bool:
    if isinstance(keys, dict):
        return bool(keys.get(k, False))
    try:
        return bool(keys[k])
    except (IndexError, KeyError):
        return False


class BeanCharacter:
    def __init__(self, x=PLAYER_START_X, y=PLAYER_START_Y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.heading = 0.0          # Current facing angle in radians
        self.banking_roll = 0.0     # Lean angle when turning sharply

        # 3-Tier Locomotion Speeds
        self.speed_walk = 1.9
        self.speed_jog = 3.6
        self.speed_sprint = 6.2

        # Momentum Physics tuning
        self.accel = 16.0           # Acceleration rate (units/s^2)
        self.friction = 18.0        # Braking friction (units/s^2)
        self.turn_speed = 12.0      # Free-roam angular slerp rate
        self.radius = 0.22          # Collision radius

        # State flags
        self.is_moving = False
        self.is_sprinting = False
        self.is_aiming = False
        self.current_speed = 0.0
        self.anim_time = 0.0
        self.strafe_side = 0.0

        self.model_3d = WhiteBean3DModel()

    def update(self, keys, dt: float, camera_angle: float, is_aiming: bool = False):
        self.is_aiming = is_aiming
        self.is_sprinting = bool(_is_pressed(keys, pygame.K_LSHIFT) or _is_pressed(keys, pygame.K_RSHIFT)) and not is_aiming

        # Determine target speed
        if self.is_aiming:
            target_max_speed = self.speed_walk * 1.15
        elif self.is_sprinting:
            target_max_speed = self.speed_sprint
        else:
            target_max_speed = self.speed_jog

        # 1. Compute Desired Input Direction relative to camera yaw
        cos_c = math.cos(camera_angle)
        sin_c = math.sin(camera_angle)

        input_x = 0.0
        input_y = 0.0

        if _is_pressed(keys, pygame.K_w) or _is_pressed(keys, pygame.K_UP):
            input_x += cos_c
            input_y += sin_c
        if _is_pressed(keys, pygame.K_s) or _is_pressed(keys, pygame.K_DOWN):
            input_x -= cos_c
            input_y -= sin_c
        if _is_pressed(keys, pygame.K_d):
            input_x -= sin_c
            input_y += cos_c
        if _is_pressed(keys, pygame.K_a):
            input_x += sin_c
            input_y -= cos_c

        input_mag = math.hypot(input_x, input_y)

        # 2. Momentum & Friction Physics
        if input_mag > 0.05:
            # Accelerate in input direction
            desired_vx = (input_x / input_mag) * target_max_speed
            desired_vy = (input_y / input_mag) * target_max_speed

            # Exponential acceleration
            rate = self.accel * dt
            self.vx += (desired_vx - self.vx) * min(1.0, rate)
            self.vy += (desired_vy - self.vy) * min(1.0, rate)
        else:
            # Decelerate with ground braking friction
            speed = math.hypot(self.vx, self.vy)
            if speed > 0.02:
                drop = self.friction * dt
                new_speed = max(0.0, speed - drop)
                self.vx = (self.vx / speed) * new_speed
                self.vy = (self.vy / speed) * new_speed
            else:
                self.vx = 0.0
                self.vy = 0.0

        self.current_speed = math.hypot(self.vx, self.vy)
        self.is_moving = self.current_speed > 0.12

        # 3. Position update with smooth collision sliding
        dx = self.vx * dt
        dy = self.vy * dt
        if abs(dx) > 0.00001 or abs(dy) > 0.00001:
            self._move_with_collision(dx, dy)

        # 4. Heading & Rotation Logic (Dual-Mode)
        if self.is_aiming:
            # GTA Aim Mode: Snaps heading directly to camera crosshair
            diff = (camera_angle - self.heading + math.pi) % (2.0 * math.pi) - math.pi
            self.heading += diff * min(1.0, 22.0 * dt)
            self.heading = self.heading % (2.0 * math.pi)
            self.banking_roll = 0.0

            # Calculate lateral strafe velocity component
            # Forward dot = vx*cos_c + vy*sin_c, Right dot = vx*(-sin_c) + vy*cos_c
            self.strafe_side = (-sin_c * self.vx + cos_c * self.vy) / max(0.1, target_max_speed)
        else:
            self.strafe_side = 0.0
            if self.is_moving:
                # Free-Roam Mode: Rotate towards velocity vector
                target_heading = math.atan2(self.vy, self.vx)
                diff = (target_heading - self.heading + math.pi) % (2.0 * math.pi) - math.pi
                turn_rate = diff * min(1.0, self.turn_speed * dt)
                self.heading += turn_rate
                self.heading = self.heading % (2.0 * math.pi)

                # Banking roll into turns (GTA motorcycle/runner lean effect)
                target_roll = -turn_rate * 0.15
                self.banking_roll += (target_roll - self.banking_roll) * min(1.0, 10.0 * dt)
            else:
                self.banking_roll += (0.0 - self.banking_roll) * min(1.0, 12.0 * dt)

        # 5. Stride Animation speed linked to actual movement speed
        if self.is_moving:
            stride_rate = 2.4 * self.current_speed
            self.anim_time += dt * stride_rate
        else:
            self.anim_time = 0.0

    def _move_with_collision(self, dx: float, dy: float):
        # Sliding X collision
        new_x = self.x + dx
        cx = new_x + (self.radius if dx > 0 else -self.radius)
        if not is_wall(cx, self.y):
            self.x = new_x
        else:
            self.vx *= 0.35  # Wall friction damp

        # Sliding Y collision
        new_y = self.y + dy
        cy = new_y + (self.radius if dy > 0 else -self.radius)
        if not is_wall(self.x, cy):
            self.y = new_y
        else:
            self.vy *= 0.35  # Wall friction damp

    def get_world_polygons(self) -> list:
        return self.model_3d.build_world_polygons(
            self.x, self.y, self.heading, self.is_moving, self.anim_time,
            is_aiming=self.is_aiming, banking_roll=self.banking_roll,
            strafe_side=self.strafe_side
        )
