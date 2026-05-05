import warnings

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
)

import pygame
import sys

from car import Car
from circuit import Circuit
from ai import SimpleMLP


# =========================
# CONFIG
# =========================

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

TRACK_CENTER_X = 400
TRACK_CENTER_Y = 300
TRACK_WIDTH = 50
TRACK_LENGTH = 560
TRACK_HEIGHT = 340
BORDER_THICKNESS = 4

CAR_START_X = 400
CAR_START_Y = 170

OUTER_COLOR = (0, 0, 0)
TRACK_COLOR = (100, 100, 100)
BORDER_COLOR = (255, 0, 0)
CAR_COLOR = (255, 255, 255)


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Chronos Racing - V1")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)


circuit = Circuit(
    center_x=TRACK_CENTER_X,
    center_y=TRACK_CENTER_Y,
    length=TRACK_LENGTH,
    height=TRACK_HEIGHT,
    width=TRACK_WIDTH,
    border_thickness=BORDER_THICKNESS,
)

car = Car(CAR_START_X, CAR_START_Y)
ai = SimpleMLP()

running = True
crashed = False


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not crashed:
        state = circuit.get_state(car)
        action = ai.forward(state)
        car.update(action)

        if not circuit.is_on_track(car.pos):
            crashed = True
            print("Collision : voiture hors piste / dans le mur.")

    circuit.draw(screen, OUTER_COLOR, TRACK_COLOR, BORDER_COLOR)

    pygame.draw.circle(screen, CAR_COLOR, car.pos.astype(int), 6)

    if crashed:
        text = font.render("CRASH - FIN", True, BORDER_COLOR)
        screen.blit(text, (270, 40))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()