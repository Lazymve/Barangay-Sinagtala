"""
GTA-Style Character Controller & 3D Procedural Mesh Renderer for Barangay Sinagtala 3D.
Features a complete Locomotion State Machine, decoupled variables (facing_yaw, movement_direction,
velocity, camera_orientation), rotational inertia, angular velocity damping, speed-dependent turning,
banking lean, and velocity-matched procedural 3D animation.
"""

import math
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from locomotion_states import (
    LocomotionState, LocomotionConfig, normalize_angle, angle_diff
)


def _is_pressed(keys, k) -> bool:
    if isinstance(keys, dict):
        return bool(keys.get(k, False))
    try:
        return bool(keys[k])
    except (IndexError, KeyError):
        return False


def _draw_solid_capsule(radius: float, height: float, color: tuple, quadric):
    half_h = height / 2.0
    glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [color[0], color[1], color[2], 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.35, 0.35, 0.35, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 28.0)

    # Cylinder body
    glPushMatrix()
    glTranslatef(0.0, 0.0, -half_h)
    gluCylinder(quadric, radius, radius, height, 14, 2)
    glPopMatrix()

    # Top Hemisphere dome
    glPushMatrix()
    glTranslatef(0.0, 0.0, half_h)
    gluSphere(quadric, radius, 14, 10)
    glPopMatrix()

    # Bottom Hemisphere base
    glPushMatrix()
    glTranslatef(0.0, 0.0, -half_h)
    gluSphere(quadric, radius, 14, 10)
    glPopMatrix()


def _draw_solid_ellipsoid(rx: float, ry: float, rz: float, color: tuple, quadric):
    glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [color[0], color[1], color[2], 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.2, 0.2, 0.2, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 16.0)

    glPushMatrix()
    glScalef(rx, ry, rz)
    gluSphere(quadric, 1.0, 10, 8)
    glPopMatrix()


def _draw_curved_visor(radius: float, height: float, color: tuple):
    glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [color[0], color[1], color[2], 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.75, 0.85, 0.95, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 64.0)

    num_segs = 8
    width_angle = math.pi * 0.50
    half_angle = width_angle / 2.0
    r = radius * 1.025
    half_h = height / 2.0

    glBegin(GL_QUAD_STRIP)
    for i in range(num_segs + 1):
        theta = -half_angle + width_angle * (i / float(num_segs))
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        glNormal3f(cos_t, sin_t, 0.0)
        glVertex3f(r * cos_t, r * sin_t, half_h)
        glVertex3f(r * cos_t, r * sin_t, -half_h)
    glEnd()


