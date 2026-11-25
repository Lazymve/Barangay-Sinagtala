"""
Locomotion States and Centralized Tuning Parameters for Barangay Sinagtala 3D.
Inspired by the physics and camera philosophy of GTA III, IV, and V.
"""

import math
from enum import Enum


class LocomotionState(Enum):
    IDLE = "IDLE"
    START_WALK = "START_WALK"
    WALK = "WALK"
    START_JOG = "START_JOG"
    JOG = "JOG"
    SPRINT = "SPRINT"
    TURN = "TURN"
    STOPPING = "STOPPING"
    STRAFE_LEFT = "STRAFE_LEFT"
    STRAFE_RIGHT = "STRAFE_RIGHT"
    BACKPEDAL = "BACKPEDAL"
    AIM_IDLE = "AIM_IDLE"


class LocomotionConfig:
    """Centralized tuning parameters for movement physics, rotation, and animation."""
    # Speeds (m/s)
    SPEED_WALK = 2.0
    SPEED_JOG = 4.2
    SPEED_SPRINT = 7.4
    SPEED_AIM = 2.2
    SPEED_BACKPEDAL = 2.0
    SPEED_STRAFE = 2.4

    # Acceleration and Friction (m/s^2)
    ACCELERATION = 14.0
    FRICTION = 16.0
    TURN_BRAKING = 18.0         # Extra braking when changing direction > 90 deg

    # Rotational Responsiveness (rad/s)
    TURN_SPEED_WALK = 14.0       # Snappy at low speeds (GTA V)
    TURN_SPEED_JOG = 9.5         # Natural rotation at medium speed
    TURN_SPEED_SPRINT = 5.5      # Wide turning radius at sprint (GTA IV momentum)
    TURN_SPEED_AIM = 22.0        # Rapid lock to crosshair

    # Banking Tilt (radians per angular velocity)
    BANKING_STRENGTH = 0.08
    MAX_BANKING_ROLL = 0.22      # Max ~12.5 degrees body lean

    # Timers (seconds)
    START_TRANSITION_TIME = 0.14
    STOP_TRANSITION_TIME = 0.22


class CameraConfig:
    """Centralized tuning parameters for the GTA chase camera boom."""
    DIST_BASE = 3.5
    DIST_AIM = 1.95
    SHOULDER_BASE = 0.38        # Shift toward character's right shoulder
    SHOULDER_AIM = 0.48
    HEIGHT_BASE = 0.88          # Pivot height above character feet

    # Dynamic FOV
    FOV_BASE = 65.0
    FOV_SPRINT = 74.0
    FOV_AIM = 50.0

    # Sensitivity and Damping
    MOUSE_SENS_X = 0.0024
    MOUSE_SENS_Y = 0.0020
    ROT_KEY_SPEED = 2.4
    FOLLOW_SMOOTH_TIME = 0.08   # Spatial follow critically-damped spring time
    ENABLE_AUTO_RECENTER = False  # Toggle for legacy auto-recenter (default off)

    # True GTA Chase Camera Parameters
    CHASE_SPEED_WALK = 2.4      # Chase yaw follow speed while walking (rad/s)
    CHASE_SPEED_JOG = 3.4       # Chase yaw follow speed while jogging (rad/s)
    CHASE_SPEED_SPRINT = 4.2    # Chase yaw follow speed while sprinting (rad/s)
    MANUAL_HOLD_TIME = 0.60     # Seconds of manual hold after touching mouse before resuming chase
    # Automatic recentering parameters (GTA V style)
    RECENTER_DELAY = 2.0           # Seconds of no mouse input before recenter starts
    RECENTER_MIN_SPEED = 0.2       # Minimum character speed to trigger recenter
    RECENTER_DEADZONE = 0.1        # Minimum yaw diff before recenter engages (radians)
    RECENTER_SPEED = 0.85          # Gentle recenter turn speed (rad/s)



def normalize_angle(angle: float) -> float:
    """Normalizes an angle to [0, 2*pi)."""
    return angle % (2.0 * math.pi)


def angle_diff(target: float, current: float) -> float:
    """Returns the shortest signed difference between two angles in [-pi, pi]."""
    return (target - current + math.pi) % (2.0 * math.pi) - math.pi


def smooth_damp(current: float, target: float, current_velocity: float,
                smooth_time: float, dt: float, max_speed: float = float("inf")) -> tuple:
    """
    Critically damped spring-damper interpolation (Game Programming Gems / Unity SmoothDamp).
    Returns (new_position, new_velocity).
    """
    if smooth_time <= 0.0001:
        return target, 0.0

    omega = 2.0 / smooth_time
    x = omega * dt
    exp = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)

    change = current - target
    original_to = target

    # Clamp maximum speed
    max_change = max_speed * smooth_time
    change = max(-max_change, min(max_change, change))
    target = current - change

    temp = (current_velocity + omega * change) * dt
    new_velocity = (current_velocity - omega * temp) * exp
    output = target + (change + temp) * exp

    # Prevent overshooting
    if (original_to - current > 0.0) == (output > original_to):
        output = original_to
        new_velocity = (output - original_to) / dt

    return output, new_velocity
