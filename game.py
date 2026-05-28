import json
import os
import re
import sys

import pygame

from ai.ai_controller import create_ai_controller
from car import Car
from circuit.ellipse_circuit import EllipseCircuit
from circuit.imported_circuit import ImportedCircuit
from config import *
from gui.file_browser import choose_import_image
from gui.menu import choose_circuit_mode
from gui.renderer import draw_game
from gui.start_selector import choose_start_position, choose_import_start_position
from sensors.ray_sensor import RaySensor


class ChronosGame:
    def __init__(self, screen=None, ai_name="simple", load_path=None):
        pygame.init()

        if screen is None:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        else:
            self.screen = screen
        pygame.display.set_caption("Chronos Racing - Racing Simulator")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)

        self.track_view_size = (TRACK_VIEW_WIDTH, TRACK_VIEW_HEIGHT)
        self.track_view_offset = (TRACK_OFFSET_X, TRACK_OFFSET_Y)
        self.show_checkpoints = True

        self.button_font = pygame.font.SysFont(None, 28)
        self.checkpoints_button_rect = pygame.Rect(20, 20, 230, 42)

        self.circuit = None
        self.car = None

        self.ai_name = ai_name
        self.sensor = RaySensor(
            ray_count=RAY_COUNT,
            fov=RAY_FOV,
            max_distance=RAY_MAX_DISTANCE,
            step=RAY_STEP,
        )

        self.ai_controller = create_ai_controller(
            ai_name=ai_name,
            load_path=load_path,
        )

        self.running = True
        self.crashed = False

        self.start_pos = None
        self.start_angle = 0.0
        self.finish_radius = 50.0
        self.has_left_start_zone = False
        self.was_in_start_zone = True
        self.generation = 1
        self.lap_start_time = 0.0
        self.current_lap_time = 0.0
        self.best_lap_time = None
        self.best_save_path = None
        self.min_valid_lap_time = 2.0

    def setup(self):
        circuit_mode = choose_circuit_mode(self.screen, self.clock)

        if circuit_mode == "default":
            self.setup_default_circuit()

        elif circuit_mode == "import":
            self.setup_imported_circuit()

        else:
            self.quit()

        self.start_pos = self.car.pos.copy()
        self.lap_start_time = pygame.time.get_ticks() / 1000.0

    def setup_default_circuit(self):
        self.circuit = EllipseCircuit(
            center_x=TRACK_CENTER_X,
            center_y=TRACK_CENTER_Y,
            length=TRACK_LENGTH,
            height=TRACK_HEIGHT,
            width=TRACK_WIDTH,
            border_thickness=BORDER_THICKNESS,
            view_size=self.track_view_size,
            view_offset=self.track_view_offset,
        )

        start_pos, start_angle = choose_start_position(
            screen=self.screen,
            clock=self.clock,
            circuit=self.circuit,
            default_pos=(CAR_START_X, CAR_START_Y),
        )

        self.circuit.generate_start_line_from_point(start_pos)
        self.car = Car(start_pos[0], start_pos[1], angle=start_angle)
        self.start_angle = start_angle

    def setup_imported_circuit(self):
        image_path = choose_import_image(self.screen, self.clock)

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

        self.car = Car(start_pos[0], start_pos[1], angle=start_angle)
        self.start_angle = start_angle

    @staticmethod
    def _sanitize_filename(value):
        value = str(value).strip().lower()
        value = re.sub(r"[^a-z0-9._-]+", "_", value)
        return value.strip("_") or "unknown"

    def _circuit_name(self):
        for attr in ("name", "circuit_name", "filename", "track_name"):
            if hasattr(self.circuit, attr):
                v = getattr(self.circuit, attr)
                if v:
                    return self._sanitize_filename(os.path.basename(str(v)))
        if isinstance(self.circuit, EllipseCircuit):
            return "ellipse"
        if isinstance(self.circuit, ImportedCircuit):
            return "imported"
        return "unknown_circuit"

    def _save_best_if_needed(self, lap_time):
        if self.ai_name not in ("physics", "heuristic"):
            return
        if self.best_lap_time is not None and lap_time >= self.best_lap_time:
            return

        self.best_lap_time = lap_time
        os.makedirs("saves", exist_ok=True)

        if hasattr(self.ai_controller, "ai") and hasattr(self.ai_controller.ai, "sector_memory"):
            sector_memory = self.ai_controller.ai.sector_memory
        elif hasattr(self.ai_controller, "sector_memory"):
            sector_memory = self.ai_controller.sector_memory
        else:
            sector_memory = {}

        serial_memory = {str(k): v for k, v in sector_memory.items()}
        circuit_name = self._circuit_name()
        ai_label = "physics"
        filename = f"{ai_label}_{circuit_name}_{lap_time:.2f}.json"
        path = os.path.join("saves", filename)

        if self.best_save_path is not None and self.best_save_path != path and os.path.exists(self.best_save_path):
            os.remove(self.best_save_path)

        payload = {
            "ai_name": ai_label,
            "circuit_name": circuit_name,
            "best_lap_time": round(lap_time, 4),
            "generation": self.generation,
            "sector_memory": serial_memory,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        self.best_save_path = path

    def _update_lap_logic(self):
        now = pygame.time.get_ticks() / 1000.0
        self.current_lap_time = now - self.lap_start_time

        if self.start_pos is None:
            return

        distance_to_start = np.linalg.norm(self.car.pos - self.start_pos)
        in_start_zone = distance_to_start < self.finish_radius

        if not in_start_zone:
            self.has_left_start_zone = True

        just_entered_zone = in_start_zone and not self.was_in_start_zone

        if just_entered_zone and self.has_left_start_zone:
            lap_time = self.current_lap_time
            if lap_time >= self.min_valid_lap_time:
                self.generation += 1
                self._save_best_if_needed(lap_time)
                self.lap_start_time = now
                self.current_lap_time = 0.0
            self.has_left_start_zone = False

        self.was_in_start_zone = in_start_zone

    def run(self):
        self.setup()

        while self.running:
            self.handle_events()
            self.update()
            self.draw()

            pygame.display.flip()
            self.clock.tick(FPS)

        self.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    event.size,
                    pygame.RESIZABLE,
                )
                self.update_layout()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.checkpoints_button_rect.collidepoint(event.pos):
                    self.show_checkpoints = not self.show_checkpoints

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset_car()

    def reset_car(self):
        self.car.pos = self.start_pos.copy()
        self.car.prev_pos = self.start_pos.copy()
        self.car.angle = float(self.start_angle)
        self.car.speed_kmh = 0.0
        self.crashed = False
        self.has_left_start_zone = False
        self.was_in_start_zone = True
        self.lap_start_time = pygame.time.get_ticks() / 1000.0
        self.current_lap_time = 0.0

    def update_layout(self):
        self.track_view_offset = (
            (self.screen.get_width() - self.track_view_size[0]) // 2,
            TRACK_OFFSET_Y,
        )

        if self.circuit is not None:
            self.circuit.offset_x = self.track_view_offset[0]
            self.circuit.offset_y = self.track_view_offset[1]

    def update(self):
        if self.crashed:
            return

        action = self.ai_controller.get_action(
            circuit=self.circuit,
            car=self.car,
            sensor=self.sensor,
        )

        self.car.update(action)
        self._update_lap_logic()

        if not self.circuit.is_on_track(self.car.pos):
            self.crashed = True
            print("Collision: car is off track.")

    def _physics_hud_line(self):
        best = "---" if self.best_lap_time is None else f"{self.best_lap_time:.2f}s"
        speed = int(round(getattr(self.car, "speed_kmh", 0.0)))
        return f"AI: physics | Gen: {self.generation} | Lap: {self.current_lap_time:.2f}s | Best: {best} | Speed: {speed} km/h"

    def draw(self):
        self.update_layout()

        hud_text = None
        if self.ai_name in "physics":
            hud_text = self._physics_hud_line()

        draw_game(
            screen=self.screen,
            circuit=self.circuit,
            car=self.car,
            crashed=self.crashed,
            font=self.font,
            button_font=self.button_font,
            checkpoints_button_rect=self.checkpoints_button_rect,
            show_checkpoints=self.show_checkpoints,
            sensor=self.sensor,
            draw_rays=DRAW_RAYS,
            hud_text=hud_text,
        )

    def quit(self):
        pygame.quit()
        sys.exit()
