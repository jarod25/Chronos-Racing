import warnings, pygame, sys, numpy as np, argparse
from car_grid import Car
from circuit_grid import Circuit
from ai_grid import SimpleMLP
from save_manager import save_ai, load_ai
from sensors_grid import RaySensor

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)

# CONFIG

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
TRACK_CENTER_X, TRACK_CENTER_Y = 400, 300
TRACK_WIDTH, TRACK_LENGTH, TRACK_HEIGHT = 50, 560, 340
BORDER_THICKNESS = 4
CAR_START_X, CAR_START_Y = 400, 170

POP_SIZE = 50
INPUT_SIZE = 24
FPS = 60

OUTER_COLOR = (0, 0, 0)
TRACK_COLOR = (100, 100, 100)
BORDER_COLOR = (255, 0, 0)

# ARGUMENTS

parser = argparse.ArgumentParser()
parser.add_argument("--load", type=str, default=None, help="Load IA save")
args = parser.parse_args()

# PYGAME

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Chronos Racing - IA Genétique")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)

# CIRCUIT

circuit = Circuit(
    center_x=TRACK_CENTER_X,
    center_y=TRACK_CENTER_Y,
    length=TRACK_LENGTH,
    height=TRACK_HEIGHT,
    width=TRACK_WIDTH,
    border_thickness=BORDER_THICKNESS
)

# Initialisation loading ia

if args.load:
    print(f"\nChargement IA : {args.load}")
    base_ai = load_ai(SimpleMLP, args.load)
    ais = [base_ai.copy() for _ in range(POP_SIZE)]

    for i in range(1, POP_SIZE):
        ais[i].mutate(rate=0.02)

    print("Population générée depuis sauvegarde.\n")

else:
    ais = [SimpleMLP(input_size=INPUT_SIZE) for _ in range(POP_SIZE)]

cars = [Car(CAR_START_X, CAR_START_Y) for _ in range(POP_SIZE)]
alive = [True] * POP_SIZE

best_ai = ais[0]
best_time = 100.0 # high time for starter
generation = 1

finished = False
winner_time = None
start_frame = 0

# MAIN LOOP

running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    circuit.draw(screen, OUTER_COLOR, TRACK_COLOR, BORDER_COLOR)
    sensor = RaySensor()

    all_dead = True

    for i in range(POP_SIZE):

        if not alive[i]:
            continue

        all_dead = False

        # RAYCAST INPUT
        vision = sensor.get_distances(circuit, cars[i])

        vision.append(cars[i].speed / 5.0)

        vision.append(np.sin(cars[i].angle))
        vision.append(np.cos(cars[i].angle))

        vision = np.array(vision)

        action = ais[i].forward(vision)

        action += np.random.randn(2) * 0.02
        action = np.clip(action, -1, 1)

        cars[i].update(action)

        # gestion checkpoints
        old_checkpoint = cars[i].checkpoint
        new_checkpoint = circuit.get_checkpoint(cars[i])
        delta = new_checkpoint - old_checkpoint

        # gestion loop 0 -> 199
        if delta < -100:
            delta += circuit.num_checkpoints

        elif delta > 100:
            delta -= circuit.num_checkpoints

        # update checkpoint
        cars[i].checkpoint = new_checkpoint

        # SCORE
        # progression
        if delta > 0:
            cars[i].score += delta * 10
            cars[i].total_checkpoints += delta

        # stagnation
        else:
            cars[i].score -= 0.02

        # time cost
        cars[i].score -= 0.001
        # bonus speed
        cars[i].score += cars[i].speed * 0.01

        # lap completed
        if cars[i].total_checkpoints >= circuit.num_checkpoints and not finished:
            finished = True
            winner_time = pygame.time.get_ticks() - start_frame
            winner_time_seconds = winner_time / 1000
            cars[i].score += 10000
            print(f"TOUR COMPLET ! Temps: {winner_time} ms")

        # if collision
        if not circuit.is_on_track(cars[i].pos):
            cars[i].score -= 100
            alive[i] = False

    # DRAW CARS

    for i in range(POP_SIZE):
        pygame.draw.circle(screen, (255, 255, 255) if alive[i] else (70, 70, 70),cars[i].pos.astype(int), 4)

    # NEXT GENERATION

    if all_dead or finished:

        print(f"\n=== GENERATION {generation} ===")
        
        scores = [car.score for car in cars]
        best_idx = np.argmax(scores)
        best_gen_score = scores[best_idx]

        print(f"Best score this gen: {best_gen_score}")
        print(f"Best global score: {best_time}")
        print("--------------------")

        if winner_time is not None:

            winner_time_seconds = winner_time / 1000

            if winner_time_seconds < best_time:
                best_time = winner_time_seconds
                best_ai = ais[best_idx].copy()
                print("NOUVEAU MEILLEUR TEMPS !")
                save_ai(best_ai, f"time_{best_time:.2f}.npz")

        sorted_idx = np.argsort(scores)[::-1]
        parents = sorted_idx[:20]

        new_ais = [ais[idx].copy() for idx in parents[:1]]

        while len(new_ais) < POP_SIZE:

            parent = ais[np.random.choice(parents)]
            child = parent.copy()

            r = np.random.rand()
            rate = 0.02 if r < 0.7 else 0.05 if r < 0.95 else 0.15

            child.mutate(rate=rate)

            new_ais.append(child)

        ais = new_ais

        cars = [Car(CAR_START_X, CAR_START_Y) for _ in range(POP_SIZE)]
        alive = [True] * POP_SIZE

        finished = False
        winner_time = None

        generation += 1
        start_frame = pygame.time.get_ticks()

    # UI
    best_alive = next((i for i in range(POP_SIZE) if alive[i]), None)

    if best_alive is not None:
        sensor.draw(screen, circuit, cars[best_alive])

    text = font.render(f"Gen: {generation} | Alive: {sum(alive)} | Best: {best_time}",True,(255, 255, 255))

    screen.blit(text, (10, 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()