class CharacterGL:
    """
    GTA-style third-person player controller.
    Completely decouples character facing direction, movement direction,
    velocity, and camera orientation.
    """

    def __init__(self, x=40.0, y=36.0, z=0.0, facing_yaw=0.0):
        # 1. World Position
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

        # 2. Velocity Vector (world m/s)
        self.vx = 0.0
        self.vy = 0.0
        self.current_speed = 0.0

        # 3. Movement Direction (normalized intended vector in world space)
        self.movement_dir_x = 0.0
        self.movement_dir_y = 0.0
        self.has_movement_input = False

        # 4. Facing Direction & Rotational Inertia
        self.facing_yaw = float(facing_yaw)  # Current character orientation in radians
        self.angular_velocity = 0.0     # Rotational velocity (rad/s)
        self.banking_roll = 0.0         # Body tilt/lean when turning sharply (rad)

        # 5. Locomotion State Machine
        self.state = LocomotionState.IDLE
        self.state_time = 0.0
        self.is_aiming = False
        self.is_sprinting = False

        # 6. Animation Clocks & Parameters
        self.stride_phase = 0.0
        self.body_bounce = 0.0
        self.arm_swing = 0.0
        self.leg_lift = 0.0
        self.strafe_amount = 0.0

        # 7. Physical Dimensions
        self.radius = 0.35

        # OpenGL Quadric (created lazily or safely if GL context is active)
        try:
            self.quadric = gluNewQuadric()
            if self.quadric:
                gluQuadricNormals(self.quadric, GLU_SMOOTH)
        except Exception:
            self.quadric = None

    @property
    def heading(self):
        return self.facing_yaw

    def update(self, keys, dt: float, camera_yaw: float, is_aiming: bool, city_env):
        self.is_aiming = is_aiming
        self.state_time += dt

        # -------------------------------------------------------------
        # STEP 1: CALCULATE INTENDED MOVEMENT DIRECTION (CAMERA-RELATIVE)
        # -------------------------------------------------------------
        cos_c = math.cos(camera_yaw)
        sin_c = math.sin(camera_yaw)

        # Camera flat forward = (cos_c, sin_c)
        # Camera flat right   = (sin_c, -cos_c)  [Cross product (cos_c, sin_c, 0) x (0, 0, 1)]
        input_forward = 0.0
        input_right = 0.0

        if _is_pressed(keys, pygame.K_w) or _is_pressed(keys, pygame.K_UP):
            input_forward += 1.0
        if _is_pressed(keys, pygame.K_s) or _is_pressed(keys, pygame.K_DOWN):
            input_forward -= 1.0
        if _is_pressed(keys, pygame.K_d):
            input_right += 1.0
        if _is_pressed(keys, pygame.K_a):
            input_right -= 1.0

        raw_mag = math.hypot(input_forward, input_right)
        self.has_movement_input = raw_mag > 0.05

        if self.has_movement_input:
            norm_f = input_forward / raw_mag
            norm_r = input_right / raw_mag
            # World movement vector: forward * norm_f + right * norm_r
            self.movement_dir_x = norm_f * cos_c + norm_r * sin_c
            self.movement_dir_y = norm_f * sin_c - norm_r * cos_c
        else:
            self.movement_dir_x = 0.0
            self.movement_dir_y = 0.0

        # Sprint and Walk modifiers
        sprint_intent = bool(_is_pressed(keys, pygame.K_LSHIFT) or _is_pressed(keys, pygame.K_RSHIFT)) and not is_aiming
        walk_intent = bool(_is_pressed(keys, pygame.K_LALT) or _is_pressed(keys, pygame.K_RALT) or _is_pressed(keys, pygame.K_LCTRL)) and not is_aiming

        # Determine target speed
        if self.is_aiming:
            if input_forward < -0.1:
                target_speed = LocomotionConfig.SPEED_BACKPEDAL
            elif abs(input_right) > 0.1:
                target_speed = LocomotionConfig.SPEED_STRAFE
            else:
                target_speed = LocomotionConfig.SPEED_AIM
            self.is_sprinting = False
        elif sprint_intent and self.has_movement_input:
            target_speed = LocomotionConfig.SPEED_SPRINT
            self.is_sprinting = True
        elif walk_intent and self.has_movement_input:
            target_speed = LocomotionConfig.SPEED_WALK
            self.is_sprinting = False
        elif self.has_movement_input:
            target_speed = LocomotionConfig.SPEED_JOG
            self.is_sprinting = False
        else:
            target_speed = 0.0
            self.is_sprinting = False

        # -------------------------------------------------------------
        # STEP 2: MOMENTUM & VELOCITY DYNAMICS (WITH TURN BRAKING)
        # -------------------------------------------------------------
        if self.has_movement_input:
            target_vx = self.movement_dir_x * target_speed
            target_vy = self.movement_dir_y * target_speed

            # Detect sharp direction change (> 90 deg) relative to current velocity
            current_spd = math.hypot(self.vx, self.vy)
            if current_spd > 1.8:
                vel_angle = math.atan2(self.vy, self.vx)
                inp_angle = math.atan2(self.movement_dir_y, self.movement_dir_x)
                diff_dir = abs(angle_diff(inp_angle, vel_angle))
                if diff_dir > math.radians(95):
                    # Turn braking: momentarily apply extra friction to plant feet and pivot (GTA IV feel)
                    brake_force = LocomotionConfig.TURN_BRAKING * dt
                    new_spd = max(0.0, current_spd - brake_force)
                    self.vx = (self.vx / current_spd) * new_spd
                    self.vy = (self.vy / current_spd) * new_spd

            # Accelerate toward target velocity
            rate = LocomotionConfig.ACCELERATION * dt
            self.vx += (target_vx - self.vx) * min(1.0, rate)
            self.vy += (target_vy - self.vy) * min(1.0, rate)
        else:
            # Ground braking friction
            current_spd = math.hypot(self.vx, self.vy)
            if current_spd > 0.04:
                drop = LocomotionConfig.FRICTION * dt
                new_spd = max(0.0, current_spd - drop)
                self.vx = (self.vx / current_spd) * new_spd
                self.vy = (self.vy / current_spd) * new_spd
            else:
                self.vx = 0.0
                self.vy = 0.0

        self.current_speed = math.hypot(self.vx, self.vy)

        # -------------------------------------------------------------
        # STEP 3: WORLD POSITION UPDATE WITH CITY COLLISION
        # -------------------------------------------------------------
        raw_x = self.x + self.vx * dt
        raw_y = self.y + self.vy * dt
        if city_env is not None and hasattr(city_env, "resolve_player_collision"):
            self.x, self.y = city_env.resolve_player_collision(raw_x, raw_y, self.radius)
        else:
            self.x, self.y = raw_x, raw_y

        # -------------------------------------------------------------
        # STEP 4: SEPARATE CHARACTER FACING DIRECTION & ANGULAR INERTIA
        # -------------------------------------------------------------
        if self.is_aiming:
            # AIM MODE: Character heading is locked to Camera Yaw
            target_yaw = camera_yaw
            diff = angle_diff(target_yaw, self.facing_yaw)
            # Fast critically-damped turn to crosshair
            self.facing_yaw += diff * min(1.0, LocomotionConfig.TURN_SPEED_AIM * dt)
            self.facing_yaw = normalize_angle(self.facing_yaw)
            self.angular_velocity = 0.0
            self.banking_roll = 0.0

            # Compute lateral strafe factor (-1 for left, +1 for right)
            # Right vector = (sin_c, -cos_c)
            self.strafe_amount = (sin_c * self.vx - cos_c * self.vy) / max(0.1, LocomotionConfig.SPEED_STRAFE)
        else:
            self.strafe_amount = 0.0
            if self.current_speed > 0.18:
                # FREE-ROAM: Face the direction of actual velocity (travel direction)
                target_yaw = math.atan2(self.vy, self.vx)
                diff = angle_diff(target_yaw, self.facing_yaw)

                if self.current_speed > LocomotionConfig.SPEED_JOG + 0.5:
                    turn_resp = LocomotionConfig.TURN_SPEED_SPRINT
                elif self.current_speed > LocomotionConfig.SPEED_WALK + 0.5:
                    turn_resp = LocomotionConfig.TURN_SPEED_JOG
                else:
                    turn_resp = LocomotionConfig.TURN_SPEED_WALK

                # Angular velocity with damping
                target_ang_vel = diff * turn_resp
                self.angular_velocity += (target_ang_vel - self.angular_velocity) * min(1.0, 14.0 * dt)
                self.facing_yaw += self.angular_velocity * dt
                self.facing_yaw = normalize_angle(self.facing_yaw)

                # Banking roll lean into turns
                target_roll = -self.angular_velocity * LocomotionConfig.BANKING_STRENGTH
                target_roll = max(-LocomotionConfig.MAX_BANKING_ROLL, min(LocomotionConfig.MAX_BANKING_ROLL, target_roll))
                self.banking_roll += (target_roll - self.banking_roll) * min(1.0, 10.0 * dt)
            else:
                self.angular_velocity = 0.0
                self.banking_roll += (0.0 - self.banking_roll) * min(1.0, 12.0 * dt)

        # -------------------------------------------------------------
        # STEP 5: LOCOMOTION STATE MACHINE TRANSITIONS
        # -------------------------------------------------------------
        self._update_locomotion_state(input_forward, input_right)

        # -------------------------------------------------------------
        # STEP 6: PROCEDURAL 3D ANIMATION KINEMATICS
        # -------------------------------------------------------------
        self._update_animation_kinematics(dt, input_forward, input_right)

    def _update_locomotion_state(self, input_forward: float, input_right: float):
        old_state = self.state

        if self.is_aiming:
            if not self.has_movement_input and self.current_speed < 0.2:
                self.state = LocomotionState.AIM_IDLE
            elif input_forward < -0.2:
                self.state = LocomotionState.BACKPEDAL
            elif input_right > 0.2:
                self.state = LocomotionState.STRAFE_RIGHT
            elif input_right < -0.2:
                self.state = LocomotionState.STRAFE_LEFT
            else:
                self.state = LocomotionState.WALK
        elif self.has_movement_input:
            if old_state in (LocomotionState.IDLE, LocomotionState.STOPPING):
                if self.is_sprinting:
                    self.state = LocomotionState.SPRINT
                elif self.current_speed < 1.0:
                    self.state = LocomotionState.START_WALK
                else:
                    self.state = LocomotionState.START_JOG
            elif old_state == LocomotionState.START_WALK:
                if self.state_time < LocomotionConfig.START_TRANSITION_TIME:
                    self.state = LocomotionState.START_WALK
                else:
                    self.state = LocomotionState.WALK
            elif old_state == LocomotionState.START_JOG:
                if self.state_time < LocomotionConfig.START_TRANSITION_TIME:
                    self.state = LocomotionState.START_JOG
                else:
                    self.state = LocomotionState.JOG
            elif self.is_sprinting and self.current_speed > LocomotionConfig.SPEED_JOG:
                self.state = LocomotionState.SPRINT
            elif abs(self.angular_velocity) > 2.8 and self.current_speed > 1.8:
                self.state = LocomotionState.TURN
            elif self.current_speed > LocomotionConfig.SPEED_WALK + 0.6:
                self.state = LocomotionState.JOG
            else:
                self.state = LocomotionState.WALK
        else:
            # Releasing keys
            if self.current_speed > 0.3:
                self.state = LocomotionState.STOPPING
            else:
                self.state = LocomotionState.IDLE

        if self.state != old_state:
            self.state_time = 0.0

    def _update_animation_kinematics(self, dt: float, input_forward: float, input_right: float):
        """Advances limb stride and body bounce proportional to actual speed."""
        if self.current_speed > 0.12:
            stride_speed = 2.4 * self.current_speed
            self.stride_phase += dt * stride_speed

            # Stride kinematics
            self.stride_angle = math.sin(self.stride_phase) * (0.42 if self.is_sprinting else 0.34)
            self.leg_lift = max(0.0, math.cos(self.stride_phase)) * (0.06 if self.is_sprinting else 0.04)
            self.arm_swing = -math.sin(self.stride_phase) * (0.46 if self.is_sprinting else 0.35)
            self.body_bounce = abs(math.sin(self.stride_phase * 2.0)) * (0.035 if self.is_sprinting else 0.02)
        else:
            # Idle gentle breathing
            self.stride_phase += dt * 1.8
            self.stride_angle = 0.0
            self.leg_lift = 0.0
            self.arm_swing = 0.0
            self.body_bounce = math.sin(self.stride_phase) * 0.008

    def render_gl(self):
        """Renders the true 3D White Bean model using OpenGL transforms and materials."""
        if not self.quadric:
            self.quadric = gluNewQuadric()
            if self.quadric:
                gluQuadricNormals(self.quadric, GLU_SMOOTH)

        glPushMatrix()

        # 1. World Position
        glTranslatef(self.x, self.y, self.z)

        # 2. Character Facing Yaw
        glRotatef(math.degrees(self.facing_yaw), 0.0, 0.0, 1.0)

        # 3. Banking Lean Roll
        if self.banking_roll != 0.0:
            glRotatef(math.degrees(self.banking_roll), 1.0, 0.0, 0.0)

        # Materials
        white_pearl = (0.95, 0.95, 0.97)
        charcoal_glass = (0.09, 0.11, 0.15)
        foot_sole = (0.28, 0.30, 0.35)

        center_z = 0.58 + self.body_bounce

        # 4. Main Body Capsule
        glPushMatrix()
        glTranslatef(0.0, 0.0, center_z)

        # In sprint: forward torso lean
        if self.is_sprinting and self.current_speed > 3.0:
            glRotatef(8.0, 0.0, 1.0, 0.0)

        _draw_solid_capsule(radius=0.22, height=0.28, color=white_pearl, quadric=self.quadric)

        # Visor Band (Front +X)
        glPushMatrix()
        glTranslatef(0.0, 0.0, 0.16)
        _draw_curved_visor(radius=0.22, height=0.08, color=charcoal_glass)
        glPopMatrix()
        glPopMatrix()

        # 5. Articulated 3D Hands
        hand_dist_y = 0.32
        hand_base_z = 0.52 + self.body_bounce

        if self.is_aiming:
            # Tactical Aim Stance: Hands raised forward pointing at crosshair (+X)
            glPushMatrix()
            glTranslatef(0.30, 0.08, center_z + 0.04)
            _draw_solid_ellipsoid(0.07, 0.06, 0.06, white_pearl, self.quadric)
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.32, -0.06, center_z + 0.03)
            _draw_solid_ellipsoid(0.07, 0.06, 0.06, white_pearl, self.quadric)
            glPopMatrix()
        else:
            lh_x = math.sin(self.arm_swing) * 0.16
            lh_z = hand_base_z + math.cos(self.arm_swing) * 0.03
            glPushMatrix()
            glTranslatef(lh_x, hand_dist_y, lh_z)
            _draw_solid_ellipsoid(0.06, 0.06, 0.08, white_pearl, self.quadric)
            glPopMatrix()

            rh_x = math.sin(-self.arm_swing) * 0.16
            rh_z = hand_base_z + math.cos(-self.arm_swing) * 0.03
            glPushMatrix()
            glTranslatef(rh_x, -hand_dist_y, rh_z)
            _draw_solid_ellipsoid(0.06, 0.06, 0.08, white_pearl, self.quadric)
            glPopMatrix()

        # 6. Articulated 3D Feet
        foot_dist_y = 0.12
        foot_base_z = 0.06
        strafe_l = self.strafe_amount * 0.08 if self.is_aiming else 0.0
        strafe_r = -self.strafe_amount * 0.08 if self.is_aiming else 0.0

        # Left Foot
        lf_x = math.sin(self.stride_angle) * 0.18
        lf_z = foot_base_z + (self.leg_lift if self.stride_angle > 0 else 0.0)
        glPushMatrix()
        glTranslatef(lf_x, foot_dist_y + strafe_l, lf_z)
        _draw_solid_ellipsoid(0.11, 0.06, 0.05, foot_sole, self.quadric)
        glPopMatrix()

        # Right Foot
        rf_x = math.sin(-self.stride_angle) * 0.18
        rf_z = foot_base_z + (self.leg_lift if self.stride_angle < 0 else 0.0)
        glPushMatrix()
        glTranslatef(rf_x, -foot_dist_y + strafe_r, rf_z)
        _draw_solid_ellipsoid(0.11, 0.06, 0.05, foot_sole, self.quadric)
        glPopMatrix()

        # 7. Ground Contact Shadow
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.05, 0.07, 0.10, 0.55)

        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0.0, 0.0, 0.015)
        for i in range(13):
            th = 2.0 * math.pi * (i / 12.0)
            glVertex3f(0.32 * math.cos(th), 0.22 * math.sin(th), 0.015)
        glEnd()

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

        glPopMatrix()
