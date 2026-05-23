from collections import deque

import numpy as np
import pygame

from circuit.base_circuit import BaseCircuit
from gui.colors import LIGHT_BACKGROUND


class ImportedCircuit(BaseCircuit):
    def __init__(self,image_path,view_size,view_offset=(0, 0),checkpoint_spacing=8,checkpoint_depth=300):
        super().__init__(
            view_size=view_size,
            view_offset=view_offset,
            checkpoint_depth=checkpoint_depth,
        )

        self.image_path = image_path

        self.width = self.view_width
        self.height = self.view_height

        self.checkpoint_spacing = checkpoint_spacing
        self.num_checkpoints = 0

        self.color_tolerance = 45
        self.click_search_radius = 10
        self.min_component_ratio_from_biggest = 0.30
        self.min_component_width_ratio = 0.12
        self.min_component_height_ratio = 0.12
        self.bottom_text_zone_start = 0.70

        loaded_image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.smoothscale(loaded_image, view_size)

        self.pixels = pygame.surfarray.array3d(self.image).astype(np.int16)
        self.alpha = pygame.surfarray.array_alpha(self.image)

        self.track_mask = None
        self.mask_pixel_count = 0

    def generate_track_mask_from_point(self, pos):
        if not self.is_inside_view(pos):
            return 0

        component = self.find_valid_component_near_point(pos)

        if component is None:
            self.track_mask = None
            self.mask_pixel_count = 0
            self.checkpoints = []
            return 0

        self.track_mask = self.array_to_mask(component)
        self.mask_pixel_count = self.track_mask.count()

        self.checkpoints = self.generate_checkpoints()
        self.num_checkpoints = len(self.checkpoints)

        print("outline points:", len(self.get_outline_points()))
        print("generated checkpoints:", len(self.checkpoints))

        return self.mask_pixel_count

    def find_valid_component_near_point(self, pos):
        x0 = int(pos[0])
        y0 = int(pos[1])

        tested_colors = set()
        best_component = None
        best_count = 0

        for x, y in self.get_search_positions(x0, y0):
            if self.alpha[x, y] <= 10:
                continue

            color = self.image.get_at((x, y))
            color_key = (
                color.r // 8,
                color.g // 8,
                color.b // 8,
            )

            if color_key in tested_colors:
                continue

            tested_colors.add(color_key)

            color_mask = self.build_color_mask(color)
            component = self.extract_component(color_mask, (x, y))

            if not self.is_valid_track_component(component, color_mask):
                continue

            count = int(component.sum())

            if count > best_count:
                best_count = count
                best_component = component

        return best_component

    def get_search_positions(self, x0, y0):
        if 0 <= x0 < self.width and 0 <= y0 < self.height:
            yield x0, y0

        for radius in range(1, self.click_search_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in (-radius, radius):
                    x = x0 + dx
                    y = y0 + dy

                    if 0 <= x < self.width and 0 <= y < self.height:
                        yield x, y

            for dy in range(-radius + 1, radius):
                for dx in (-radius, radius):
                    x = x0 + dx
                    y = y0 + dy

                    if 0 <= x < self.width and 0 <= y < self.height:
                        yield x, y

    def build_color_mask(self, selected_color):
        tolerance_squared = self.color_tolerance * self.color_tolerance * 3

        selected = np.array(
            [selected_color.r, selected_color.g, selected_color.b],
            dtype=np.int16,
        )

        diff = self.pixels - selected
        distance_squared = np.sum(diff * diff, axis=2)

        return (distance_squared <= tolerance_squared) & (self.alpha > 10)

    def extract_component(self, mask, seed):
        x = int(seed[0])
        y = int(seed[1])

        if not self.is_mask_pos_valid(mask, x, y):
            return np.zeros_like(mask, dtype=bool)

        component = np.zeros_like(mask, dtype=bool)

        queue = deque([(x, y)])
        component[x, y] = True

        while queue:
            cx, cy = queue.popleft()

            for nx, ny in self.get_neighbors(cx, cy):
                if mask[nx, ny] and not component[nx, ny]:
                    component[nx, ny] = True
                    queue.append((nx, ny))

        return component

    def is_valid_track_component(self, component, color_mask):
        count = int(component.sum())

        if count == 0:
            return False

        xs, ys = np.where(component)

        min_x = int(xs.min())
        max_x = int(xs.max())
        min_y = int(ys.min())
        max_y = int(ys.max())

        box_width = max_x - min_x + 1
        box_height = max_y - min_y + 1

        if min_y > self.height * self.bottom_text_zone_start:
            return False

        if (
                box_width < self.width * self.min_component_width_ratio
                and box_height < self.height * self.min_component_height_ratio
        ):
            return False

        biggest_count = self.get_biggest_component_count(color_mask)

        if biggest_count > 0:
            if count < biggest_count * self.min_component_ratio_from_biggest:
                return False

        return True

    def get_biggest_component_count(self, mask):
        visited = np.zeros_like(mask, dtype=bool)
        points = np.argwhere(mask)

        biggest_count = 0

        for point in points:
            x = int(point[0])
            y = int(point[1])

            if visited[x, y]:
                continue

            count = 0

            queue = deque([(x, y)])
            visited[x, y] = True

            while queue:
                cx, cy = queue.popleft()
                count += 1

                for nx, ny in self.get_neighbors(cx, cy):
                    if mask[nx, ny] and not visited[nx, ny]:
                        visited[nx, ny] = True
                        queue.append((nx, ny))

            if count > biggest_count:
                biggest_count = count

        return biggest_count

    def get_neighbors(self, x, y):
        neighbors = (
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
            (x - 1, y - 1),
            (x - 1, y + 1),
            (x + 1, y - 1),
            (x + 1, y + 1),
        )

        for nx, ny in neighbors:
            if 0 <= nx < self.width and 0 <= ny < self.height:
                yield nx, ny

    def is_mask_pos_valid(self, mask, x, y):
        return (
                0 <= x < self.width
                and 0 <= y < self.height
                and mask[x, y]
        )

    def array_to_mask(self, mask_array):
        mask = pygame.mask.Mask((self.width, self.height), fill=False)

        points = np.argwhere(mask_array)

        for point in points:
            mask.set_at((int(point[0]), int(point[1])), 1)

        return mask

    def is_on_track(self, pos):
        if self.track_mask is None:
            return False

        if not self.is_inside_view(pos):
            return False

        x = int(pos[0])
        y = int(pos[1])

        return self.track_mask.get_at((x, y)) == 1

    def get_outline_points(self):
        if self.track_mask is None:
            return []

        return self.track_mask.outline()

    def generate_checkpoints(self):
        return self.generate_checkpoints_from_outline(
            outline=self.get_outline_points(),
            checkpoint_spacing=self.checkpoint_spacing,
            avoid_intersections=True,
        )

    def get_state(self, car):
        x = car.pos[0] / self.width
        y = car.pos[1] / self.height

        return [
            x,
            y,
            np.cos(car.angle),
            np.sin(car.angle),
        ]

    def draw(self, screen, draw_checkpoints=False):
        screen.fill(LIGHT_BACKGROUND)

        screen.blit(
            self.image,
            (self.offset_x, self.offset_y),
        )

        self.draw_start_line(screen)

        if draw_checkpoints:
            self.draw_checkpoints(screen)

    def draw_mask_overlay(self, screen):
        if self.track_mask is None:
            return

        mask_surface = self.track_mask.to_surface(
            setcolor=(0, 255, 0),
            unsetcolor=(0, 0, 0),
        )

        mask_surface.set_colorkey((0, 0, 0))
        mask_surface.set_alpha(80)

        screen.blit(
            mask_surface,
            (self.offset_x, self.offset_y),
        )

    def get_start_pose(self):
        if len(self.checkpoints) == 0:
            return (100, 100), 0

        p1, p2 = self.checkpoints[0]

        # Milieu du checkpoint
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2

        # Direction du checkpoint
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]

        # Tangente = perpendiculaire au checkpoint
        tx = -dy
        ty = dx

        angle = np.arctan2(ty, tx)

        return (mx, my), angle