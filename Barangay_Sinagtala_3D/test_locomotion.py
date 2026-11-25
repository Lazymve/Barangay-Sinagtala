"""
Comprehensive Automated Test Suite for GTA-Style Locomotion and Camera System
Tests Scenarios A through F, Auto-Recentering, Decoupled Vectors, Collision, and Framerate Independence.
"""
import sys
import os
import math
import numpy as np

# Ensure path includes Barangay_Sinagtala_3D
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from locomotion_states import LocomotionState, LocomotionConfig, CameraConfig, normalize_angle, angle_diff
from character_gl import CharacterGL
from camera_gl import CameraGL

class MockCollider:
    def __init__(self, boxes=None):
        self.boxes = boxes or []  # list of (min_x, min_y, max_x, max_y)

    def resolve_player_collision(self, px: float, py: float, radius: float) -> tuple:
        resolved_x = px
        resolved_y = py
        for min_x, min_y, max_x, max_y in self.boxes:
            closest_x = max(min_x, min(resolved_x, max_x))
            closest_y = max(min_y, min(resolved_y, max_y))
            diff_x = resolved_x - closest_x
            diff_y = resolved_y - closest_y
            dist = math.hypot(diff_x, diff_y)
            if dist < radius:
                if dist > 0.0001:
                    push = radius - dist
                    resolved_x += (diff_x / dist) * push
                    resolved_y += (diff_y / dist) * push
                else:
                    resolved_x = min_x - radius
        return resolved_x, resolved_y

def make_keys(pressed=None):
    import pygame
    keys = {k: False for k in [
        pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d,
        pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
        pygame.K_LSHIFT, pygame.K_RSHIFT
    ]}
    if pressed:
        for k in pressed:
            keys[k] = True
    return keys

def test_scenario_a_walk_forward():
    print("[TEST] Scenario A: Walk forward transition & velocity matching...")
    import pygame
    char = CharacterGL(x=10.0, y=10.0, facing_yaw=0.0)
    camera = CameraGL(distance=CameraConfig.DIST_BASE)
    camera.set_angles(yaw=0.0, pitch=15.0)

    # Initial state
    assert char.state == LocomotionState.IDLE, f"Expected IDLE, got {char.state}"
    assert char.current_speed == 0.0

    # Press W for 0.08s (5 frames, within START_TRANSITION_TIME)
    dt = 1.0 / 60.0
    keys_w = make_keys([pygame.K_w])
    for _ in range(5):
        char.update(keys_w, dt, camera.yaw, False, MockCollider())
    
    assert char.state in (LocomotionState.START_WALK, LocomotionState.WALK), f"Expected START_WALK or WALK, got {char.state}"
    assert char.current_speed > 0.0
    # Walk forward along camera yaw 0 (world +X)
    assert abs(normalize_angle(char.facing_yaw - 0.0)) < 0.1, f"Character should face camera forward (0 rad), got {char.facing_yaw}"
    
    # Continue moving for 1s
    for _ in range(60):
        char.update(keys_w, dt, camera.yaw, False, MockCollider())
    
    assert char.state in (LocomotionState.WALK, LocomotionState.JOG), f"Expected WALK or JOG, got {char.state}"
    assert abs(char.current_speed - LocomotionConfig.SPEED_JOG) < 0.2
    assert char.x > 10.0, "Character should have moved forward in +X"
    print("  -> Scenario A PASSED!")

