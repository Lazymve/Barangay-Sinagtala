import os
import pygame
from asset_loader import AssetLoader
from map import BarangaySinagtalaMap
from camera import Camera
from lighting import LightingSystem


def export_all_renders(output_dir="renders"):
    os.makedirs(output_dir, exist_ok=True)
    pygame.init()
    # Hidden display surface for hardware-accelerated surface conversion
    pygame.display.set_mode((1280, 720), pygame.HIDDEN)

    assets = AssetLoader(".")
    world = BarangaySinagtalaMap(assets)
    world.anim.update(1.25)

    view_w, view_h = 1280, 720
    camera = Camera(view_w, view_h, world.tilemap.pixel_width, world.tilemap.pixel_height)
    lighting = LightingSystem(view_w, view_h)

    # 1. Export Close-Up Screenshots of All 8 Districts
    filenames = {
        "1": "01_area_a_central_town_plaza.png",
        "2": "02_area_b_public_market_palengke.png",
        "3": "03_area_c_residential_neighborhood.png",
        "4": "04_area_d_riverside_countryside.png",
        "5": "05_area_e_agricultural_district.png",
        "6": "06_area_f_heritage_district.png",
        "7": "07_area_g_forest_and_garden_edge.png",
        "8": "08_area_h_municipal_and_palace_district.png",
    }

    surf = pygame.Surface((view_w, view_h))
    for key, (d_name, lx, ly) in world.DISTRICT_LANDMARKS.items():
        camera.center_on(lx, ly, immediate=True)
        # Warm up district lighting interpolation
        for _ in range(30):
            lighting.apply(surf, camera, d_name, world.env.light_positions, time_sec=1.5)

        world.tilemap.render_visible(surf, camera, water_frame_idx=1)
        world.anim.render_ground_nodes(surf, camera)
        world.env.render(surf, camera, dynamic_ables=world.anim.get_mid_ables())
        world.anim.particles.render(surf, camera)
        lighting.apply(surf, camera, d_name, world.env.light_positions, time_sec=1.5)

        out_path = os.path.join(output_dir, filenames[key])
        pygame.image.save(surf, out_path)
        print(f"[Exported District Close-Up] {out_path}")

    # 2. Stitch Full-Map Overview (5120x3840 native -> saved at 2560x1920 overview PNG)
    full_w, full_h = world.tilemap.pixel_width, world.tilemap.pixel_height
    full_cam = Camera(full_w, full_h, full_w, full_h)
    full_cam.center_on(full_w // 2, full_h // 2, immediate=True)
    full_surf = pygame.Surface((full_w, full_h))

    world.tilemap.render_visible(full_surf, full_cam, water_frame_idx=1)
    world.anim.render_ground_nodes(full_surf, full_cam)
    world.env.render(full_surf, full_cam, dynamic_ables=world.anim.get_mid_ables())
    world.anim.particles.render(full_surf, full_cam)

    overview_scaled = pygame.transform.smoothscale(full_surf, (full_w // 2, full_h // 2))
    overview_path = os.path.join(output_dir, "00_barangay_sinagtala_full_overview.png")
    pygame.image.save(overview_scaled, overview_path)
    print(f"[Exported Full Map Overview] {overview_path}")
    pygame.quit()


if __name__ == "__main__":
    export_all_renders()
