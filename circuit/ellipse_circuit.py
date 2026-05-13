import numpy as np
import pygame

from gui.colors import LIGHT_BACKGROUND


class EllipseCircuit:
    def __init__(
            self,
            center_x,
            center_y,
            length,
            height,
            width,
            border_thickness,
            view_size=(800, 600),
            view_offset=(0, 0),
    ):
        self.cx = center_x
        self.cy = center_y

        self.length = length
        self.height = height
        self.width = width
        self.border_thickness = border_thickness

        self.view_width = view_size[0]
        self.view_height = view_size[1]

        self.offset_x = view_offset[0]
        self.offset_y = view_offset[1]

        self.outer_a = length / 2
        self.outer_b = height / 2

        self.inner_a = (length - width * 2) / 2
        self.inner_b = (height - width * 2) / 2

        self.outer_rect = self._make_rect(length, height)
        self.inner_rect = self._make_rect(length - width * 2, height - width * 2)

        self.outer_border_rect = self._expand_rect(self.outer_rect, border_thickness)
        self.inner_hole_rect = self._shrink_rect(self.inner_rect, border_thickness)

    def _make_rect(self, w, h):
        return (
            self.cx - w // 2,
            self.cy - h // 2,
            w,
            h,
        )

    def _expand_rect(self, rect, amount):
        x, y, w, h = rect

        return (
            x - amount,
            y - amount,
            w + amount * 2,
            h + amount * 2,
        )

    def _shrink_rect(self, rect, amount):
        x, y, w, h = rect

        return (
            x + amount,
            y + amount,
            w - amount * 2,
            h - amount * 2,
        )

    def _shift_rect(self, rect):
        x, y, w, h = rect

        return (
            x + self.offset_x,
            y + self.offset_y,
            w,
            h,
        )

    def _ellipse_value(self, pos, a, b):
        x, y = pos

        return ((x - self.cx) ** 2) / (a ** 2) + ((y - self.cy) ** 2) / (b ** 2)

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

        return 0 <= x < self.view_width and 0 <= y < self.view_height

    def is_screen_pos_on_track(self, screen_pos):
        return self.is_on_track(self.screen_to_track(screen_pos))

    def is_on_track(self, pos):
        if not self.is_inside_view(pos):
            return False

        outer_value = self._ellipse_value(pos, self.outer_a, self.outer_b)
        inner_value = self._ellipse_value(pos, self.inner_a, self.inner_b)

        return outer_value <= 1.0 <= inner_value

    def get_state(self, car):
        dx = (car.pos[0] - self.cx) / self.outer_a
        dy = (car.pos[1] - self.cy) / self.outer_b

        return [
            dx,
            dy,
            np.cos(car.angle),
            np.sin(car.angle),
        ]

    def draw(self, screen):
        screen.fill(LIGHT_BACKGROUND)

        outer_color = (230, 230, 230)
        track_color = (100, 100, 100)
        border_color = (255, 0, 0)

        view_rect = pygame.Rect(
            self.offset_x,
            self.offset_y,
            self.view_width,
            self.view_height,
        )

        pygame.draw.rect(screen, outer_color, view_rect)
        pygame.draw.ellipse(screen, track_color, self._shift_rect(self.outer_rect))
        pygame.draw.ellipse(screen, border_color, self._shift_rect(self.outer_border_rect), self.border_thickness)
        pygame.draw.ellipse(screen, border_color, self._shift_rect(self.inner_rect), self.border_thickness)
        pygame.draw.ellipse(screen, outer_color, self._shift_rect(self.inner_hole_rect))
