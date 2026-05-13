import math
import sys

import pygame

from gui.colors import GRAY, GREEN, RED, YELLOW
from gui.components import draw_centered_text


def get_angle_from_points(start_pos, target_pos):
    dx = target_pos[0] - start_pos[0]
    dy = target_pos[1] - start_pos[1]

    return math.atan2(dy, dx)


def is_direction_far_enough(start_pos, target_pos):
    dx = target_pos[0] - start_pos[0]
    dy = target_pos[1] - start_pos[1]

    return dx * dx + dy * dy >= 100


def draw_direction_preview(screen, circuit, start_pos, mouse_pos):
    start_screen_pos = circuit.track_to_screen(start_pos)
    target_track_pos = circuit.screen_to_track(mouse_pos)
    target_screen_pos = circuit.track_to_screen(target_track_pos)

    pygame.draw.circle(
        screen,
        YELLOW,
        (int(start_screen_pos[0]), int(start_screen_pos[1])),
        8,
    )

    pygame.draw.line(
        screen,
        YELLOW,
        (int(start_screen_pos[0]), int(start_screen_pos[1])),
        (int(target_screen_pos[0]), int(target_screen_pos[1])),
        3,
    )


def choose_start_position(screen, clock, circuit, default_pos=None):
    title_font = pygame.font.SysFont(None, 34)
    text_font = pygame.font.SysFont(None, 24)

    start_pos = None
    error_message = ""

    while True:
        mouse_pos = pygame.mouse.get_pos()

        circuit.draw(screen)

        if start_pos is None:
            draw_centered_text(screen, title_font, "Click the start point", 35)
            draw_centered_text(screen, text_font, "Then click the driving direction", 65, GRAY)
        else:
            draw_centered_text(screen, title_font, "Click the driving direction", 35)
            draw_direction_preview(screen, circuit, start_pos, mouse_pos)

        if error_message != "":
            draw_centered_text(screen, text_font, error_message, screen.get_height() - 25, RED)

        if start_pos is None:
            if circuit.is_screen_pos_on_track(mouse_pos):
                pygame.draw.circle(screen, GREEN, mouse_pos, 6)
            else:
                pygame.draw.circle(screen, RED, mouse_pos, 6)

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
                clicked_track_pos = circuit.screen_to_track(event.pos)

                if start_pos is None:
                    if circuit.is_on_track(clicked_track_pos):
                        start_pos = clicked_track_pos
                        error_message = ""
                    else:
                        error_message = "Not on track."
                else:
                    if is_direction_far_enough(start_pos, clicked_track_pos):
                        start_angle = get_angle_from_points(start_pos, clicked_track_pos)
                        return start_pos, start_angle

                    error_message = "Click a bit farther."


def choose_import_start_position(screen, clock, circuit):
    title_font = pygame.font.SysFont(None, 34)
    text_font = pygame.font.SysFont(None, 24)

    start_pos = None
    error_message = ""

    while True:
        mouse_pos = pygame.mouse.get_pos()

        circuit.draw(screen)

        if circuit.track_mask is not None:
            circuit.draw_mask_overlay(screen)

        if start_pos is None:
            draw_centered_text(screen, title_font, "Click the start point", 35)
            draw_centered_text(screen, text_font, "Track detection is automatic", 65, GRAY)
        else:
            draw_centered_text(screen, title_font, "Click the driving direction", 35)
            draw_direction_preview(screen, circuit, start_pos, mouse_pos)

        if error_message != "":
            draw_centered_text(screen, text_font, error_message, screen.get_height() - 25, RED)

        if start_pos is None:
            pygame.draw.circle(screen, YELLOW, mouse_pos, 6)

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
                clicked_track_pos = circuit.screen_to_track(event.pos)

                if start_pos is None:
                    pixel_count = circuit.generate_track_mask_from_point(clicked_track_pos)

                    if pixel_count < 100:
                        error_message = "Track not detected."
                    else:
                        start_pos = clicked_track_pos
                        error_message = ""
                else:
                    if is_direction_far_enough(start_pos, clicked_track_pos):
                        start_angle = get_angle_from_points(start_pos, clicked_track_pos)
                        return start_pos, start_angle

                    error_message = "Click a bit farther."