def test_scenario_b_sprint_and_turn():
    print("[TEST] Scenario B: Sprint and turn left (banking & speed-dependent turning)...")
    import pygame
    char = CharacterGL(x=10.0, y=10.0, facing_yaw=0.0)
    camera = CameraGL()
    camera.set_angles(yaw=0.0, pitch=15.0)
    dt = 1.0 / 60.0

    # Accelerate to sprint (W + Shift)
    keys_sprint = make_keys([pygame.K_w, pygame.K_LSHIFT])
    for _ in range(90): # 1.5s
        char.update(keys_sprint, dt, camera.yaw, False, MockCollider())
    
    assert char.state == LocomotionState.SPRINT, f"Expected SPRINT, got {char.state}"
    assert char.current_speed > LocomotionConfig.SPEED_JOG, f"Expected > {LocomotionConfig.SPEED_JOG}, got {char.current_speed}"

    # Now hold A while sprinting (turn left: desired angle is +pi/2)
    keys_turn = make_keys([pygame.K_w, pygame.K_a, pygame.K_LSHIFT])
    char.update(keys_turn, dt, camera.yaw, False, MockCollider())
    
    # State should reflect turning or sprint
    assert char.state in (LocomotionState.TURN, LocomotionState.SPRINT), f"Got {char.state}"
    
    # Run a few frames and verify bank roll is activated
    bank_detected = False
    keys_turn_sharp = make_keys([pygame.K_a, pygame.K_LSHIFT])
    for _ in range(30):
        char.update(keys_turn_sharp, dt, camera.yaw, False, MockCollider())
        if abs(char.banking_roll) > 0.01:
            bank_detected = True
    
    assert bank_detected, f"Expected non-zero banking roll during high-speed turn, got {char.banking_roll}"
    print(f"  -> Scenario B PASSED! (Peak banking roll: {char.banking_roll:.3f} rad)")

def test_scenario_c_walk_backward_s_key():
    print("[TEST] Scenario C: Pressing S in Free-Roam (character turns around, camera does NOT snap)...")
    import pygame
    char = CharacterGL(x=10.0, y=10.0, facing_yaw=0.0)
    camera = CameraGL()
    camera.set_angles(yaw=0.0, pitch=15.0)
    dt = 1.0 / 60.0

    initial_cam_yaw = camera.yaw
    initial_cam_pitch = camera.pitch

    # Press S (backward relative to camera) for 0.7s (42 frames) to complete natural pivot
    keys_s = make_keys([pygame.K_s])
    for _ in range(45):
        char.update(keys_s, dt, camera.yaw, False, MockCollider())
        camera.update(char, keys_s, dt, 0, 0, False, None)
    
    # Character travel angle should be camera.yaw + pi (i.e. -X direction)
    expected_facing = normalize_angle(initial_cam_yaw + math.pi)
    yaw_diff = abs(angle_diff(char.facing_yaw, expected_facing))
    assert yaw_diff < 0.35, f"Character should have turned around toward camera backward ({expected_facing:.2f}), got {char.facing_yaw:.2f} (diff {yaw_diff:.2f})"
    
    # Crucial: camera yaw must NOT have changed unexpectedly (it shouldn't snap 180 degrees!)
    assert abs(angle_diff(camera.yaw, initial_cam_yaw)) < 0.05, f"Camera yaw snapped! Was {initial_cam_yaw}, now {camera.yaw}"
    assert abs(camera.pitch - initial_cam_pitch) < 0.05, f"Camera pitch changed! Was {initial_cam_pitch}, now {camera.pitch}"
    print("  -> Scenario C PASSED! No camera snapping, character smoothly pivots.")

def test_scenario_d_camera_rotation_while_stationary():
    print("[TEST] Scenario D: Stationary camera rotation decoupling...")
    import pygame
    char = CharacterGL(x=10.0, y=10.0, facing_yaw=0.0)
    camera = CameraGL()
    camera.set_angles(yaw=0.0, pitch=15.0)
    dt = 1.0 / 60.0

    initial_char_yaw = char.facing_yaw

    # Mouse moves: orbit camera yaw by +90 degrees (pi/2)
    camera.handle_mouse_movement(dx=100.0, dy=0.0)
    empty_keys = make_keys([])
    for _ in range(10):
        char.update(empty_keys, dt, camera.yaw, False, MockCollider())
        camera.update(char, empty_keys, dt, 0, 0, False, None)
    
    # Character facing direction MUST NOT rotate just because the camera orbited!
    assert abs(angle_diff(char.facing_yaw, initial_char_yaw)) < 0.001, f"Character turned with camera while idle! Was {initial_char_yaw}, now {char.facing_yaw}"
    assert abs(angle_diff(camera.yaw, initial_char_yaw)) > 0.1, "Camera did not orbit"

    # Now press W: character should move toward the NEW camera yaw
    keys_w = make_keys([pygame.K_w])
    for _ in range(40):
        char.update(keys_w, dt, camera.yaw, False, MockCollider())
    
    new_facing_diff = abs(angle_diff(char.facing_yaw, camera.yaw))
    assert new_facing_diff < 0.25, f"Character should face camera forward ({camera.yaw:.2f}), got {char.facing_yaw:.2f}"
    print("  -> Scenario D PASSED! Stationary camera orbits without turning character.")

