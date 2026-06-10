import sys
from pathlib import Path

import pygame

from gui.colors import (
    BLACK,
    DARK_BUTTON,
    GRAY,
    LIGHT_BACKGROUND,
    LIGHT_BUTTON,
    RED,
    WHITE,
)
from gui.components import draw_centered_text, draw_text, shorten_text

IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".svg"]
AI_EXTENSIONS = [".npz", ".json"]


def _get_visible_entries(current_dir, allowed_extensions):
    folders = []
    files = []

    try:
        for item in current_dir.iterdir():
            if item.is_dir():
                folders.append(item)
            elif item.is_file() and item.suffix.lower() in allowed_extensions:
                files.append(item)
    except PermissionError:
        return [], [], "Permission denied."
    except FileNotFoundError:
        return [], [], "Folder not found."

    folders.sort(key=lambda path: path.name.lower())
    files.sort(key=lambda path: path.name.lower())

    return folders, files, ""


def _choose_file_from_directory(
        screen,
        clock,
        root_dir,
        allowed_extensions,
        title,
        empty_message,
):
    title_font = pygame.font.SysFont(None, 40)
    text_font = pygame.font.SysFont(None, 24)

    root_dir.mkdir(parents=True, exist_ok=True)

    current_dir = root_dir
    scroll = 0
    row_height = 36
    error_message = ""

    while True:
        mouse_pos = pygame.mouse.get_pos()

        folders, files, read_error = _get_visible_entries(current_dir, allowed_extensions)

        if read_error:
            error_message = read_error

        entries = []

        if current_dir.parent != current_dir:
            entries.append(("folder", current_dir.parent, ".."))

        for folder in folders:
            entries.append(("folder", folder, folder.name))

        for file_path in files:
            entries.append(("file", file_path, file_path.name))

        screen.fill(LIGHT_BACKGROUND)

        draw_centered_text(screen, title_font, title, 40)

        path_text = shorten_text(str(current_dir), text_font, screen.get_width() - 60)
        draw_centered_text(screen, text_font, path_text, 75, GRAY)

        list_top = 115
        list_bottom = screen.get_height() - 45
        visible_rows = (list_bottom - list_top) // row_height

        max_scroll = max(0, len(entries) - visible_rows)
        scroll = max(0, min(scroll, max_scroll))

        visible_entries = entries[scroll:scroll + visible_rows]
        row_rects = []

        for index, entry in enumerate(visible_entries):
            entry_type, path, label = entry

            y = list_top + index * row_height
            rect = pygame.Rect(120, y, screen.get_width() - 240, row_height - 5)
            row_rects.append((rect, entry_type, path))

            if rect.collidepoint(mouse_pos):
                color = LIGHT_BUTTON
                text_color = BLACK
            else:
                color = DARK_BUTTON
                text_color = WHITE

            pygame.draw.rect(screen, color, rect, border_radius=8)

            prefix = "[D] " if entry_type == "folder" else ""
            short_label = shorten_text(prefix + label, text_font, rect.width - 20)
            draw_text(screen, text_font, short_label, rect.x + 10, rect.y + 8, text_color)

        if len(entries) == 0:
            draw_centered_text(screen, text_font, empty_message, 260, GRAY)

        if error_message:
            draw_centered_text(screen, text_font, error_message, screen.get_height() - 25, RED)

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEWHEEL:
                scroll -= event.y

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_BACKSPACE and current_dir.parent != current_dir:
                    current_dir = current_dir.parent
                    scroll = 0
                    error_message = ""

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    scroll -= 1

                if event.button == 5:
                    scroll += 1

                if event.button == 1:
                    for rect, entry_type, path in row_rects:
                        if rect.collidepoint(event.pos):
                            if entry_type == "folder":
                                current_dir = path
                                scroll = 0
                                error_message = ""
                            elif entry_type == "file":
                                return str(path)


def choose_import_image(screen, clock):
    tracks_dir = Path.cwd() / "assets" / "tracks"
    return _choose_file_from_directory(
        screen=screen,
        clock=clock,
        root_dir=tracks_dir,
        allowed_extensions=IMAGE_EXTENSIONS,
        title="Choose a track",
        empty_message="No image here.",
    )


def choose_saved_ai(screen, clock):
    saves_dir = Path.cwd() / "saves"
    return _choose_file_from_directory(
        screen=screen,
        clock=clock,
        root_dir=saves_dir,
        allowed_extensions=AI_EXTENSIONS,
        title="Choose AI save",
        empty_message="No AI save here.",
    )
