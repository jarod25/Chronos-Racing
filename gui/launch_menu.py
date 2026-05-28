import sys
from dataclasses import dataclass

import pygame

from gui.colors import LIGHT_BACKGROUND
from gui.components import draw_button, draw_centered_text
from gui.file_browser import choose_saved_ai


@dataclass
class LaunchSelection:
    mode: str
    ai_name: str
    load_path: str | None


PLAY_AI_OPTIONS = [
    ("simple", "Simple AI"),
    ("physic", "Physics AI"),
    ("genetic", "Genetic AI"),
]

TRAIN_AI_OPTIONS = [
    ("physic", "Physics AI"),
    ("genetic", "Genetic AI"),
]

MODE_OPTIONS = [
    ("play", "Play"),
    ("train", "Train"),
]


def _draw_title(screen, title_font, subtitle_font, title, subtitle):
    screen.fill(LIGHT_BACKGROUND)
    draw_centered_text(screen, title_font, "Chronos Racing", 90)
    draw_centered_text(screen, subtitle_font, title, 145)
    if subtitle:
        draw_centered_text(screen, subtitle_font, subtitle, 175)


def _button_list(screen, clock, title, entries, subtitle=""):
    title_font = pygame.font.SysFont(None, 56)
    button_font = pygame.font.SysFont(None, 32)
    subtitle_font = pygame.font.SysFont(None, 26)

    button_width = 420
    button_height = 60
    spacing = 16

    total_h = len(entries) * button_height + max(0, len(entries) - 1) * spacing
    top = (screen.get_height() - total_h) // 2
    x = (screen.get_width() - button_width) // 2

    while True:
        mouse_pos = pygame.mouse.get_pos()
        _draw_title(screen, title_font, subtitle_font, title, subtitle)

        rects = []
        for i, (value, label) in enumerate(entries):
            rect = pygame.Rect(x, top + i * (button_height + spacing), button_width, button_height)
            rects.append((rect, value))
            draw_button(screen, button_font, rect, label, mouse_pos)

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, value in rects:
                    if rect.collidepoint(event.pos):
                        return value


def _ask_load_or_fresh(screen, clock):
    return _button_list(
        screen,
        clock,
        title="AI Setup",
        subtitle="Create a fresh AI or load one from saves",
        entries=[
            ("fresh", "Fresh AI"),
            ("load", "Load existing AI"),
        ],
    )


def choose_launch_selection(screen, clock):
    mode = _button_list(
        screen,
        clock,
        title="Choose mode",
        entries=MODE_OPTIONS,
    )

    ai_entries = PLAY_AI_OPTIONS if mode == "play" else TRAIN_AI_OPTIONS

    ai_name = _button_list(
        screen,
        clock,
        title="Choose AI",
        subtitle=f"Mode: {mode}",
        entries=ai_entries,
    )

    load_choice = _ask_load_or_fresh(screen, clock)
    load_path = None

    if load_choice == "load":
        selected = choose_saved_ai(screen, clock)
        if selected is None:
            load_path = None
        else:
            load_path = selected

    return LaunchSelection(mode=mode, ai_name=ai_name, load_path=load_path)