def test_scenario_e_combat_aim_mode():
    print("[TEST] Scenario E: Combat aim mode (RMB, strafing, backpedaling, locked facing)...")
    import pygame
    char = CharacterGL(x=10.0, y=10.0, facing_yaw=0.0)
    camera = CameraGL()
    camera.set_angles(yaw=0.5, pitch=10.0)
    dt = 1.0 / 60.0

    # RMB Aiming idle (snap to crosshair over ~0.2s)
    for _ in range(12):
        char.update(make_keys([]), dt, camera.yaw, True, MockCollider())
    assert char.state == LocomotionState.AIM_IDLE, f"Expected AIM_IDLE, got {char.state}"
    assert abs(angle_diff(char.facing_yaw, camera.yaw)) < 0.01, "Facing yaw should lock to camera yaw when aiming"

    # Strafe Left (A + RMB)
    keys_a = make_keys([pygame.K_a])
    for _ in range(15):
        char.update(keys_a, dt, camera.yaw, True, MockCollider())
    assert char.state == LocomotionState.STRAFE_LEFT, f"Expected STRAFE_LEFT, got {char.state}"
    # Still facing camera yaw!
    assert abs(angle_diff(char.facing_yaw, camera.yaw)) < 0.01, "Facing yaw must remain locked during strafe"

    # Strafe Right (D + RMB)
    keys_d = make_keys([pygame.K_d])
    for _ in range(15):
        char.update(keys_d, dt, camera.yaw, True, MockCollider())
    assert char.state == LocomotionState.STRAFE_RIGHT, f"Expected STRAFE_RIGHT, got {char.state}"
    assert abs(angle_diff(char.facing_yaw, camera.yaw)) < 0.01

    # Backpedal (S + RMB)
    keys_s = make_keys([pygame.K_s])
    for _ in range(15):
        char.update(keys_s, dt, camera.yaw, True, MockCollider())
    assert char.state == LocomotionState.BACKPEDAL, f"Expected BACKPEDAL, got {char.state}"
    assert abs(angle_diff(char.facing_yaw, camera.yaw)) < 0.01
    print("  -> Scenario E PASSED! Aim mode strafing and backpedaling verified.")

def test_scenario_f_sudden_stopping():
    print("[TEST] Scenario F: Sudden stop with friction deceleration...")
    import pygame
    char = CharacterGL(x=10.0, y=10.0, facing_yaw=0.0)
    camera = CameraGL()
    dt = 1.0 / 60.0

    # Run up to full jog speed
    keys_w = make_keys([pygame.K_w])
    for _ in range(60):
        char.update(keys_w, dt, camera.yaw, False, MockCollider())
    assert char.current_speed > 3.0

    # Release all keys
    empty_keys = make_keys([])
    char.update(empty_keys, dt, camera.yaw, False, MockCollider())
    assert char.state == LocomotionState.STOPPING, f"Expected STOPPING, got {char.state}"
    
    # Wait until fully stopped
    for _ in range(45):
        char.update(empty_keys, dt, camera.yaw, False, MockCollider())
    
    assert char.state == LocomotionState.IDLE, f"Expected IDLE after stop, got {char.state}"
    assert char.current_speed == 0.0
    print("  -> Scenario F PASSED! Smooth stopping transition verified.")

