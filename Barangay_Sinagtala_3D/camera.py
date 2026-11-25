"""
GTA 6-Style Spherical Orbit Camera Boom with Camera Lag,
Dynamic FOV, Aim Zoom, and Spring-Arm Collision.
"""

import math
import pygame
from map_data import is_wall


def _is_pressed(keys, k) -> bool:
    if isinstance(keys, dict):
        return bool(keys.get(k, False))
    try:
        return bool(keys[k])
    except (IndexError, KeyError):
        return False


class CameraSystem:
    THIRD_PERSON = "THIRD_PERSON"
    FIRST_PERSON = "FIRST_PERSON"

    def __init__(self, init_angle: float = 0.0):
        self.yaw = float(init_angle)
        self.pitch = 0.0            # Vertical tilt (-0.35 looking up, +0.40 looking down)
        self.mode = self.THIRD_PERSON

        # Actual damped camera position
        self.x = 0.0
        self.y = 0.0

        # GTA 6 Boom Tuning
        self.base_dist = 1.70          # Normal third-person distance
        self.aim_dist = 1.15           # Tight over-the-shoulder aim distance
        self.shoulder_offset = 0.28    # Right shoulder bias
        self.current_dist = self.base_dist

        # Dynamic FOV (degrees)
        self.fov_base = 65.0
        self.fov_sprint = 74.0
        self.fov_aim = 54.0
        self.current_fov = self.fov_base

        # Controls & Damping
        self.rot_speed = 2.4
        self.mouse_sensitivity_x = 0.0022
        self.mouse_sensitivity_y = 0.0018
        self.cam_lag_speed = 15.0       # Exponential position damping rate

    @property
    def angle(self):
        """Returns the horizontal yaw for compatibility with raycaster."""
        return self.yaw

    def toggle_mode(self):
        if self.mode == self.THIRD_PERSON:
            self.mode = self.FIRST_PERSON
        else:
            self.mode = self.THIRD_PERSON

    def update(self, character, keys, dt: float, mouse_dx: int = 0, mouse_dy: int = 0, is_aiming: bool = False):
        # 1. Orbit Rotation (Yaw & Pitch)
        if _is_pressed(keys, pygame.K_LEFT):
            self.yaw -= self.rot_speed * dt
        if _is_pressed(keys, pygame.K_RIGHT):
            self.yaw += self.rot_speed * dt

        if mouse_dx != 0:
            self.yaw += mouse_dx * self.mouse_sensitivity_x
        if mouse_dy != 0:
            self.pitch += mouse_dy * self.mouse_sensitivity_y

        self.yaw = self.yaw % (2.0 * math.pi)
        # Clamp pitch to avoid extreme flips
        self.pitch = max(-0.35, min(0.42, self.pitch))

        # 2. Dynamic FOV Interpolation
        if is_aiming:
            target_fov = self.fov_aim
        elif character.is_sprinting and character.is_moving:
            target_fov = self.fov_sprint
        else:
            target_fov = self.fov_base

        self.current_fov += (target_fov - self.current_fov) * min(1.0, 10.0 * dt)

        # 3. Camera Positioning
        if self.mode == self.FIRST_PERSON:
            self.x = character.x
            self.y = character.y
            self.current_dist = 0.0
        else:
            # Over-the-shoulder target distance
            target_boom_dist = self.aim_dist if is_aiming else self.base_dist

            cos_a = math.cos(self.yaw)
            sin_a = math.sin(self.yaw)

            # Behind vector & Right-shoulder vector
            back_x = -cos_a
            back_y = -sin_a
            right_x = -sin_a
            right_y = cos_a

            # Spring-arm collision: raycast check from character outward
            safe_dist = self._spring_arm_raycast(
                character.x, character.y,
                back_x, back_y,
                right_x, right_y,
                target_boom_dist, self.shoulder_offset
            )

            # Interpolate boom distance
            self.current_dist += (safe_dist - self.current_dist) * min(1.0, 18.0 * dt)
            ratio = max(0.1, self.current_dist / self.base_dist)
            actual_shoulder = self.shoulder_offset * ratio

            ideal_x = character.x + back_x * self.current_dist + right_x * actual_shoulder
            ideal_y = character.y + back_y * self.current_dist + right_y * actual_shoulder

            # Physical Camera Lag: smooth damping towards ideal position
            # When player turns or accelerates, camera lags slightly creating weight
            lag_rate = min(1.0, self.cam_lag_speed * dt)
            if self.x == 0.0 and self.y == 0.0:
                self.x = ideal_x
                self.y = ideal_y
            else:
                self.x += (ideal_x - self.x) * lag_rate
                self.y += (ideal_y - self.y) * lag_rate

    def _spring_arm_raycast(self, start_x: float, start_y: float,
                            back_x: float, back_y: float,
                            right_x: float, right_y: float,
                            max_dist: float, shoulder: float) -> float:
        steps = 26
        for i in range(1, steps + 1):
            t = i / float(steps)
            dist = max_dist * t
            sh = shoulder * t
            test_x = start_x + back_x * dist + right_x * sh
            test_y = start_y + back_y * dist + right_y * sh
            if is_wall(test_x, test_y):
                return max(0.35, max_dist * ((i - 1) / float(steps)) - 0.15)
        return max_dist
