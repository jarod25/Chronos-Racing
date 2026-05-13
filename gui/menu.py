import sys

import pygame

from gui.colors import LIGHT_BACKGROUND
from gui.components import draw_button, draw_centered_text


def choose_circuit_mode(screen, clock):
    title_font = pygame.font.SysFont(None, 56)
    button_font = pygame.font.SysFont(None, 32)

    default_button = pygame.Rect(300, 250, 400, 60)
    import_button = pygame.Rect(300, 330, 400, 60)

    while True:
        mouse_pos = pygame.mouse.get_pos()

        screen.fill(LIGHT_BACKGROUND)

        draw_centered_text(screen, title_font, "Chronos Racing", 130)
        draw_button(screen, button_font, default_button, "Default track", mouse_pos)
        draw_button(screen, button_font, import_button, "Import track", mouse_pos)

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
                if default_button.collidepoint(event.pos):
                    return "default"

                if import_button.collidepoint(event.pos):
                    return "import"
