import sys
import warnings

import pygame

from ai import SimpleAI
from car import Car
from circuit.ellipse_circuit import EllipseCircuit
from circuit.imported_circuit import ImportedCircuit
from config import *
from gui.file_browser import choose_import_image
from gui.menu import choose_circuit_mode
from gui.renderer import draw_game
from gui.start_selector import choose_start_position, choose_import_start_position
from sensors.ray_sensor import RaySensor


warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
)


class ChronosGame:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Chronos Racing - V1")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)

        self.track_view_size = (TRACK_VIEW_WIDTH, TRACK_VIEW_HEIGHT)
        self.track_view_offset = (TRACK_OFFSET_X, TRACK_OFFSET_Y)

        self.circuit = None
        self.car = None

        self.sensor = RaySensor(
            ray_count=RAY_COUNT,
            fov=RAY_FOV,
            max_distance=RAY_MAX_DISTANCE,
            step=RAY_STEP,
        )

        self.ai = SimpleAI(1.8)

        self.running = True
        self.crashed = False

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

        self.car = Car(start_pos[0], start_pos[1], angle=start_angle)

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

    def update(self):
        if self.crashed:
            return

        vision = self.sensor.get_distances(self.circuit, self.car)
        action = self.ai.forward(vision)

        self.car.update(action)

        if not self.circuit.is_on_track(self.car.pos):
            self.crashed = True
            print("Collision: car is off track.")

    def draw(self):
        draw_game(
            screen=self.screen,
            circuit=self.circuit,
            car=self.car,
            crashed=self.crashed,
            font=self.font,
            sensor=self.sensor,
            draw_rays=DRAW_RAYS,
        )

    def quit(self):
        pygame.quit()
        sys.exit()