def test_camera_relative_a_and_d():
    print("[TEST] Bug 1 Verification: A=LEFT and D=RIGHT at 0°, 90°, 180°, 270° in Free-Roam & Aim Mode...")
    import pygame
    test_angles = [
        (0.0, "0 deg (East, +X)"),
        (math.pi * 0.5, "90 deg (North, +Y)"),
        (math.pi, "180 deg (West, -X)"),
        (math.pi * 1.5, "270 deg (South, -Y)")
    ]
    dt = 1.0 / 60.0

    for yaw, desc in test_angles:
        # Camera Forward = (cos(yaw), sin(yaw))
        # Camera Right   = (sin(yaw), -cos(yaw))
        # Camera Left    = (-sin(yaw), cos(yaw))
        cam_right = (math.sin(yaw), -math.cos(yaw))
        cam_left = (-math.sin(yaw), math.cos(yaw))

        for is_aiming in [False, True]:
            mode_str = "Aim Mode" if is_aiming else "Free-Roam"

            # 1. Test D Key (Must move RIGHT relative to camera)
            char_d = CharacterGL(x=50.0, y=50.0, facing_yaw=yaw)
            keys_d = make_keys([pygame.K_d])
            for _ in range(30):
                char_d.update(keys_d, dt, yaw, is_aiming, MockCollider())
            
            dx_d = char_d.x - 50.0
            dy_d = char_d.y - 50.0

            dot_right_d = dx_d * cam_right[0] + dy_d * cam_right[1]
            dot_left_d = dx_d * cam_left[0] + dy_d * cam_left[1]

            assert dot_right_d > 0.5, f"[{desc} - {mode_str}] Pressing D did NOT move Right! dot_right={dot_right_d:.3f}, dx={dx_d:.3f}, dy={dy_d:.3f}"
            assert dot_left_d < -0.5, f"[{desc} - {mode_str}] Pressing D moved Left! dot_left={dot_left_d:.3f}"
            assert char_d.movement_dir_x * cam_right[0] + char_d.movement_dir_y * cam_right[1] > 0.99, f"Movement dir not pointing Right! {char_d.movement_dir_x}, {char_d.movement_dir_y}"
            if is_aiming:
                assert char_d.state == LocomotionState.STRAFE_RIGHT, f"Expected STRAFE_RIGHT, got {char_d.state}"

            # 2. Test A Key (Must move LEFT relative to camera)
            char_a = CharacterGL(x=50.0, y=50.0, facing_yaw=yaw)
            keys_a = make_keys([pygame.K_a])
            for _ in range(30):
                char_a.update(keys_a, dt, yaw, is_aiming, MockCollider())
            
            dx_a = char_a.x - 50.0
            dy_a = char_a.y - 50.0

            dot_left_a = dx_a * cam_left[0] + dy_a * cam_left[1]
            dot_right_a = dx_a * cam_right[0] + dy_a * cam_right[1]

            assert dot_left_a > 0.5, f"[{desc} - {mode_str}] Pressing A did NOT move Left! dot_left={dot_left_a:.3f}, dx={dx_a:.3f}, dy={dy_a:.3f}"
            assert dot_right_a < -0.5, f"[{desc} - {mode_str}] Pressing A moved Right! dot_right={dot_right_a:.3f}"
            assert char_a.movement_dir_x * cam_left[0] + char_a.movement_dir_y * cam_left[1] > 0.99, f"Movement dir not pointing Left! {char_a.movement_dir_x}, {char_a.movement_dir_y}"
            if is_aiming:
                assert char_a.state == LocomotionState.STRAFE_LEFT, f"Expected STRAFE_LEFT, got {char_a.state}"

    print("  -> Bug 1 Fix VERIFIED: A moves Left, D moves Right at 0°, 90°, 180°, 270° in both modes!")

