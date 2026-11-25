import math
import random
import pygame


class AnimatedNode:
    def __init__(self, x, y, anim_key, fps=6.0, phase=0.0, layer="mid", patrol_radius=0):
        self.home_x = float(x)
        self.home_y = float(y)
        self.x = float(x)
        self.y = float(y)
        self.anim_key = anim_key
        self.fps = fps
        self.timer = phase
        self.layer = layer
        self.patrol_radius = patrol_radius
        self.angle = phase * 3.14


class AtmosphericParticleSystem:
    """Manages subtle drifting petals, golden dust motes, fireflies, and cloud shadows."""

    def __init__(self, world_w, world_h, count=140):
        self.world_w = world_w
        self.world_h = world_h
        rng = random.Random(2026)
        self.particles = []
        for _ in range(count):
            ptype = rng.choice(["petal", "mote", "firefly"])
            self.particles.append({
                "x": rng.uniform(0, world_w),
                "y": rng.uniform(0, world_h),
                "vx": rng.uniform(8.0, 22.0) if ptype == "petal" else rng.uniform(-6.0, 6.0),
                "vy": rng.uniform(6.0, 14.0) if ptype == "petal" else rng.uniform(-5.0, 5.0),
                "phase": rng.uniform(0, 6.28),
                "type": ptype,
            })

    def update(self, dt):
        for p in self.particles:
            p["phase"] += dt * 2.5
            p["x"] = (p["x"] + p["vx"] * dt + math.sin(p["phase"]) * 0.3) % self.world_w
            p["y"] = (p["y"] + p["vy"] * dt + math.cos(p["phase"] * 0.7) * 0.2) % self.world_h

    def render(self, target_surf, camera):
        view = camera.get_world_viewport()
        for p in self.particles:
            if not view.collidepoint(p["x"], p["y"]):
                continue
            sx, sy = camera.world_to_screen(p["x"], p["y"])
            if p["type"] == "petal":
                pygame.draw.rect(target_surf, (255, 168, 198), (sx, sy, 4, 3))
            elif p["type"] == "firefly":
                alpha = int(130 + 120 * math.sin(p["phase"] * 1.8))
                glow = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(glow, (210, 255, 110, alpha // 2), (5, 5), 5)
                pygame.draw.circle(glow, (255, 255, 180, alpha), (5, 5), 2)
                target_surf.blit(glow, (sx - 5, sy - 5))
            else:
                pygame.draw.circle(target_surf, (255, 242, 185), (sx, sy), 2)


class AnimationManager:
    """Coordinates sprite-sheet frame cycling for waterfalls, fountains, flora, and fauna."""

    def __init__(self, asset_loader, world_w, world_h):
        self.assets = asset_loader
        self.nodes = []
        self.particles = AtmosphericParticleSystem(world_w, world_h, count=150)
        self.global_time = 0.0

    def add_node(self, x, y, anim_key, fps=6.0, phase=0.0, layer="mid", patrol_radius=0):
        self.nodes.append(AnimatedNode(x, y, anim_key, fps, phase, layer, patrol_radius))

    def update(self, dt):
        self.global_time += dt
        self.particles.update(dt)
        for node in self.nodes:
            node.timer += dt * node.fps
            if node.patrol_radius > 0:
                node.angle += dt * 0.55
                node.x = node.home_x + math.cos(node.angle) * node.patrol_radius
                node.y = node.home_y + math.sin(node.angle * 0.8) * (node.patrol_radius * 0.6)

    def get_water_frame_index(self):
        return int(self.global_time * 4.5) % 4

    def render_ground_nodes(self, target_surf, camera):
        view = camera.get_world_viewport().inflate(128, 128)
        for node in self.nodes:
            if node.layer != "ground":
                continue
            if view.collidepoint(node.x, node.y):
                frames = self.assets.anim_frames.get(node.anim_key)
                if frames:
                    surf = frames[int(node.timer) % len(frames)]
                    sx, sy = camera.world_to_screen(node.x, node.y)
                    target_surf.blit(surf, (sx, sy))

    def get_mid_ables(self):
        ables = []
        for node in self.nodes:
            if node.layer != "mid":
                continue
            frames = self.assets.anim_frames.get(node.anim_key)
            if frames:
                surf = frames[int(node.timer) % len(frames)]
                ables.append((node.y + surf.get_height(), int(node.x), int(node.y), surf))
        return ables
