import os
import sys

import pygame

from car import Car
from circuit.ellipse_circuit import EllipseCircuit
from circuit.imported_circuit import ImportedCircuit
from config import *
from gui.file_browser import choose_import_image
from gui.menu import choose_circuit_mode
from gui.start_selector import choose_import_start_position, choose_start_position
from sensors.ray_sensor import RaySensor
from data_manager import add_run_result


def get_config(name, default):
    return globals().get(name, default)


class TrainingGame:
    def __init__(self, screen=None, ai_name="AI", load_path=None):
        self.ai_name = ai_name
        pygame.init()

        self.load_path = load_path
        self.best_save_filename = os.path.basename(load_path) if load_path is not None else None

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
        self.start_pos = np.array([self.car_start_x, self.car_start_y], dtype=float)
        self.expected_checkpoint_direction = 1
        self.start_area_radius = START_AREA_RADIUS

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

        self.is_generalist_run = False
        self.first_success_logged = False

        if load_path is not None:
            filename = os.path.basename(load_path)

            if filename.lower() == "generalist.npz":
                self.is_generalist_run = True


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
        start_pos, start_angle = choose_start_position(self.screen, self.clock, self.circuit,
                                                       (self.car_start_x, self.car_start_y))
        self.circuit.generate_start_line_from_point(start_pos)
        self.expected_checkpoint_direction = self.circuit.get_checkpoint_direction_from_angle(start_pos, start_angle)
        self.circuit_name = "ellipse"
        self.car_start_x, self.car_start_y, self.car_start_angle = start_pos[0], start_pos[1], start_angle
        self.start_pos = np.array(start_pos, dtype=float)

    def setup_imported_circuit(self):
        image_path = choose_import_image(self.screen, self.clock)
        if image_path is None:
            self.quit()
        self.circuit = ImportedCircuit(image_path=image_path, view_size=self.track_view_size,
                                       view_offset=self.track_view_offset)
        start_pos, start_angle = choose_import_start_position(self.screen, self.clock, self.circuit)
        self.expected_checkpoint_direction = self.circuit.get_checkpoint_direction_from_angle(start_pos, start_angle)
        self.circuit_name = os.path.splitext(os.path.basename(image_path))[0]
        self.car_start_x, self.car_start_y, self.car_start_angle = start_pos[0], start_pos[1], start_angle
        self.start_pos = np.array(start_pos, dtype=float)

    def reset_cars(self):
        self.cars = [Car(self.car_start_x, self.car_start_y, angle=self.car_start_angle) for _ in range(self.pop_size)]
        self.alive = [True] * self.pop_size
        for car in self.cars:
            start_checkpoint = self.circuit.get_checkpoint(car)
            car.score = 0
            car.start_checkpoint = start_checkpoint
            car.last_checkpoint = start_checkpoint
            car.checkpoint_progress = 0
            car.backward_frames = 0
            car.wrong_way_frames = 0
            car.has_left_start_area = False
            car.frames_since_spawn = 0
            car.death_reason = None
            car.stuck_frames = 0
            car.last_progress_pos = car.pos.copy()
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
        for i in range(self.pop_size):
            if not self.alive[i]:
                continue
            car = self.cars[i]
            car.frames_since_spawn += 1
            action = self.compute_action(self.ais[i], car)
            car.update(action)

            if self.simulation_steps > STUCK_GRACE_FRAMES:
                progress = float(np.linalg.norm(car.pos - car.last_progress_pos))
                if car.speed_kmh < STUCK_SPEED_KMH or progress < STUCK_POSITION_EPSILON:
                    car.stuck_frames += 1
                    car.score -= 0.15
                else:
                    car.stuck_frames = 0
                    car.last_progress_pos = car.pos.copy()

                if car.stuck_frames > STUCK_FRAME_LIMIT:
                    self.alive[i] = False
                    continue

            if not self.circuit.is_on_track(car.pos):
                self.alive[i] = False
                continue

            new_checkpoint = self.circuit.get_checkpoint(car)
            previous_wrong_way_frames = car.wrong_way_frames

            if self.is_wrong_way(car, new_checkpoint):
                car.score -= 200
                car.death_reason = "wrong way"
                self.alive[i] = False
                continue

            if car.wrong_way_frames > previous_wrong_way_frames:
                car.score -= 2.0 * car.wrong_way_frames

            self.update_checkpoint_progress(car, new_checkpoint)
            if car.backward_frames > BACKWARD_PROGRESS_LIMIT:
                car.death_reason = "backward"
                self.alive[i] = False
                continue

            self.update_lap_progress(car)
            car.score += (car.speed_kmh / car.max_speed_kmh) * 50 - 0.01

        if not any(self.alive) or self.finished:
            self.next_generation()

    def is_wrong_way(self, car, checkpoint):
        expected_forward = self.circuit.get_checkpoint_forward_vector(
            checkpoint,
            self.expected_checkpoint_direction,
        )
        if expected_forward is None:
            return False

        car_forward = np.array([np.cos(car.angle), np.sin(car.angle)])
        orientation_alignment = float(np.dot(car_forward, expected_forward))

        displacement = car.pos - car.prev_pos
        displacement_norm = float(np.linalg.norm(displacement))
        movement_alignment = 1.0
        if displacement_norm > 0.1:
            movement_alignment = float(np.dot(displacement / displacement_norm, expected_forward))

        wrong_orientation = orientation_alignment < WRONG_WAY_ALIGNMENT_LIMIT
        wrong_movement = movement_alignment < WRONG_WAY_MOVEMENT_LIMIT

        if car.speed_kmh > WRONG_WAY_SPEED_KMH and wrong_orientation and wrong_movement:
            car.wrong_way_frames += 1
        else:
            car.wrong_way_frames = max(0, car.wrong_way_frames - 3)

        return car.wrong_way_frames >= WRONG_WAY_FRAME_LIMIT

    def update_checkpoint_progress(self, car, new_checkpoint):
        raw_delta = self.circuit.get_checkpoint_delta(car.last_checkpoint, new_checkpoint)
        signed_delta = raw_delta * self.expected_checkpoint_direction

        if signed_delta > 0:
            car.checkpoint_progress += signed_delta
            car.score += 20 * signed_delta
            car.backward_frames = max(0, car.backward_frames - 2)
        elif signed_delta < 0:
            car.score -= 25 * abs(signed_delta)
            car.backward_frames += abs(signed_delta)

        car.last_checkpoint = new_checkpoint

    def update_lap_progress(self, car):
        distance_to_start = float(np.linalg.norm(car.pos - self.start_pos))
        if distance_to_start > self.start_area_radius:
            car.has_left_start_area = True

        needed_progress = max(1, len(self.circuit.checkpoints)) * MIN_LAP_PROGRESS_RATIO
        if car.frames_since_spawn < 5:
            return
        if not car.has_left_start_area or car.checkpoint_progress < needed_progress:
            return

        if not self.circuit.has_crossed_start_line(car.prev_pos, car.pos):
            return

        expected_forward = self.circuit.get_checkpoint_forward_vector(
            car.start_checkpoint,
            self.expected_checkpoint_direction,
        )
        if expected_forward is None:
            return

        displacement = car.pos - car.prev_pos
        crossed_forward = float(np.dot(displacement, expected_forward)) > 0
        if crossed_forward:
            self.finished = True
            self.winner_time = self.simulation_steps / self.fps

    def next_generation(self):
        scores = [car.score for car in self.cars]
        best_idx = int(np.argmax(scores))

        best_score = scores[best_idx]
        print(f"[GEN {self.generation}] Best score: {best_score:.2f}")
        if self.winner_time is not None and (self.best_time is None or self.winner_time < self.best_time):
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

        self.draw_debug_rays()
        best_display = "---" if self.best_time is None else f"{self.best_time:.2f}s"

        debug_idx = self.get_debug_car_index()

        if debug_idx is not None:
            speed_display = f"{self.cars[debug_idx].speed_kmh:.1f} km/h"
        else:
            speed_display = "---"

        text = self.font.render(
            f"AI: {self.ai_name} | Gen: {self.generation} | Alive: {sum(self.alive)} | Best: {best_display} | Speed: {speed_display}",
            True,
            (0, 0, 0)
)
        self.screen.blit(text, (10, 10))

    def get_debug_car_index(self):
        alive_indexes = [i for i, is_alive in enumerate(self.alive) if is_alive]
        if not alive_indexes:
            return None
        if self.pop_size == 1:
            return alive_indexes[0]
        best_alive = max(alive_indexes, key=lambda idx: self.cars[idx].score)
        return best_alive

    def draw_debug_rays(self):
        debug_idx = self.get_debug_car_index()
        if debug_idx is None:
            return
        self.sensor.draw(self.screen, self.circuit, self.cars[debug_idx])

    def quit(self):
        pygame.quit()
        sys.exit()