def test_camera_auto_recentering():
    print("[TEST] Camera Auto-Recentering logic & manual priority...")
    import pygame
    char = CharacterGL(x=10.0, y=10.0, facing_yaw=0.0)
    camera = CameraGL()
    camera.set_angles(yaw=0.0, pitch=15.0)
    dt = 1.0 / 60.0

    # 1. When enable_auto_recenter is False (default), camera NEVER moves on its own
    camera.enable_auto_recenter = False
    camera.set_angles(yaw=math.radians(60), pitch=15.0)
    initial_yaw = camera.yaw
    keys_w = make_keys([pygame.K_w])
    for _ in range(120): # 2.0s
        char.update(keys_w, dt, 0.0, False, MockCollider())
        camera.update(char, keys_w, dt, 0, 0, False, None)
    assert camera.auto_recentering is False
    assert abs(camera.yaw - initial_yaw) < 0.001, "Camera moved independently while auto-recenter was disabled!"

    # 2. When enable_auto_recenter is True, it recenters after delay
    camera.enable_auto_recenter = True
    camera.set_angles(yaw=math.radians(60), pitch=15.0)
    initial_yaw = camera.yaw
    # Less than RECENTER_DELAY (e.g. 1.0s)
    for _ in range(60):
        char.update(keys_w, dt, 0.0, False, MockCollider())
        camera.update(char, keys_w, dt, 0, 0, False, None)
    assert camera.auto_recentering is False, "Auto-recentering triggered too early!"

    # Exceed RECENTER_DELAY (3.5s total)
    for _ in range(180):
        char.update(keys_w, dt, 0.0, False, MockCollider())
        camera.update(char, keys_w, dt, 0, 0, False, None)
    assert camera.auto_recentering is True, "Auto-recentering should be active!"
    assert camera.yaw < initial_yaw, "Camera yaw should be easing toward forward travel direction"

    # 3. Mouse input immediately cancels recentering
    camera.handle_mouse_movement(dx=10.0, dy=0.0)
    assert camera.auto_recentering is False, "Mouse input must cancel auto-recentering"
    assert camera.recentering_timer == 0.0
    print("  -> Auto-Recentering & Manual Priority PASSED!")

def test_framerate_independence():
    print("[TEST] Framerate independence (30 FPS vs 60 FPS vs 120 FPS)...")
    import pygame

    speeds = []
    distances = []
    keys_w = make_keys([pygame.K_w])

    for target_fps in [30, 60, 120]:
        char = CharacterGL(x=0.0, y=0.0, facing_yaw=0.0)
        dt = 1.0 / target_fps
        total_time = 2.0 # 2 seconds
        steps = int(total_time * target_fps)
        for _ in range(steps):
            char.update(keys_w, dt, 0.0, False, MockCollider())
        speeds.append(char.current_speed)
        distances.append(char.x)
    
    # Ensure final speeds and distances are within 5% across framerates
    speed_diff = max(speeds) - min(speeds)
    dist_diff = max(distances) - min(distances)
    assert speed_diff < 0.15, f"Speed variation across framerates too large: {speeds}"
    assert dist_diff < 0.35, f"Distance variation across framerates too large: {distances}"
    print(f"  -> Framerate Independence PASSED! Distances: {[round(d, 3) for d in distances]}")

def test_obstacle_collision():
    print("[TEST] Obstacle collision sliding...")
    import pygame
    # Box from x=15 to 25, y=5 to 15
    collider = MockCollider(boxes=[(15.0, 5.0, 25.0, 15.0)])
    char = CharacterGL(x=13.0, y=10.0, facing_yaw=0.0)
    dt = 1.0 / 60.0
    keys_w = make_keys([pygame.K_w])

    # Try to walk straight into the box (+X)
    for _ in range(120): # 2s
        char.update(keys_w, dt, 0.0, False, collider)
    
    # Should be stopped before entering x=15 - radius (radius=0.35, so x <= 14.65)
    assert char.x < 14.7, f"Character clipped into building! x={char.x}"
    print(f"  -> Collision PASSED! Character blocked cleanly at x={char.x:.3f}")

if __name__ == "__main__":
    test_camera_relative_a_and_d()
    test_scenario_a_walk_forward()
    test_scenario_b_sprint_and_turn()
    test_scenario_c_walk_backward_s_key()
    test_scenario_d_camera_rotation_while_stationary()
    test_scenario_e_combat_aim_mode()
    test_scenario_f_sudden_stopping()
    test_camera_auto_recentering()
    test_framerate_independence()
    test_obstacle_collision()
    print("\n===========================================")
    print("ALL GTA LOCOMOTION & CAMERA TESTS PASSED!")
    print("===========================================")
