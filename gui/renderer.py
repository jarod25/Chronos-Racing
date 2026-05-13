import pygame

from config import WINDOW_WIDTH
from gui.colors import BLACK, RED, WHITE


def draw_game(screen, circuit, car, crashed, font, sensor=None, draw_rays=False):
    circuit.draw(screen)

    if sensor is not None and draw_rays:
        sensor.draw(screen, circuit, car)

    draw_car(screen, circuit, car)

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


def draw_crash_text(screen, font):
    text = font.render("CRASH", True, RED)
    rect = text.get_rect(center=(WINDOW_WIDTH // 2, 45))
    screen.blit(text, rect)