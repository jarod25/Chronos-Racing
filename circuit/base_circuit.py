import numpy as np
import pygame

from gui.colors import RED, WHITE


class BaseCircuit:
    def __init__(
            self,
            view_size,
            view_offset=(0, 0),
            checkpoint_depth=300,
    ):
        self.view_width = view_size[0]
        self.view_height = view_size[1]

        self.offset_x = view_offset[0]
        self.offset_y = view_offset[1]

        self.checkpoint_depth = checkpoint_depth

        self.checkpoints = []

        self.start_line = None
        self.start_line_width = 8

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
        raise NotImplementedError

    def get_outline_points(self):
        raise NotImplementedError

    def segments_intersect(self, a1, a2, b1, b2):
        def ccw(p1, p2, p3):
            return (
                    (p3[1] - p1[1]) * (p2[0] - p1[0])
                    > (p2[1] - p1[1]) * (p3[0] - p1[0])
            )

        return (
                ccw(a1, b1, b2) != ccw(a2, b1, b2)
                and ccw(a1, a2, b1) != ccw(a1, a2, b2)
        )

    def create_perpendicular_track_line(self, outline, index):
        current = outline[index]
        prev_point = outline[index - 1]
        next_point = outline[(index + 1) % len(outline)]

        tx = next_point[0] - prev_point[0]
        ty = next_point[1] - prev_point[1]

        tangent_norm = np.hypot(tx, ty)

        if tangent_norm == 0:
            return None

        tx /= tangent_norm
        ty /= tangent_norm

        nx = -ty
        ny = tx

        test_x = current[0] + nx * 5
        test_y = current[1] + ny * 5

        if not self.is_on_track((test_x, test_y)):
            nx = -nx
            ny = -ny

        last_valid = current

        for d in range(int(self.checkpoint_depth)):
            x = current[0] + nx * d
            y = current[1] + ny * d

            if self.is_on_track((x, y)):
                last_valid = (x, y)
            else:
                break

        return current, last_valid

    def generate_checkpoints_from_outline(
            self,
            outline,
            checkpoint_spacing=None,
            avoid_intersections=False,
    ):
        if len(outline) < 3:
            return []

        checkpoints = []
        accumulated_distance = 0

        for i in range(len(outline)):
            if checkpoint_spacing is not None:
                current = outline[i]
                next_point = outline[(i + 1) % len(outline)]

                segment_length = np.hypot(
                    next_point[0] - current[0],
                    next_point[1] - current[1],
                )

                accumulated_distance += segment_length

                if accumulated_distance < checkpoint_spacing:
                    continue

                accumulated_distance = 0

            checkpoint = self.create_perpendicular_track_line(outline, i)

            if checkpoint is None:
                continue

            current, last_valid = checkpoint

            if avoid_intersections:
                intersects = False

                for existing in checkpoints:
                    e1, e2 = existing

                    if self.segments_intersect(current, last_valid, e1, e2):
                        intersects = True
                        break

                if intersects:
                    continue

            checkpoints.append(checkpoint)

        return checkpoints

    def get_checkpoint(self, car):
        if len(self.checkpoints) == 0:
            return 0

        car_pos = np.array(car.pos)

        best_index = 0
        best_distance = float("inf")

        for i, checkpoint in enumerate(self.checkpoints):
            p1, p2 = checkpoint

            midpoint = (
                (p1[0] + p2[0]) / 2,
                (p1[1] + p2[1]) / 2,
            )

            distance = np.linalg.norm(car_pos - np.array(midpoint))

            if distance < best_distance:
                best_distance = distance
                best_index = i

        return best_index

    def get_checkpoint_delta(self, old_checkpoint, new_checkpoint):
        checkpoint_count = len(self.checkpoints)

        if checkpoint_count == 0:
            return 0

        delta = new_checkpoint - old_checkpoint

        if delta < -checkpoint_count / 2:
            delta += checkpoint_count

        elif delta > checkpoint_count / 2:
            delta -= checkpoint_count

        return delta

    def generate_start_line_from_point(self, pos):
        self.start_line = None

        if not self.is_inside_view(pos):
            return

        if not self.is_on_track(pos):
            return

        outline = self.get_outline_points()

        if len(outline) < 3:
            return

        closest_index = min(
            range(len(outline)),
            key=lambda i: (
                    (outline[i][0] - pos[0]) ** 2
                    + (outline[i][1] - pos[1]) ** 2
            ),
        )

        self.start_line = self.create_perpendicular_track_line(outline, closest_index)

    def draw_start_line(self, screen):
        if self.start_line is None:
            return

        p1, p2 = self.start_line

        p1_screen = self.track_to_screen(p1)
        p2_screen = self.track_to_screen(p2)

        pygame.draw.line(
            screen,
            WHITE,
            (int(p1_screen[0]), int(p1_screen[1])),
            (int(p2_screen[0]), int(p2_screen[1])),
            self.start_line_width,
        )

    def draw_checkpoints(self, screen):
        for checkpoint in self.checkpoints:
            p1, p2 = checkpoint

            p1_screen = self.track_to_screen(p1)
            p2_screen = self.track_to_screen(p2)

            pygame.draw.line(
                screen,
                RED,
                (int(p1_screen[0]), int(p1_screen[1])),
                (int(p2_screen[0]), int(p2_screen[1])),
                2,
            )
