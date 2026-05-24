import sys

import pygame

from ai.genetic_ai import GeneticAI
from car import Car
from circuit.ellipse_circuit import EllipseCircuit
from circuit.imported_circuit import ImportedCircuit
from config import *
from gui.file_browser import choose_import_image
from gui.menu import choose_circuit_mode
from gui.start_selector import (choose_start_position, choose_import_start_position, )
from save_manager import load_ai, replace_best_save
from sensors.ray_sensor import RaySensor


def get_config(name, default):
    return globals().get(name, default)


class GeneticTrainingGame:
    def __init__(self, load_path=None):
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

        self.pop_size = get_config("POP_SIZE", 50)

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Chronos Racing - Genetic AI Training")

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

        self.best_time = 100.0
        self.best_ai = None
        self.generation = 1

        self.ais = self.create_population()
        self.best_ai = self.ais[0]

        self.cars = []
        self.alive = []

        self.finished = False
        self.winner_time = None
        self.start_frame = pygame.time.get_ticks()
        self.simulation_steps = 0

        self.running = True
        self.setup()

        self.reset_cars()

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

        start_pos, start_angle = choose_start_position(
            screen=self.screen,
            clock=self.clock,
            circuit=self.circuit,
            default_pos=(
                self.car_start_x,
                self.car_start_y,
            ),
        )

        self.car_start_x = start_pos[0]
        self.car_start_y = start_pos[1]

    def setup_imported_circuit(self):
        image_path = choose_import_image(
            self.screen,
            self.clock,
        )

        if image_path is None:
            self.quit()

        self.circuit = ImportedCircuit(
            image_path=image_path,
            view_size=self.track_view_size,
            view_offset=self.track_view_offset,
        )

        start_pos, start_angle = choose_import_start_position(
            screen=self.screen,
            clock=self.clock,
            circuit=self.circuit,
        )

        self.car_start_x = start_pos[0]
        self.car_start_y = start_pos[1]
        self.car_start_angle = start_angle

    def create_population(self):
        if self.load_path is not None:
            print(f"\nLoading AI: {self.load_path}")

            base_ai = load_ai(GeneticAI, self.load_path)
            ais = [base_ai.copy() for _ in range(self.pop_size)]

            for i in range(1, self.pop_size):
                ais[i].mutate(rate=0.02)

            print("Population generated from save.\n")

            return ais

        return [
            GeneticAI(input_size=self.input_size)
            for _ in range(self.pop_size)
        ]

    def reset_cars(self):
        self.cars = [
            Car(self.car_start_x, self.car_start_y, angle=self.car_start_angle)
            for _ in range(self.pop_size)
        ]

        self.alive = [True] * self.pop_size

        for car in self.cars:
            car.score = 0
            car.checkpoint = self.circuit.get_checkpoint(car)
            car.total_checkpoints = 0
            car.last_checkpoint = 0
            car.lap_completed = False
            car.progress = 0

        self.finished = False
        self.winner_time = None
        self.simulation_steps = 0

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()

            pygame.display.flip()
            self.clock.tick(self.fps)

        self.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def build_vision(self, car):
        vision = self.sensor.get_distances(self.circuit, car)

        vision.append(car.speed_kmh / car.max_speed_kmh)
        vision.append(np.sin(car.angle))
        vision.append(np.cos(car.angle))

        return np.array(vision)

    def update(self):
        self.simulation_steps += 1
        all_dead = True

        for i in range(self.pop_size):
            if not self.alive[i]:
                continue

            all_dead = False

            car = self.cars[i]
            ai = self.ais[i]

            vision = self.build_vision(car)

            action = ai.forward(vision)

            action += np.random.randn(2) * 0.02
            action = np.clip(action, -1, 1)

            car.update(action)

            self.update_score(car)

            if not self.circuit.is_on_track(car.pos):
                car.score -= 100
                self.alive[i] = False

        if all_dead or self.finished:
            self.next_generation()

    def update_score(self, car):

        new_checkpoint = self.circuit.get_checkpoint(car)

        # progression normale
        if new_checkpoint != car.last_checkpoint:
            car.score += 10
            car.total_checkpoints += 1

            # détecte progression de tour
            if car.total_checkpoints > self.circuit.num_checkpoints:
                car.lap_completed = True
                self.finished = True

                self.winner_time = self.simulation_steps / self.fps
                car.score += 1000

                print(f"LAP COMPLETED! Time: {self.winner_time:.2f}s")

        car.last_checkpoint = new_checkpoint

        # rewards classiques
        car.score -= 0.01
        car.score += (car.speed_kmh / car.max_speed_kmh) * 0.6

    def next_generation(self):
        print(f"\n=== GENERATION {self.generation} ===")

        scores = [car.score for car in self.cars]

        best_idx = int(np.argmax(scores))
        best_gen_score = scores[best_idx]

        print(f"Best score this generation: {best_gen_score}")
        print(f"Best global time: {self.best_time:.2f}s")
        print("--------------------")

        if self.winner_time is not None:

            if self.winner_time < self.best_time:
                old_filename = None

                if self.best_time != float("inf"):
                    old_filename = f"time_{self.best_time:.2f}.npz"

                self.best_time = self.winner_time
                self.best_ai = self.ais[best_idx].copy()

                print("NEW BEST TIME!")

                replace_best_save(ai=self.best_ai, new_filename=f"time_{self.best_time:.2f}.npz",
                                  old_filename=old_filename)

        sorted_idx = np.argsort(scores)[::-1]

        parent_count = min(20, len(sorted_idx))
        parents = sorted_idx[:parent_count]

        new_ais = [self.ais[parents[0]].copy()]

        while len(new_ais) < self.pop_size:
            parent = self.ais[np.random.choice(parents)]
            child = parent.copy()

            r = np.random.rand()

            if r < 0.7:
                rate = 0.02
            elif r < 0.95:
                rate = 0.05
            else:
                rate = 0.15

            child.mutate(rate=rate)

            new_ais.append(child)

        self.ais = new_ais
        self.generation += 1

        self.reset_cars()

    def draw(self):
        self.circuit.draw(
            screen=self.screen,
            draw_checkpoints=True,
        )

        for i, car in enumerate(self.cars):
            if self.alive[i]:
                color = (255, 255, 255)
            else:
                color = (70, 70, 70)

            screen_pos = self.circuit.track_to_screen(car.pos)

            pygame.draw.circle(
                self.screen,
                color,
                (int(screen_pos[0]), int(screen_pos[1])),
                4,
            )

        best_alive = next((i for i in range(self.pop_size) if self.alive[i]), None)

        if best_alive is not None:
            self.sensor.draw(
                screen=self.screen,
                circuit=self.circuit,
                car=self.cars[best_alive],
            )

        text = self.font.render(
            f"Gen: {self.generation} | Alive: {sum(self.alive)} | Best: {self.best_time:.2f}s",
            True,
            (0, 0, 0),
        )

        self.screen.blit(text, (10, 10))

    def quit(self):
        pygame.quit()
        sys.exit()
