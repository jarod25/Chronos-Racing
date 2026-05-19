import numpy as np
import pygame

from gui.colors import LIGHT_BACKGROUND


class ImportedCircuit:
    def __init__(
            self,
            image_path,
            view_size,
            view_offset=(0, 0),
            checkpoint_spacing=10,
            checkpoint_depth=300,
    ):
        self.image_path = image_path

        self.width = view_size[0]
        self.height = view_size[1]

        self.offset_x = view_offset[0]
        self.offset_y = view_offset[1]

        self.checkpoint_spacing = checkpoint_spacing
        self.checkpoint_depth = checkpoint_depth

        loaded_image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.smoothscale(loaded_image, view_size)

        self.track_mask = None
        self.mask_pixel_count = 0

        self.checkpoints = []

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
    
    # TRACK MASK GENERATION

    def generate_track_mask_from_point(self, pos):
        if not self.is_inside_view(pos):
            return 0

        x = int(pos[0])
        y = int(pos[1])

        selected_color = self.image.get_at((x, y))

        if selected_color.a <= 10:
            self.track_mask = None
            self.mask_pixel_count = 0
            self.checkpoints = []
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

        # Generate checkpoints

        self.checkpoints = self.generate_checkpoints()
        print("outline points:", len(self.track_mask.outline()))
        print("generated checkpoints:", len(self.checkpoints))

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


    # CHECKPOINT GENERATION

    def segments_intersect(self, a1, a2, b1, b2):
        def ccw(p1, p2, p3):
            return ((p3[1] - p1[1]) * (p2[0] - p1[0]) > (p2[1] - p1[1]) * (p3[0] - p1[0]))
        return (ccw(a1, b1, b2) != ccw(a2, b1, b2) and ccw(a1, a2, b1) != ccw(a1, a2, b2))

    def generate_checkpoints(self):
        if self.track_mask is None:
            return []

        checkpoints = []

        # outline

        outline = self.track_mask.outline()

        if len(outline) < 3:
            return []

        accumulated_distance = 0

        for i in range(len(outline)):
            current = outline[i]
            next_point = outline[(i + 1) % len(outline)]

            segment_length = np.hypot(
                next_point[0] - current[0],
                next_point[1] - current[1],
            )

            accumulated_distance += segment_length

            if accumulated_distance < self.checkpoint_spacing:
                continue

            accumulated_distance = 0

            prev_point = outline[i - 1]
            next_point = outline[(i + 1) % len(outline)]

            # Tangente locale

            tx = next_point[0] - prev_point[0]
            ty = next_point[1] - prev_point[1]

            tangent_norm = np.hypot(tx, ty)

            if tangent_norm == 0:
                continue

            tx /= tangent_norm
            ty /= tangent_norm

            # Normale

            nx = -ty
            ny = tx

            test_x = current[0] + nx * 5
            test_y = current[1] + ny * 5

            if not self.is_on_track((test_x, test_y)):
                nx = -nx
                ny = -ny

            # Raycast intérieur

            last_valid = current

            for d in range(self.checkpoint_depth):
                x = current[0] + nx * d
                y = current[1] + ny * d

                if self.is_on_track((x, y)):
                    last_valid = (x, y)
                else:
                    break

            new_checkpoint = (
                current,
                last_valid,
            )

            intersects = False

            for existing in checkpoints:
                e1, e2 = existing

                if self.segments_intersect(
                        current,
                        last_valid,
                        e1,
                        e2,
                ):
                    intersects = True
                    break

            if not intersects:
                checkpoints.append(new_checkpoint)

        return checkpoints

    def get_state(self, car):
        x = car.pos[0] / self.width
        y = car.pos[1] / self.height

        return [
            x,
            y,
            np.cos(car.angle),
            np.sin(car.angle),
        ]

    # CHECKPOINT QUERY

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

            distance = np.linalg.norm(
                car_pos - np.array(midpoint)
            )

            if distance < best_distance:
                best_distance = distance
                best_index = i

        return best_index

    def get_checkpoint_delta(
            self,
            old_checkpoint,
            new_checkpoint,
    ):
        checkpoint_count = len(self.checkpoints)

        if checkpoint_count == 0:
            return 0

        delta = new_checkpoint - old_checkpoint

        if delta < -checkpoint_count / 2:
            delta += checkpoint_count

        elif delta > checkpoint_count / 2:
            delta -= checkpoint_count

        return delta
    
    # DRAW

    def draw(self, screen, draw_checkpoints=False):
        screen.fill(LIGHT_BACKGROUND)

        screen.blit(
            self.image,
            (self.offset_x, self.offset_y),
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
                (255, 0, 0),
                (int(p1_screen[0]), int(p1_screen[1])),
                (int(p2_screen[0]), int(p2_screen[1])),
                2,
            )

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