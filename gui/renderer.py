import pygame

from gui.colors import BLACK, RED, WHITE
from gui.hud import draw_hud

def draw_game(
        screen,
        circuit,
        car,
        crashed,
        font,
        button_font,
        raycasts_button_rect,
        checkpoints_button_rect,
        show_rays,
        show_checkpoints,
        sensor=None,
        draw_rays=False,
        ai_name=None,
        speed_kmh=None,
        current_lap_time=None,
        last_lap_time=None,
        best_lap_time=None,
        lap_delta=None,
):
    circuit.draw(screen, draw_checkpoints=show_checkpoints)

    if sensor is not None and draw_rays:
        sensor.draw(screen, circuit, car)

    draw_car(screen, circuit, car)
    draw_hud(
        screen=screen,
        font=button_font,
        button_font=button_font,
        ai_name=ai_name,
        speed_kmh=speed_kmh,
        current_lap_time=current_lap_time,
        last_lap_time=last_lap_time,
        best_lap_time=best_lap_time,
        lap_delta=lap_delta,
        show_rays=show_rays,
        show_checkpoints=show_checkpoints,
        raycasts_button_rect=raycasts_button_rect,
        checkpoints_button_rect=checkpoints_button_rect,
    )

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
    rect = text.get_rect(center=(screen.get_width() // 2, 45))
    screen.blit(text, rect)
