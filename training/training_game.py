import os
import sys

import pygame
import numpy as np

from car import Car
from circuit.ellipse_circuit import EllipseCircuit
from circuit.imported_circuit import ImportedCircuit
from config import *
from gui.file_browser import choose_import_image
from gui.menu import choose_circuit_mode
from gui.start_selector import choose_import_start_position, choose_start_position
from sensors.ray_sensor import RaySensor


def get_config(name, default):
    return globals().get(name, default)


class TrainingGame:
    def __init__(self, screen=None, ai_name="AI", load_path=None):
        self.ai_name = ai_name
        pygame.init()

        self.load_path = load_path

        self.screen_width = get_config("WINDOW_WIDTH", 800)
        self.screen_height = get_config("WINDOW_HEIGHT", 600)
        self.fps = get_config("FPS", 60)

        self.track_view_size = (
            get_config("TRACK_VIEW_WIDTH", self.screen_width),
            get_config("TRACK_VIEW_HEIGHT", self.screen_height),
        )
        self.track_view_offset = (
            get_config("TRACK_OFFSET_X", 0),
            get_config("TRACK_OFFSET_Y", 0),
        )

        self.track_center_x = get_config("TRACK_CENTER_X", 400)
        self.track_center_y = get_config("TRACK_CENTER_Y", 300)
        self.track_length = get_config("TRACK_LENGTH", 560)
        self.track_height = get_config("TRACK_HEIGHT", 340)
        self.track_width = get_config("TRACK_WIDTH", 50)
        self.border_thickness = get_config("BORDER_THICKNESS", 4)

        self.car_start_x = get_config("CAR_START_X", 400)
        self.car_start_y = get_config("CAR_START_Y", 170)
        self.car_start_angle = get_config("CAR_START_ANGLE", 0)

        self.pop_size = get_config("POP_SIZE", 20)

        if screen is None:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        else:
            self.screen = screen
        pygame.display.set_caption(f"Chronos Racing - {self.ai_name.title()} Training")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)

        self.sensor = RaySensor(
            ray_count=get_config("RAY_COUNT", 21),
            fov=get_config("RAY_FOV", np.pi),
            max_distance=get_config("RAY_MAX_DISTANCE", 220),
            step=get_config("RAY_STEP", 4),
        )

        self.input_size = self.sensor.ray_count + 3
        self.circuit = None
        self.circuit_name = None

        self.best_time = None
        self.best_ai = None
        self.generation = 1

        self.ais = self.create_population()
        self.best_ai = self.ais[0]

        self.cars = []
        self.alive = []
        self.finished = False
        self.winner_time = None
        self.simulation_steps = 0

        self.running = True
        self.setup()
        self.reset_cars()

    def create_population(self):
        raise NotImplementedError

    def compute_action(self, ai, car):
        raise NotImplementedError

    def on_new_best(self, best_ai):
        return None

    def evolve(self, scores):
        return None

    def setup(self):
        circuit_mode = choose_circuit_mode(self.screen, self.clock)
        if circuit_mode == "default":
            self.setup_default_circuit()
        elif circuit_mode == "import":
            self.setup_imported_circuit()
        else:
            self.quit()

    def setup_default_circuit(self):
        self.circuit = EllipseCircuit(
            center_x=self.track_center_x,
            center_y=self.track_center_y,
            length=self.track_length,
            height=self.track_height,
            width=self.track_width,
            border_thickness=self.border_thickness,
            view_size=self.track_view_size,
            view_offset=self.track_view_offset,
        )
        start_pos, start_angle = choose_start_position(self.screen, self.clock, self.circuit, (self.car_start_x, self.car_start_y))
        self.circuit_name = "ellipse"
        self.car_start_x, self.car_start_y, self.car_start_angle = start_pos[0], start_pos[1], start_angle

    def setup_imported_circuit(self):
        image_path = choose_import_image(self.screen, self.clock)
        if image_path is None:
            self.quit()
        self.circuit = ImportedCircuit(image_path=image_path, view_size=self.track_view_size, view_offset=self.track_view_offset)
        start_pos, start_angle = choose_import_start_position(self.screen, self.clock, self.circuit)
        self.circuit_name = os.path.splitext(os.path.basename(image_path))[0]
        self.car_start_x, self.car_start_y, self.car_start_angle = start_pos[0], start_pos[1], start_angle

    def reset_cars(self):
        self.cars = [Car(self.car_start_x, self.car_start_y, angle=self.car_start_angle) for _ in range(self.pop_size)]
        self.alive = [True] * self.pop_size
        for car in self.cars:
            car.speed_kmh = 350.0
            car.score = 0
            car.total_checkpoints = 0
            car.last_checkpoint = 0
        self.finished = False
        self.winner_time = None
        self.simulation_steps = 0

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(self.fps)
        self.quit()

    def update(self):
        self.simulation_steps += 1
        all_dead = True
        for i in range(self.pop_size):
            if not self.alive[i]:
                continue
            all_dead = False
            car = self.cars[i]
            action = self.compute_action(self.ais[i], car)
            car.update(action)
            if not self.circuit.is_on_track(car.pos):
                self.alive[i] = False
                continue
            new_checkpoint = self.circuit.get_checkpoint(car)
            if new_checkpoint != car.last_checkpoint:
                car.score += 20
                car.total_checkpoints += 1
                if car.total_checkpoints > self.circuit.num_checkpoints:
                    self.finished = True
                    self.winner_time = self.simulation_steps / self.fps
            car.last_checkpoint = new_checkpoint
            car.score += (car.speed_kmh / car.max_speed_kmh) * 50 - 0.01

        if all_dead or self.finished:
            self.next_generation()

    def next_generation(self):
        scores = [car.score for car in self.cars]
        best_idx = int(np.argmax(scores))
        if self.winner_time is not None and self.winner_time < self.best_time:
            self.best_time = self.winner_time
            self.best_ai = self.ais[best_idx]
            self.on_new_best(self.best_ai)
        self.evolve(scores)
        self.generation += 1
        self.reset_cars()

    def draw(self):
        self.circuit.draw(screen=self.screen, draw_checkpoints=True)
        for i, car in enumerate(self.cars):
            color = (255, 255, 255) if self.alive[i] else (70, 70, 70)
            p = self.circuit.track_to_screen(car.pos)
            pygame.draw.circle(self.screen, color, (int(p[0]), int(p[1])), 4)
        best_display = "---" if self.best_time is None else f"{self.best_time:.2f}s"
        text = self.font.render(
            f"AI: {self.ai_name} | Gen: {self.generation} | Alive: {sum(self.alive)} | Best: {best_display}",
            True,
            (0, 0, 0)
        )
        self.screen.blit(text, (10, 10))

    def quit(self):
        pygame.quit()
        sys.exit()
