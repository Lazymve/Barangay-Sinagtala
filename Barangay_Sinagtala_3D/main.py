"""
PROJECT BARANGAY SINAGTALA 3D — GTA III / IV Urban Game (Pygame + PyOpenGL)
Full hardware-accelerated 3D rendering pipeline, GTA decoupled character controller,
spring-arm orbital boom, multi-story buildings, atmospheric fog, and rain effects.
"""

import sys
import math
import pygame
from textures_gl import GLTextureManager
from city_builder import CityEnvironment
from character_gl import CharacterGL
from camera_gl import CameraGL
from renderer_gl import RendererGL

WINDOW_W = 1280
WINDOW_H = 720
FPS = 60


def run():
    pygame.init()
    # Request 24-bit depth buffer and double buffering
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption("PROJECT BARANGAY SINAGTALA 3D — GTA Urban Engine (PyOpenGL)")
    clock = pygame.time.Clock()

    print("=================================================================")
    print("  PROJECT BARANGAY SINAGTALA 3D — GTA III/IV ENGINE (OPENGL)")
    print("  Controls:")
    print("    W / S             : Move Forward / Backward (Camera-relative)")
    print("    A / D             : Move Left / Right (Camera-relative) [FIXED]")
    print("    Shift             : Sprint (Dynamic wide FOV)")
    print("    Right Click (Hold): Aim Mode (Locks heading to reticle + 3D strafe)")
    print("    Mouse / Arrows    : Orbit camera (Yaw + Pitch)")
    print("    Tab               : Toggle Mouse-Look Mode")
    print("    C                 : Toggle Auto-Recentering (Default: OFF / Manual)")
    print("    F3                : Toggle 3D Debug Direction Vectors")
    print("    V                 : Toggle 3rd-Person / 1st-Person [GTA Camera]")
    print("    M                 : Toggle Minimap Radar")
    print("    R                 : Toggle Rain Weather Effect")
    print("    Esc               : Quit")
    print("=================================================================")

    # Initialize GPU Texture Manager and 3D City Environment
    tex_mgr = GLTextureManager()
    city_env = CityEnvironment()
    city_env.init_gl_geometry(tex_mgr)

    # Initialize Character (spawns in central avenue), Camera, and 3D Renderer
    character = CharacterGL(x=40.0, y=36.0, z=0.0)
    camera = CameraGL(init_yaw=math.pi * 0.5)  # Facing North up the avenue
    renderer = RendererGL(width=WINDOW_W, height=WINDOW_H)

    show_minimap = True
    show_debug = True
    mouse_locked = False
    pygame.mouse.set_visible(True)

    running = True
    while running:
        dt = min(0.05, clock.tick(FPS) / 1000.0)
        mouse_dx = 0
        mouse_dy = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_v:
                    camera.toggle_mode()
                elif event.key == pygame.K_m:
                    show_minimap = not show_minimap
                elif event.key == pygame.K_r:
                    renderer.rain_enabled = not renderer.rain_enabled
                elif event.key == pygame.K_c:
                    camera.toggle_auto_recenter()
                    print(f"[CAMERA] Auto-Recentering: {'ENABLED' if camera.enable_auto_recenter else 'DISABLED'}")
                elif event.key == pygame.K_F3:
                    show_debug = not show_debug
                elif event.key == pygame.K_TAB:
                    mouse_locked = not mouse_locked
                    pygame.mouse.set_visible(not mouse_locked)
                    pygame.event.set_grab(mouse_locked)
                    if mouse_locked:
                        pygame.mouse.get_rel()

        # Handle mouse look rotation
        if mouse_locked:
            rel = pygame.mouse.get_rel()
            mouse_dx = rel[0]
            mouse_dy = rel[1]

        # Check Right Mouse Button (RMB) for GTA Aim Mode
        mouse_buttons = pygame.mouse.get_pressed()
        is_aiming = bool(mouse_buttons[2])

        # 1. Update Character physics (momentum, friction, dual-mode locomotion)
        keys = pygame.key.get_pressed()
        character.update(keys, dt, camera.yaw, is_aiming, city_env)

        # 2. Update GTA Spring-Arm Camera Boom
        camera.update(character, keys, dt, mouse_dx=mouse_dx, mouse_dy=mouse_dy, is_aiming=is_aiming, city_env=city_env)

        # 3. Render 3D Scene in OpenGL
        renderer.begin_frame(camera)
        renderer.render_world(city_env, character, camera, dt, show_debug=show_debug)

        # 4. Render 2D Orthographic HUD (Reticle, Minimap, Stats)
        fps = int(clock.get_fps())
        renderer.draw_2d_hud(camera, character, fps, show_minimap, mouse_locked, show_debug=show_debug)

        # 5. Flip OpenGL Double Buffer
        pygame.display.flip()

        # Update caption with live locomotion state machine stats
        if int(character.current_speed * 10) % 4 == 0:
            cam_str = "3RD-PERSON [GTA]" if camera.mode == camera.THIRD_PERSON else "1ST-PERSON"
            recenter_str = "RECENTER: ON" if camera.enable_auto_recenter else "RECENTER: OFF (Press C)"
            pygame.display.set_caption(
                f"BARANGAY SINAGTALA 3D | A/D: A=LEFT, D=RIGHT | STATE: {character.state.value} | SPD: {character.current_speed:.1f}m/s | CAM: {math.degrees(camera.yaw):.0f}° | {recenter_str} | FPS: {fps}"
            )

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
