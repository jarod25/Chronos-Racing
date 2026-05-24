import argparse
import warnings

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
)

from game import ChronosGame
from training.genetic_training_game import GeneticTrainingGame


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["play", "train"],
        default="play",
        help="Mode to launch: normal gameplay or genetic training.",
    )

    parser.add_argument(
        "--ai",
        choices=["simple", "physics", "genetic"],
        default="simple",
        help="AI used in play mode.",
    )

    parser.add_argument(
        "--load",
        type=str,
        default=None,
        help="Saved AI file, e.g. time_8.42.npz. (No directory path.)",
    )

    args = parser.parse_args()

    if args.mode == "train":
        game = GeneticTrainingGame(load_path=args.load)
    else:
        game = ChronosGame(
            ai_name=args.ai,
            load_path=args.load,
        )

    game.run()


if __name__ == "__main__":
    main()
