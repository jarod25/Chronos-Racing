import sys
import warnings

from graph import run_graph_mode

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
)

import pygame

from config import WINDOW_HEIGHT, WINDOW_WIDTH
from game import ChronosGame
from gui.launch_menu import choose_launch_selection
from training.genetic_training_game import GeneticTrainingGame
from training.physics_training_game import PhysicsTrainingGame


def main():
    if "--graph" in sys.argv:
        run_graph_mode()
        return

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Chronos Racing - Launcher")
    clock = pygame.time.Clock()

    launch_selection = choose_launch_selection(screen, clock)

    if launch_selection.mode == "train":
        if launch_selection.ai_name in "physics":
            game = PhysicsTrainingGame(
                screen=screen,
                ai_name=launch_selection.ai_name,
                load_path=launch_selection.load_path,
            )
        else:
            game = GeneticTrainingGame(
                screen=screen,
                ai_name=launch_selection.ai_name,
                load_path=launch_selection.load_path,
            )
    else:
        game = ChronosGame(
            screen=screen,
            ai_name=launch_selection.ai_name,
            load_path=launch_selection.load_path,
        )

    game.run()


if __name__ == "__main__":
    main()
