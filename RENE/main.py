import sys
import pygame
from asset_loader import AssetLoader
from map import BarangaySinagtalaMap
from camera import Camera
from lighting import LightingSystem

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60


def draw_loading_screen(screen, font, message):
    screen.fill((22, 28, 34))
    text = font.render(message, True, (245, 224, 175))
    rect = text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
    screen.blit(text, rect)
    pygame.display.flip()
    pygame.event.pump()


def run_explorer():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("PROJECT RENE: BARANGAY SINAGTALA — Master World Map Explorer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18, bold=True)

    # Show immediate visual feedback while extracting ZIPs and baking 160x120 tiles
    draw_loading_screen(screen, font, "Stage 1: Extracting & Loading Asset Packs...")
    assets = AssetLoader(".")

    draw_loading_screen(screen, font, "Stages 3-6: Building Barangay Sinagtala (160x120 Tiles)...")
    world = BarangaySinagtalaMap(assets)

    camera = Camera(SCREEN_W, SCREEN_H, world.tilemap.pixel_width, world.tilemap.pixel_height)
    lighting = LightingSystem(SCREEN_W, SCREEN_H)

    # Start in Area A: Central Town Plaza
    current_name, start_x, start_y = world.DISTRICT_LANDMARKS["1"]
    camera.center_on(start_x, start_y, immediate=True)

    # Interactive Object Placement Palette
    palette_keys = [
        "tree_acacia_large", "tree_mango", "tree_narra_gold", "tree_caballero_pink",
        "tree_coconut", "tree_banana", "tree_pine_tropical", "bush_flowering",
        "bush_round", "flower_bed_box", "potted_bougainvillea", "potted_fern",
        "bench_h", "street_lamp", "wooden_crate", "barrel", "clay_jar",
        "stone_well", "rock_large", "fence_h", "stone_pillar", "beehive"
    ]
    selected_idx = 0
    lighting_enabled = True
    show_brush_ghost = True

    print(f"[Ready] Loaded {len(assets.sprites)} sprites and {len(world.tilemap.chunk_cache)} map chunks.")
    print("[Controls] WASD/Arrows: Move | Shift: Fast | 1-8: Districts | Q/E or Scroll: Change Brush | L-Click: Place | R-Click: Undo | L: Toggle Lighting | B: Toggle Brush Preview")

    running = True
    while running:
        dt = min(0.05, clock.tick(FPS) / 1000.0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_l:
                    lighting_enabled = not lighting_enabled
                elif event.key == pygame.K_b:
                    show_brush_ghost = not show_brush_ghost
                elif event.key == pygame.K_q:
                    selected_idx = (selected_idx - 1) % len(palette_keys)
                    print(f"[Selected Brush] {palette_keys[selected_idx]}")
                elif event.key == pygame.K_e:
                    selected_idx = (selected_idx + 1) % len(palette_keys)
                    print(f"[Selected Brush] {palette_keys[selected_idx]}")
                elif event.unicode in world.DISTRICT_LANDMARKS:
                    name, lx, ly = world.DISTRICT_LANDMARKS[event.unicode]
                    camera.center_on(lx, ly, immediate=False)
                    pygame.display.set_caption(f"PROJECT RENE: BARANGAY SINAGTALA — {name}")

            elif event.type == pygame.MOUSEWHEEL:
                selected_idx = (selected_idx + event.y) % len(palette_keys)
                print(f"[Selected Brush] {palette_keys[selected_idx]}")


            elif event.type == pygame.MOUSEBUTTONDOWN:

                mx, my = pygame.mouse.get_pos()

                skey = palette_keys[selected_idx]

                surf = assets.sprites.get(skey)

                if event.button == 1 and surf:

                    wx = int((camera.x + mx - surf.get_width() // 2) // 8) * 8

                    wy = int((camera.y + my - surf.get_height() + 16) // 8) * 8

                    is_lamp = (skey == "street_lamp")

                    world.env.add_object(wx, wy, skey, light_source=is_lamp)

                    world.env.finalize_sorting()

                    world.save_custom_object(wx, wy, skey, light_source=is_lamp)

                    print(f'[Saved to JSON] env.add_object({wx}, {wy}, "{skey}")')

                elif event.button == 3 and world.env.mid_objects:

                    removed = world.env.mid_objects.pop()

                    world.remove_last_custom_object()

                    print(f"[Removed] {removed.sprite_key} at ({removed.x}, {removed.y})")

        # Smooth camera exploration controls (WASD / Arrow Keys, Shift for fast pan)
        keys = pygame.key.get_pressed()
        speed = 750.0 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else 360.0
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if dx or dy:
            camera.move_target(dx * speed * dt, dy * speed * dt)

        camera.update(dt)
        world.anim.update(dt)

        # Fallback background color in case camera peeks at an edge
        screen.fill((68, 138, 54))

        # 1. Render Terrain Chunks & Animated Water
        water_frame = world.anim.get_water_frame_index()
        world.tilemap.render_visible(screen, camera, water_frame_idx=water_frame)

        # 2. Render Ground Animations (Waterfalls, Swaying Flowers)
        world.anim.render_ground_nodes(screen, camera)

        # 3. Render Y-Sorted Environment (Houses, Trees, Bridges, Fauna)
        world.env.render(screen, camera, dynamic_ables=world.anim.get_mid_ables())

        # 4. Render Atmospheric Particles (Petals, Fireflies, Dust Motes)
        world.anim.particles.render(screen, camera)

        # 5. Apply District-Mood Cinematic Lighting
        cx = camera.x + SCREEN_W * 0.5
        cy = camera.y + SCREEN_H * 0.5
        current_district = world.get_district_at(cx, cy)
        if lighting_enabled:
            lighting.apply(screen, camera, current_district, world.env.light_positions, world.anim.global_time)

        # 6. Optional Ghost Preview of Selected Tree/Object Brush
        if show_brush_ghost:
            mx, my = pygame.mouse.get_pos()
            preview_surf = assets.sprites.get(palette_keys[selected_idx])
            if preview_surf:
                ghost = preview_surf.copy()
                ghost.set_alpha(145)
                screen.blit(ghost, (mx - ghost.get_width() // 2, my - ghost.get_height() + 16))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_explorer()