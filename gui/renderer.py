import pygame

from gui.colors import BLACK, RED, WHITE
from gui.components import draw_button


def draw_game(
        screen,
        circuit,
        car,
        crashed,
        font,
        button_font,
        checkpoints_button_rect,
        show_checkpoints,
        sensor=None,
        draw_rays=False,
        hud_text=None,
):
    circuit.draw(screen, draw_checkpoints=show_checkpoints)

    if sensor is not None and draw_rays:
        sensor.draw(screen, circuit, car)

    draw_car(screen, circuit, car)
    draw_checkpoints_button(
        screen=screen,
        font=button_font,
        button_rect=checkpoints_button_rect,
        show_checkpoints=show_checkpoints,
    )

    if hud_text:
        draw_hud_text(screen, hud_text)

    if crashed:
        draw_crash_text(screen, font)


def draw_car(screen, circuit, car):
    car_screen_pos = circuit.track_to_screen(car.pos)

    pygame.draw.circle(
        screen,
        BLACK,
        (int(car_screen_pos[0]), int(car_screen_pos[1])),
        8,
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (int(car_screen_pos[0]), int(car_screen_pos[1])),
        6,
    )


def draw_hud_text(screen, text_value):
    font = pygame.font.SysFont(None, 28)
    margin = 12
    text = font.render(text_value, True, BLACK)
    rect = text.get_rect()
    rect.topright = (screen.get_width() - margin, margin)
    screen.blit(text, rect)


def draw_crash_text(screen, font):
    text = font.render("CRASH", True, RED)
    rect = text.get_rect(center=(screen.get_width() // 2, 45))
    screen.blit(text, rect)


def draw_checkpoints_button(screen, font, button_rect, show_checkpoints):
    mouse_pos = pygame.mouse.get_pos()
    label = "Show checkpoints: YES" if show_checkpoints else "Show checkpoints: NO"
    draw_button(screen, font, button_rect, label, mouse_pos)
