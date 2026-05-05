import pygame
import numpy as np


class Circuit:
    def __init__(self, center_x, center_y, length, height, width, border_thickness):
        self.cx = center_x
        self.cy = center_y

        self.length = length
        self.height = height
        self.width = width
        self.border_thickness = border_thickness

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

    def _ellipse_value(self, pos, a, b):
        x, y = pos
        return ((x - self.cx) ** 2) / (a ** 2) + ((y - self.cy) ** 2) / (b ** 2)

    def is_on_track(self, pos):
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

    def draw(self, screen, outer_color, track_color, border_color):
        screen.fill(outer_color)

        # Piste
        pygame.draw.ellipse(screen, track_color, self.outer_rect)

        # Bordure extérieure
        pygame.draw.ellipse(screen, border_color, self.outer_border_rect, self.border_thickness)

        # Bordure intérieure
        pygame.draw.ellipse(screen, border_color, self.inner_rect, self.border_thickness)

        # Trou intérieur
        pygame.draw.ellipse(screen, outer_color, self.inner_hole_rect)