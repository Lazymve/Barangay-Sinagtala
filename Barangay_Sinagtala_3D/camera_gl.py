"""
GTA IV / V-Style Third-Person Orbital Camera Boom with Intelligent Recentering
and Critically-Damped Spring-Arm for PyOpenGL in Barangay Sinagtala 3D.
"""

import math
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from locomotion_states import (
    CameraConfig, LocomotionConfig, normalize_angle, angle_diff, smooth_damp
)


def _is_pressed(keys, k) -> bool:
    if isinstance(keys, dict):
        return bool(keys.get(k, False))
    try:
        return bool(keys[k])
    except (IndexError, KeyError):
        return False


class CameraGL:
    THIRD_PERSON = "THIRD_PERSON"
    FIRST_PERSON = "FIRST_PERSON"

    def __init__(self, init_yaw: float = 0.0, distance: float = None):
        # 1. Orientation Spherical Coordinates
        self.yaw = float(init_yaw)
        self.pitch = 0.18           # Slight downward tilt (radians)
        self.mode = self.THIRD_PERSON

        # 2. Camera Eye Position & Velocity (for smooth_damp)
        self.eye_x = 40.0
        self.eye_y = 36.0
        self.eye_z = 2.5
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.vel_z = 0.0

        # 3. Look-At Target Position & Velocity
        self.target_x = 40.0
        self.target_y = 40.0
        self.target_z = 0.95
        self.target_vel_x = 0.0
        self.target_vel_y = 0.0
        self.target_vel_z = 0.0

        # 4. Boom Tuning & Spring-Arm
        self.current_dist = float(distance) if distance is not None else CameraConfig.DIST_BASE
        self.dist_velocity = 0.0

        # 5. Dynamic FOV
        self.current_fov = CameraConfig.FOV_BASE
        self.fov_velocity = 0.0

        # 6. Intelligent Camera Recentering (GTA V Style)
        self.time_since_mouse_input = 0.0
        self.auto_recentering = False
        self.enable_auto_recenter = CameraConfig.ENABLE_AUTO_RECENTER

    def toggle_auto_recenter(self) -> bool:
        self.enable_auto_recenter = not self.enable_auto_recenter
        self.time_since_mouse_input = 0.0
        self.auto_recentering = False
        return self.enable_auto_recenter

    @property
    def recentering_timer(self):
        return self.time_since_mouse_input

    def set_angles(self, yaw: float = None, pitch: float = None):
        if yaw is not None:
            self.yaw = normalize_angle(float(yaw))
        if pitch is not None:
            self.pitch = max(-0.40, min(0.65, float(pitch)))
        self.time_since_mouse_input = 0.0
        self.auto_recentering = False

    def handle_mouse_movement(self, dx: float, dy: float):
        if dx != 0.0 or dy != 0.0:
            self.yaw = normalize_angle(self.yaw + dx * CameraConfig.MOUSE_SENS_X)
            self.pitch = max(-0.40, min(0.65, self.pitch + dy * CameraConfig.MOUSE_SENS_Y))
            self.time_since_mouse_input = 0.0
            self.auto_recentering = False

    def toggle_mode(self):
        if self.mode == self.THIRD_PERSON:
            self.mode = self.FIRST_PERSON
        else:
            self.mode = self.THIRD_PERSON

    def update(self, character, keys, dt: float, mouse_dx: int = 0, mouse_dy: int = 0, is_aiming: bool = False, city_env = None):
        # -------------------------------------------------------------
        # STEP 1: ORBIT ROTATION & MOUSE INPUT TRACKING
        # -------------------------------------------------------------
        has_manual_rotation = False

        if _is_pressed(keys, pygame.K_LEFT):
            self.yaw -= CameraConfig.ROT_KEY_SPEED * dt
            has_manual_rotation = True
        if _is_pressed(keys, pygame.K_RIGHT):
            self.yaw += CameraConfig.ROT_KEY_SPEED * dt
            has_manual_rotation = True

        if mouse_dx != 0:
            self.yaw += mouse_dx * CameraConfig.MOUSE_SENS_X
            has_manual_rotation = True
        if mouse_dy != 0:
            self.pitch += mouse_dy * CameraConfig.MOUSE_SENS_Y
            has_manual_rotation = True

        if has_manual_rotation:
            self.time_since_mouse_input = 0.0
            self.auto_recentering = False
        else:
            self.time_since_mouse_input += dt

        self.yaw = normalize_angle(self.yaw)
        # Pitch clamped between [-0.40 looking up, +0.65 looking down]
        self.pitch = max(-0.40, min(0.65, self.pitch))

        # -------------------------------------------------------------
        # STEP 2: CONFIGURABLE GENTLE AUTO-RECENTERING (GTA V STYLE)
        # -------------------------------------------------------------
        # When enabled and moving forward for RECENTER_DELAY with zero mouse input:
        # Camera gently eases behind character's movement trajectory
        cam_fwd_x = math.cos(self.yaw)
        cam_fwd_y = math.sin(self.yaw)
        spd = max(0.1, character.current_speed)
        forward_dot = (character.vx * cam_fwd_x + character.vy * cam_fwd_y) / spd

        if (
            self.enable_auto_recenter
            and self.mode == self.THIRD_PERSON
            and not is_aiming
            and not has_manual_rotation
            and character.current_speed > CameraConfig.RECENTER_MIN_SPEED
            and forward_dot > 0.4
            and self.time_since_mouse_input > CameraConfig.RECENTER_DELAY
        ):
            move_angle = math.atan2(character.vy, character.vx)
            diff_recenter = angle_diff(move_angle, self.yaw)
            if abs(diff_recenter) > CameraConfig.RECENTER_DEADZONE:
                self.auto_recentering = True
                recenter_step = diff_recenter * min(1.0, CameraConfig.RECENTER_SPEED * dt)
                self.yaw = normalize_angle(self.yaw + recenter_step)
            else:
                self.auto_recentering = False
        else:
            self.auto_recentering = False

        # -------------------------------------------------------------
        # STEP 3: DYNAMIC FOV INTERPOLATION
        # -------------------------------------------------------------
        if is_aiming:
            target_fov = CameraConfig.FOV_AIM
        elif character.is_sprinting and character.current_speed > 4.0:
            target_fov = CameraConfig.FOV_SPRINT
        else:
            target_fov = CameraConfig.FOV_BASE

        self.current_fov, self.fov_velocity = smooth_damp(
            self.current_fov, target_fov, self.fov_velocity, 0.16, dt
        )

        # -------------------------------------------------------------
        # STEP 4: ELEVATED LOOK-AT TARGET SMOOTH DAMPING
        # -------------------------------------------------------------
        pivot_z = character.z + CameraConfig.HEIGHT_BASE
        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)

        # Right vector relative to camera yaw: (sin_yaw, -cos_yaw)
        right_x = sin_yaw
        right_y = -cos_yaw

        if self.mode == self.FIRST_PERSON:
            # First person eye placement directly at character head
            self.eye_x = character.x
            self.eye_y = character.y
            self.eye_z = character.z + 0.76

            cos_p = math.cos(self.pitch)
            sin_p = math.sin(self.pitch)
            self.target_x = self.eye_x + cos_p * cos_yaw
            self.target_y = self.eye_y + cos_p * sin_yaw
            self.target_z = self.eye_z - sin_p
        else:
            # Third Person GTA Boom
            shoulder = CameraConfig.SHOULDER_AIM if is_aiming else CameraConfig.SHOULDER_BASE
            target_boom_dist = CameraConfig.DIST_AIM if is_aiming else CameraConfig.DIST_BASE

            # Look-at point slightly shifted toward right shoulder
            ideal_target_x = character.x + right_x * (shoulder * 0.40)
            ideal_target_y = character.y + right_y * (shoulder * 0.40)
            ideal_target_z = pivot_z

            # Critically-damped target following (eliminates high-frequency jitter)
            self.target_x, self.target_vel_x = smooth_damp(self.target_x, ideal_target_x, self.target_vel_x, CameraConfig.FOLLOW_SMOOTH_TIME, dt)
            self.target_y, self.target_vel_y = smooth_damp(self.target_y, ideal_target_y, self.target_vel_y, CameraConfig.FOLLOW_SMOOTH_TIME, dt)
            self.target_z, self.target_vel_z = smooth_damp(self.target_z, ideal_target_z, self.target_vel_z, CameraConfig.FOLLOW_SMOOTH_TIME, dt)

            # -------------------------------------------------------------
            # STEP 5: SPRING-ARM COLLISION & POSITIONING
            # -------------------------------------------------------------
            cos_pitch = math.cos(self.pitch)
            sin_pitch = math.sin(self.pitch)

            # Behind vector from target: (-cos_yaw * cos_pitch, -sin_yaw * cos_pitch, sin_pitch)
            back_x = -cos_yaw * cos_pitch
            back_y = -sin_yaw * cos_pitch
            up_z = sin_pitch

            # Ideal eye position before obstacle collision
            ideal_eye_x = self.target_x + back_x * target_boom_dist + right_x * shoulder
            ideal_eye_y = self.target_y + back_y * target_boom_dist + right_y * shoulder
            ideal_eye_z = self.target_z + up_z * target_boom_dist + 0.22

            # Raycast spring-arm from target out to ideal camera position
            if city_env is not None and hasattr(city_env, "raycast_camera_spring_arm"):
                start_p = (self.target_x, self.target_y, self.target_z)
                end_p = (ideal_eye_x, ideal_eye_y, ideal_eye_z)
                t_hit = city_env.raycast_camera_spring_arm(start_p, end_p)
            else:
                t_hit = 1.0

            # If obstacle hit, pull boom in with safety buffer
            if t_hit < 0.999:
                safe_dist = target_boom_dist * max(0.20, t_hit * 0.88)
            else:
                safe_dist = target_boom_dist

            self.current_dist, self.dist_velocity = smooth_damp(
                self.current_dist, safe_dist, self.dist_velocity, 0.05, dt
            )

            # Actual eye position computed directly from tracked target and safe boom distance.
            # Anchoring the eye directly to the tracked target eliminates rotational lag,
            # providing responsive 1:1 mouse orbit while spatial following remains silky smooth.
            scaled_shoulder = shoulder * (self.current_dist / target_boom_dist)
            self.eye_x = self.target_x + back_x * self.current_dist + right_x * scaled_shoulder
            self.eye_y = self.target_y + back_y * self.current_dist + right_y * scaled_shoulder
            self.eye_z = self.target_z + up_z * self.current_dist + 0.22

    def apply_view(self):
        """Sets up the OpenGL ModelView matrix using gluLookAt."""
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            self.eye_x, self.eye_y, self.eye_z,
            self.target_x, self.target_y, self.target_z,
            0.0, 0.0, 1.0  # Up vector is +Z
        )
