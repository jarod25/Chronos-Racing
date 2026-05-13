import warnings

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
)

from game import ChronosGame

if __name__ == "__main__":
    game = ChronosGame()
    game.run()
