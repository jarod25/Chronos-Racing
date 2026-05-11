import warnings
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
)

import pygame
import sys
import numpy as np

from car_grid import Car
from circuit_grid import Circuit
from ai_grid import SimpleMLP

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

POP_SIZE = 50
VISION_SIZE = 200
GRID_SIZE = 20
INPUT_SIZE = GRID_SIZE * GRID_SIZE

FPS = 60

OUTER_COLOR = (0, 0, 0)
TRACK_COLOR = (100, 100, 100)
BORDER_COLOR = (255, 0, 0)
CAR_COLOR = (255, 255, 255)


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Chronos Racing - IA Genétique")
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

cars = [Car(CAR_START_X, CAR_START_Y) for _ in range(POP_SIZE)]
ais = [SimpleMLP(input_size=INPUT_SIZE) for _ in range(POP_SIZE)]
alive = [True] * POP_SIZE

best_ai = ais[0]
best_score = 0
generation = 1


def reset_population():
    return (
        [Car(CAR_START_X, CAR_START_Y) for _ in range(POP_SIZE)],
        [ai.copy() for ai in ais],
        [True] * POP_SIZE
    )


# MAIN LOOP

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    # DRAW TRACK

    circuit.draw(
        screen,
        OUTER_COLOR,
        TRACK_COLOR,
        BORDER_COLOR
    )

    all_dead = True

    # UPDATE CARS

    for i in range(POP_SIZE):

        if not alive[i]:
            continue

        all_dead = False

        # VISION

        vision = circuit.get_vision(
            screen,
            cars[i],
            size=VISION_SIZE,
            grid_size=GRID_SIZE
        )

        # IA ACTION

        action = ais[i].forward(vision)

        cars[i].update(action)

        # CHECKPOINT SCORE

        new_checkpoint = circuit.get_checkpoint(
            cars[i]
        )

        delta = (
            new_checkpoint
            - cars[i].checkpoint
        )

        # boucle circulaire
        if delta < -100:
            delta += circuit.num_checkpoints

        elif delta > 100:
            delta -= circuit.num_checkpoints

        # uniquement sens horaire
        if delta > 0:
            cars[i].score += delta

        cars[i].checkpoint = new_checkpoint

        # COLLISION

        if not circuit.is_on_track(cars[i].pos):
            alive[i] = False

    # DRAW CARS

    for i in range(POP_SIZE):

        if alive[i]:
            color = (255, 255, 255)
        else:
            color = (70, 70, 70)

        pygame.draw.circle(
            screen,
            color,
            cars[i].pos.astype(int),
            4
        )

    # NEXT GENERATION

    if all_dead:

        print(f"\n=== GENERATION {generation} ===")

        # SCORES

        scores = [
            cars[i].score
            for i in range(POP_SIZE)
        ]

        best_idx = np.argmax(scores)

        best_gen_score = scores[best_idx]

        print(
            f"Best score this gen: "
            f"{best_gen_score}"
        )

        print(
            f"Best global score: "
            f"{best_score}"
        )

        print("--------------------")

        # SAVE BEST

        if best_gen_score > best_score:

            best_score = best_gen_score

            best_ai = ais[best_idx].copy()

            print("NOUVEAU MEILLEUR !")

        # SELECTION

        sorted_idx = np.argsort(scores)[::-1]

        top_k = 10

        parents = sorted_idx[:top_k]

        # NEW GENERATION

        new_ais = []

        for _ in range(POP_SIZE):

            parent = ais[
                np.random.choice(parents)
            ]

            child = parent.copy()

            child.mutate(rate=0.05)

            new_ais.append(child)

        ais = new_ais

        # RESET CARS

        cars = [
            Car(CAR_START_X, CAR_START_Y)
            for _ in range(POP_SIZE)
        ]

        alive = [True] * POP_SIZE

        generation += 1

    # UI

    alive_count = sum(alive)

    text = font.render(
        f"Gen: {generation} | "
        f"Alive: {alive_count} | "
        f"Best: {best_score}",
        True,
        (255, 255, 255)
    )

    screen.blit(text, (10, 10))

    # DISPLAY

    pygame.display.flip()

    clock.tick(FPS)

pygame.quit()
sys.exit()