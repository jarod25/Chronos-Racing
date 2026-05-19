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
            num_checkpoints=200,
    ):
        self.cx = center_x
        self.cy = center_y

        self.length = length
        self.height = height
        self.width = width
        self.border_thickness = border_thickness

        self.num_checkpoints = num_checkpoints

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

        # ==========================================
        # Checkpoints
        # ==========================================

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

    # =========================================================
    # CHECKPOINT GENERATION
    # =========================================================

    def generate_outer_outline(self):
        outline = []

        for i in range(self.num_checkpoints):
            angle = i / self.num_checkpoints * 2 * np.pi

            x = self.cx + np.cos(angle) * self.outer_a
            y = self.cy + np.sin(angle) * self.outer_b

            outline.append((x, y))

        return outline

    def generate_checkpoints(self):
        checkpoints = []

        outline = self.generate_outer_outline()

        for i in range(len(outline)):
            prev_point = outline[i - 1]
            current_point = outline[i]
            next_point = outline[(i + 1) % len(outline)]

            # Tangente locale

            tx = next_point[0] - prev_point[0]
            ty = next_point[1] - prev_point[1]

            tangent_length = np.hypot(tx, ty)

            if tangent_length == 0:
                continue

            tx /= tangent_length
            ty /= tangent_length

            # Normale

            nx = -ty
            ny = tx

            # Vérifie le sens de la normale

            test_x = current_point[0] + nx * 5
            test_y = current_point[1] + ny * 5

            if not self.is_on_track((test_x, test_y)):
                nx = -nx
                ny = -ny

            # Raycast vers l'intérieur

            last_valid = current_point

            for d in range(int(self.width * 2)):
                x = current_point[0] + nx * d
                y = current_point[1] + ny * d

                if self.is_on_track((x, y)):
                    last_valid = (x, y)
                else:
                    break

            checkpoints.append(
                (
                    current_point,
                    last_valid,
                )
            )

        return checkpoints

    def get_state(self, car):
        dx = (car.pos[0] - self.cx) / self.outer_a
        dy = (car.pos[1] - self.cy) / self.outer_b

        return [
            dx,
            dy,
            np.cos(car.angle),
            np.sin(car.angle),
        ]

    def get_checkpoint(self, car):
        car_pos = np.array(car.pos)

        best_index = 0
        best_distance = float("inf")

        for i, checkpoint in enumerate(self.checkpoints):
            p1, p2 = checkpoint

            midpoint = (
                (p1[0] + p2[0]) / 2,
                (p1[1] + p2[1]) / 2,
            )

            distance = np.linalg.norm(
                car_pos - np.array(midpoint)
            )

            if distance < best_distance:
                best_distance = distance
                best_index = i

        return best_index

    def get_checkpoint_delta(self, old_checkpoint, new_checkpoint):
        delta = new_checkpoint - old_checkpoint

        if delta < -self.num_checkpoints / 2:
            delta += self.num_checkpoints

        elif delta > self.num_checkpoints / 2:
            delta -= self.num_checkpoints

        return delta

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

        if draw_checkpoints:
            self.draw_checkpoints(screen)

    def draw_checkpoints(self, screen):
        for checkpoint in self.checkpoints:
            p1, p2 = checkpoint

            p1_screen = self.track_to_screen(p1)
            p2_screen = self.track_to_screen(p2)

            pygame.draw.line(
                screen,
                (40, 40, 40),
                (int(p1_screen[0]), int(p1_screen[1])),
                (int(p2_screen[0]), int(p2_screen[1])),
                2,
            )