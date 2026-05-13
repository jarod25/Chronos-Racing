import numpy as np
import pygame


class RaySensor:
    def __init__(self, ray_count=21, fov=np.pi, max_distance=220, step=4):
        self.ray_count = ray_count
        self.fov = fov
        self.max_distance = max_distance
        self.step = step

    def get_ray_angles(self, car_angle):
        start_angle = car_angle - self.fov / 2
        end_angle = car_angle + self.fov / 2

        return np.linspace(start_angle, end_angle, self.ray_count)

    def cast_ray(self, circuit, car_pos, angle):
        for distance in range(0, self.max_distance, self.step):
            x = car_pos[0] + np.cos(angle) * distance
            y = car_pos[1] + np.sin(angle) * distance

            if not circuit.is_on_track((x, y)):
                return distance

        return self.max_distance

    def get_distances(self, circuit, car):
        distances = []

        for angle in self.get_ray_angles(car.angle):
            distance = self.cast_ray(circuit, car.pos, angle)
            distances.append(distance / self.max_distance)

        return distances

    def draw(self, screen, circuit, car):
        for angle in self.get_ray_angles(car.angle):
            distance = self.cast_ray(circuit, car.pos, angle)

            start_track_pos = car.pos

            end_track_pos = (
                car.pos[0] + np.cos(angle) * distance,
                car.pos[1] + np.sin(angle) * distance,
            )

            start_screen_pos = circuit.track_to_screen(start_track_pos)
            end_screen_pos = circuit.track_to_screen(end_track_pos)

            pygame.draw.line(
                screen,
                (0, 255, 0),
                (int(start_screen_pos[0]), int(start_screen_pos[1])),
                (int(end_screen_pos[0]), int(end_screen_pos[1])),
                1,
            )
