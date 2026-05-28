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

    def get_checkpoint_at_pos(self, pos):
        if len(self.checkpoints) == 0:
            return 0

        car_pos = np.array(pos)

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

    def get_checkpoint(self, car):
        return self.get_checkpoint_at_pos(car.pos)

    def get_checkpoint_midpoint(self, checkpoint_index):
        checkpoint_count = len(self.checkpoints)

        if checkpoint_count == 0:
            return None

        p1, p2 = self.checkpoints[checkpoint_index % checkpoint_count]

        return np.array([
            (p1[0] + p2[0]) / 2,
            (p1[1] + p2[1]) / 2,
        ], dtype=float)

    def get_checkpoint_forward_vector(self, checkpoint_index, expected_direction=1):
        checkpoint_count = len(self.checkpoints)

        if checkpoint_count == 0:
            return None

        current_idx = checkpoint_index % checkpoint_count
        step = 1 if expected_direction >= 0 else -1
        next_idx = (current_idx + step) % checkpoint_count

        current_midpoint = self.get_checkpoint_midpoint(current_idx)
        next_midpoint = self.get_checkpoint_midpoint(next_idx)

        if current_midpoint is None or next_midpoint is None:
            return None

        vector = next_midpoint - current_midpoint
        norm = np.linalg.norm(vector)

        if norm == 0:
            return None

        return vector / norm

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

    def get_checkpoint_direction_from_angle(self, start_pos, start_angle):
        start_checkpoint = self.get_checkpoint_at_pos(start_pos)
        direction = np.array([
            np.cos(start_angle),
            np.sin(start_angle),
        ])

        for distance in (20, 40, 80):
            ahead_pos = np.array(start_pos) + direction * distance
            ahead_checkpoint = self.get_checkpoint_at_pos(ahead_pos)
            delta = self.get_checkpoint_delta(start_checkpoint, ahead_checkpoint)

            if delta > 0:
                return 1
            if delta < 0:
                return -1

        return 1

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

    def has_crossed_start_line(self, previous_pos, current_pos):
        if self.start_line is None:
            return False

        def orientation(a, b, c):
            return (
                    (b[0] - a[0]) * (c[1] - a[1])
                    - (b[1] - a[1]) * (c[0] - a[0])
            )

        def on_segment(a, b, c):
            return (
                    min(a[0], c[0]) <= b[0] <= max(a[0], c[0])
                    and min(a[1], c[1]) <= b[1] <= max(a[1], c[1])
            )

        a1 = np.array(previous_pos, dtype=float)
        a2 = np.array(current_pos, dtype=float)
        b1 = np.array(self.start_line[0], dtype=float)
        b2 = np.array(self.start_line[1], dtype=float)

        o1 = orientation(a1, a2, b1)
        o2 = orientation(a1, a2, b2)
        o3 = orientation(b1, b2, a1)
        o4 = orientation(b1, b2, a2)
        epsilon = 1e-9

        if o1 * o2 < 0 and o3 * o4 < 0:
            return True

        if abs(o1) <= epsilon and on_segment(a1, b1, a2):
            return True
        if abs(o2) <= epsilon and on_segment(a1, b2, a2):
            return True
        if abs(o3) <= epsilon and on_segment(b1, a1, b2):
            return True
        if abs(o4) <= epsilon and on_segment(b1, a2, b2):
            return True

        return False

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
