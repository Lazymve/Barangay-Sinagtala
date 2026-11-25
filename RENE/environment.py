import pygame


class EnvObject:
    """Represents a placed environmental structure, tree, or prop with Y-sort depth."""

    __slots__ = ("x", "y", "sprite_key", "layer", "sort_y", "light_source", "collision_rect", "w", "h")

    def __init__(self, x, y, sprite_key, sprite_surf, layer="mid", sort_offset=0, light_source=False):
        self.x = x
        self.y = y
        self.sprite_key = sprite_key
        self.layer = layer  # "ground", "mid", "overhead"
        self.w, self.h = sprite_surf.get_size() if sprite_surf else (32, 32)
        self.sort_y = self.y + self.h + sort_offset
        self.light_source = light_source
        self.collision_rect = pygame.Rect(self.x + 8, self.y + self.h - 24, max(16, self.w - 16), 20)


class EnvironmentManager:
    """Manages placement, Y-sorting, overhead wire networks, and viewport culling."""

    def __init__(self, asset_loader):
        self.assets = asset_loader
        self.ground_objects = []
        self.mid_objects = []
        self.overhead_wires = []
        self.light_positions = []

    def add_object(self, x, y, sprite_key, layer="mid", sort_offset=0, light_source=False):
        surf = self.assets.sprites.get(sprite_key)
        if surf is None:
            return
        obj = EnvObject(x, y, sprite_key, surf, layer=layer, sort_offset=sort_offset, light_source=light_source)
        if layer == "ground":
            self.ground_objects.append(obj)
        else:
            self.mid_objects.append(obj)
        if light_source:
            self.light_positions.append((x + obj.w // 2, y + 14))

    def add_wire_span(self, x1, y1, x2, y2):
        self.overhead_wires.append((x1, y1, x2, y2))

    def finalize_sorting(self):
        self.mid_objects.sort(key=lambda o: o.sort_y)

    def render(self, target_surf, camera, dynamic_ables=None):
        view_rect = camera.get_world_viewport().inflate(256, 256)

        # 1. Ground-flush structures (bridges, docks, lilypads)
        for obj in self.ground_objects:
            if view_rect.colliderect(pygame.Rect(obj.x, obj.y, obj.w, obj.h)):
                sx, sy = camera.world_to_screen(obj.x, obj.y)
                target_surf.blit(self.assets.sprites[obj.sprite_key], (sx, sy))

        # 2. Y-Sorted middle-ground (buildings, trees, fences, benches, animated fauna)
        vis_items = []
        for obj in self.mid_objects:
            if view_rect.colliderect(pygame.Rect(obj.x, obj.y, obj.w, obj.h)):
                vis_items.append((obj.sort_y, obj.x, obj.y, self.assets.sprites[obj.sprite_key]))

        if dynamic_ables:
            for sort_y, wx, wy, surf in dynamic_ables:
                if view_rect.collidepoint(wx, wy):
                    vis_items.append((sort_y, wx, wy, surf))

        vis_items.sort(key=lambda item: item[0])
        for _, wx, wy, surf in vis_items:
            sx, sy = camera.world_to_screen(wx, wy)
            target_surf.blit(surf, (sx, sy))

        # 3. Foreground overhead utility wires (Barangay street ambiance)
        for x1, y1, x2, y2 in self.overhead_wires:
            if view_rect.collidepoint(x1, y1) or view_rect.collidepoint(x2, y2):
                p1 = camera.world_to_screen(x1, y1)
                p2 = camera.world_to_screen(x2, y2)
                mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2 + 10)
                pygame.draw.lines(target_surf, (38, 42, 48), False, [p1, mid, p2], 2)
