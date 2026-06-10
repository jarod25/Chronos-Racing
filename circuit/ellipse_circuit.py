import numpy as np
import pygame

from circuit.base_circuit import BaseCircuit
from gui.colors import LIGHT_BACKGROUND


class EllipseCircuit(BaseCircuit):
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
            num_checkpoints=200,
    ):
        super().__init__(
            view_size=view_size,
            view_offset=view_offset,
            checkpoint_depth=int(width * 2),
        )

        self.cx = center_x
        self.cy = center_y

        self.length = length
        self.height = height
        self.width = width
        self.border_thickness = border_thickness

        self.num_checkpoints = num_checkpoints

        self.outer_a = length / 2
        self.outer_b = height / 2

        self.inner_a = (length - width * 2) / 2
        self.inner_b = (height - width * 2) / 2

        self.outer_rect = self._make_rect(length, height)
        self.inner_rect = self._make_rect(length - width * 2, height - width * 2)

        self.outer_border_rect = self._expand_rect(self.outer_rect, border_thickness)
        self.inner_hole_rect = self._shrink_rect(self.inner_rect, border_thickness)

        self.checkpoints = self.generate_checkpoints()

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

        return (
                ((x - self.cx) ** 2) / (a ** 2)
                + ((y - self.cy) ** 2) / (b ** 2)
        )

    def is_on_track(self, pos):
        if not self.is_inside_view(pos):
            return False

        outer_value = self._ellipse_value(pos, self.outer_a, self.outer_b)
        inner_value = self._ellipse_value(pos, self.inner_a, self.inner_b)

        return outer_value <= 1.0 <= inner_value

    def generate_outer_outline(self):
        outline = []

        for i in range(self.num_checkpoints):
            angle = i / self.num_checkpoints * 2 * np.pi

            x = self.cx + np.cos(angle) * self.outer_a
            y = self.cy + np.sin(angle) * self.outer_b

            outline.append((x, y))

        return outline

    def get_outline_points(self):
        return self.generate_outer_outline()

    def generate_checkpoints(self):
        return self.generate_checkpoints_from_outline(
            outline=self.get_outline_points(),
            checkpoint_spacing=None,
            avoid_intersections=False,
        )

    def get_state(self, car):
        dx = (car.pos[0] - self.cx) / self.outer_a
        dy = (car.pos[1] - self.cy) / self.outer_b

        return [
            dx,
            dy,
            np.cos(car.angle),
            np.sin(car.angle),
        ]

    def draw(self, screen, draw_checkpoints=False):
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

        pygame.draw.ellipse(
            screen,
            track_color,
            self._shift_rect(self.outer_rect),
        )

        pygame.draw.ellipse(
            screen,
            border_color,
            self._shift_rect(self.outer_border_rect),
            self.border_thickness,
        )

        pygame.draw.ellipse(
            screen,
            border_color,
            self._shift_rect(self.inner_rect),
            self.border_thickness,
        )

        pygame.draw.ellipse(
            screen,
            outer_color,
            self._shift_rect(self.inner_hole_rect),
        )

        self.draw_start_line(screen)

        if draw_checkpoints:
            self.draw_checkpoints(screen)
