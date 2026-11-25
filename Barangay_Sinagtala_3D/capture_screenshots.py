"""
Captures high-resolution in-game screenshots of the GTA locomotion and camera system.
Saves directly into the artifact directory.
"""
import sys
import os
import math
import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from textures_gl import GLTextureManager
from city_builder import CityEnvironment
from character_gl import CharacterGL
from camera_gl import CameraGL
from renderer_gl import RendererGL
from test_locomotion import make_keys

ARTIFACT_DIR = r"C:\Users\Erica Leira\.gemini\antigravity-cli\brain\81013177-957b-40b3-9cdc-ace4b1f69cea"
WINDOW_W = 1280
WINDOW_H = 720

def save_frame(filename):
    out_path = os.path.join(ARTIFACT_DIR, filename)
    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    data = glReadPixels(0, 0, WINDOW_W, WINDOW_H, GL_RGBA, GL_UNSIGNED_BYTE)
    surface = pygame.image.fromstring(data, (WINDOW_W, WINDOW_H), "RGBA", True)
    pygame.image.save(surface, out_path)
    print(f"Saved: {out_path}")

def run_captures():
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption("Capturing GTA Locomotion...")

    tex_mgr = GLTextureManager()
    city_env = CityEnvironment()
    city_env.init_gl_geometry(tex_mgr)
    renderer = RendererGL(width=WINDOW_W, height=WINDOW_H)

    dt = 1.0 / 60.0

    # -------------------------------------------------------------
    # 1. SCENE 1: FREE-ROAM JOGGING (North along +Y)
    # -------------------------------------------------------------
    char = CharacterGL(x=40.0, y=36.0, z=0.0)
    cam = CameraGL(init_yaw=math.pi * 0.5)
    keys_w = make_keys([pygame.K_w])
    for _ in range(60): # 1 sec of jogging
        char.update(keys_w, dt, cam.yaw, False, city_env)
        cam.update(char, keys_w, dt, 0, 0, False, city_env)
    
    renderer.begin_frame(cam)
    renderer.render_world(city_env, char, cam, dt, show_debug=True)
    renderer.draw_2d_hud(cam, char, 60, show_minimap=True, mouse_locked=True, show_debug=True)
    pygame.display.flip()
    save_frame("screen_gta_jog.png")

    # -------------------------------------------------------------
    # 2. SCENE 2: BUG 1 VERIFICATION — D KEY MOVES RIGHT (+X)
    # -------------------------------------------------------------
    char_d = CharacterGL(x=40.0, y=40.0, z=0.0)
    cam_d = CameraGL(init_yaw=math.pi * 0.5) # Looking North (+Y), Right is East (+X)
    keys_d = make_keys([pygame.K_d])
    for _ in range(45):
        char_d.update(keys_d, dt, cam_d.yaw, False, city_env)
        cam_d.update(char_d, keys_d, dt, 0, 0, False, city_env)
    
    renderer.begin_frame(cam_d)
    renderer.render_world(city_env, char_d, cam_d, dt, show_debug=True)
    renderer.draw_2d_hud(cam_d, char_d, 60, show_minimap=True, mouse_locked=True, show_debug=True)
    pygame.display.flip()
    save_frame("screen_debug_strafe_right.png")

    # -------------------------------------------------------------
    # 3. SCENE 3: BUG 1 VERIFICATION — A KEY MOVES LEFT (-X) IN AIM MODE
    # -------------------------------------------------------------
    char_a = CharacterGL(x=40.0, y=40.0, z=0.0)
    cam_a = CameraGL(init_yaw=math.pi * 0.5) # Looking North (+Y), Left is West (-X)
    keys_a = make_keys([pygame.K_a])
    for _ in range(45):
        char_a.update(keys_a, dt, cam_a.yaw, True, city_env)
        cam_a.update(char_a, keys_a, dt, 0, 0, True, city_env)
    
    renderer.begin_frame(cam_a)
    renderer.render_world(city_env, char_a, cam_a, dt, show_debug=True)
    renderer.draw_2d_hud(cam_a, char_a, 60, show_minimap=True, mouse_locked=True, show_debug=True)
    pygame.display.flip()
    save_frame("screen_debug_strafe_left.png")

    # -------------------------------------------------------------
    # 4. SCENE 4: SPRINTING WITH DYNAMIC FOV & BODY LEAN
    # -------------------------------------------------------------
    char_sp = CharacterGL(x=40.0, y=36.0, z=0.0)
    cam_sp = CameraGL(init_yaw=math.pi * 0.5)
    keys_sprint = make_keys([pygame.K_w, pygame.K_LSHIFT])
    for _ in range(90): # 1.5s sprint
        char_sp.update(keys_sprint, dt, cam_sp.yaw, False, city_env)
        cam_sp.update(char_sp, keys_sprint, dt, 0, 0, False, city_env)
    
    renderer.begin_frame(cam_sp)
    renderer.render_world(city_env, char_sp, cam_sp, dt, show_debug=True)
    renderer.draw_2d_hud(cam_sp, char_sp, 60, show_minimap=True, mouse_locked=True, show_debug=True)
    pygame.display.flip()
    save_frame("screen_gta_sprint.png")

    # -------------------------------------------------------------
    # 5. SCENE 5: BANKING TURN (BODY ROLL & ANGULAR INERTIA)
    # -------------------------------------------------------------
    keys_turn = make_keys([pygame.K_w, pygame.K_a, pygame.K_LSHIFT])
    for _ in range(25): # Turning left while sprinting
        char_sp.update(keys_turn, dt, cam_sp.yaw, False, city_env)
        cam_sp.update(char_sp, keys_turn, dt, 0, 0, False, city_env)
    
    renderer.begin_frame(cam_sp)
    renderer.render_world(city_env, char_sp, cam_sp, dt, show_debug=True)
    renderer.draw_2d_hud(cam_sp, char_sp, 60, show_minimap=True, mouse_locked=True, show_debug=True)
    pygame.display.flip()
    save_frame("screen_gta_bank_turn.png")

    # -------------------------------------------------------------
    # 6. SCENE 6: COMBAT AIM STRAFING (SHOULDER CAM + RETICLE)
    # -------------------------------------------------------------
    char_aim = CharacterGL(x=40.0, y=42.0, z=0.0)
    cam_aim = CameraGL(init_yaw=math.pi * 0.5)
    keys_aim = make_keys([pygame.K_d]) # Strafing right while aiming
    for _ in range(40):
        char_aim.update(keys_aim, dt, cam_aim.yaw, True, city_env)
        cam_aim.update(char_aim, keys_aim, dt, 0, 0, True, city_env)
    
    renderer.begin_frame(cam_aim)
    renderer.render_world(city_env, char_aim, cam_aim, dt, show_debug=True)
    renderer.draw_2d_hud(cam_aim, char_aim, 60, show_minimap=True, mouse_locked=True, show_debug=True)
    pygame.display.flip()
    save_frame("screen_gta_aim_strafe.png")

    pygame.quit()
    print("All captures completed successfully!")

if __name__ == "__main__":
    run_captures()
