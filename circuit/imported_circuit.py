import numpy as np
import pygame

from gui.colors import LIGHT_BACKGROUND


class ImportedCircuit:
    def __init__(self, image_path, view_size, view_offset=(0, 0)):
        self.image_path = image_path

        self.width = view_size[0]
        self.height = view_size[1]

        self.offset_x = view_offset[0]
        self.offset_y = view_offset[1]

        loaded_image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.smoothscale(loaded_image, view_size)

        self.track_mask = None
        self.mask_pixel_count = 0

    def screen_to_track(self, screen_pos):
        return (
            screen_pos[0] - self.offset_x,
            screen_pos[1] - self.offset_y,
        )

    def track_to_screen(self, track_pos):
        return (
            track_pos[0] + self.offset_x,
            track_pos[1] + self.offset_y,
        )

    def is_inside_view(self, pos):
        x = int(pos[0])
        y = int(pos[1])

        return 0 <= x < self.width and 0 <= y < self.height

    def generate_track_mask_from_point(self, pos):
        if not self.is_inside_view(pos):
            return 0

        x = int(pos[0])
        y = int(pos[1])

        selected_color = self.image.get_at((x, y))

        if selected_color.a <= 10:
            self.track_mask = None
            self.mask_pixel_count = 0
            return 0

        tolerance = 45
        tolerance_squared = tolerance * tolerance * 3

        mask = pygame.mask.Mask((self.width, self.height), fill=False)

        for py in range(self.height):
            for px in range(self.width):
                color = self.image.get_at((px, py))

                if color.a <= 10:
                    continue

                dr = color.r - selected_color.r
                dg = color.g - selected_color.g
                db = color.b - selected_color.b

                distance_squared = dr * dr + dg * dg + db * db

                if distance_squared <= tolerance_squared:
                    mask.set_at((px, py), 1)

        self.track_mask = mask
        self.mask_pixel_count = mask.count()

        return self.mask_pixel_count

    def is_on_track(self, pos):
        if self.track_mask is None:
            return False

        if not self.is_inside_view(pos):
            return False

        x = int(pos[0])
        y = int(pos[1])

        return self.track_mask.get_at((x, y)) == 1

    def is_screen_pos_on_track(self, screen_pos):
        return self.is_on_track(self.screen_to_track(screen_pos))

    def get_state(self, car):
        x = car.pos[0] / self.width
        y = car.pos[1] / self.height

        return [
            x,
            y,
            np.cos(car.angle),
            np.sin(car.angle),
        ]

    def draw(self, screen):
        screen.fill(LIGHT_BACKGROUND)
        screen.blit(self.image, (self.offset_x, self.offset_y))

    def draw_mask_overlay(self, screen):
        if self.track_mask is None:
            return

        mask_surface = self.track_mask.to_surface(
            setcolor=(0, 255, 0),
            unsetcolor=(0, 0, 0),
        )

        mask_surface.set_colorkey((0, 0, 0))
        mask_surface.set_alpha(80)

        screen.blit(mask_surface, (self.offset_x, self.offset_y))
