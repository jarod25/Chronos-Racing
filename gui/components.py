import pygame

from gui.colors import BLACK, DARK_BUTTON, LIGHT_BUTTON, WHITE


def draw_text(screen, font, text, x, y, color=BLACK):
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))


def draw_centered_text(screen, font, text, y, color=BLACK):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(screen.get_width() // 2, y))
    screen.blit(surface, rect)


def draw_button(screen, font, rect, text, mouse_pos):
    if rect.collidepoint(mouse_pos):
        color = LIGHT_BUTTON
        text_color = BLACK
    else:
        color = DARK_BUTTON
        text_color = WHITE

    pygame.draw.rect(screen, color, rect, border_radius=10)

    surface = font.render(text, True, text_color)
    text_rect = surface.get_rect(center=rect.center)
    screen.blit(surface, text_rect)


def shorten_text(text, font, max_width):
    if font.size(text)[0] <= max_width:
        return text

    result = text

    while len(result) > 3 and font.size(result + "...")[0] > max_width:
        result = result[:-1]

    return result + "..."
