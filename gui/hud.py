import math

import pygame

from gui.colors import BLACK
from gui.components import draw_button

HUD_MARGIN_LEFT = 10
HUD_MARGIN_TOP = 8
HUD_MARGIN_RIGHT = 10
HUD_BUTTON_WIDTH = 150
HUD_BUTTON_HEIGHT = 30
HUD_BUTTON_GAP = 10
HUD_TEXT_TOP = 10
HUD_CURRENT_TOP = 34
HUD_LAST_TOP = 60


def format_lap_time(seconds):
    if seconds is None:
        return "--:--.---"
    try:
        value = float(seconds)
    except (TypeError, ValueError):
        return "--:--.---"
    if not math.isfinite(value) or value < 0:
        return "--:--.---"

    total_milliseconds = int(round(value * 1000))
    minutes, remainder = divmod(total_milliseconds, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def format_delta(lap_delta):
    if lap_delta is None:
        return "Delta: ---"
    try:
        delta = float(lap_delta)
    except (TypeError, ValueError):
        return "Delta: ---"
    if not math.isfinite(delta):
        return "Delta: ---"
    return f"Delta: {delta:+.3f}s"


def build_toggle_button_rects(left=HUD_MARGIN_LEFT, top=HUD_MARGIN_TOP):
    raycasts_rect = pygame.Rect(left, top, HUD_BUTTON_WIDTH, HUD_BUTTON_HEIGHT)
    checkpoints_rect = pygame.Rect(
        raycasts_rect.right + HUD_BUTTON_GAP,
        top,
        HUD_BUTTON_WIDTH + 35,
        HUD_BUTTON_HEIGHT,
    )
    return raycasts_rect, checkpoints_rect


def draw_toggle_button(screen, font, button_rect, label, enabled):
    state = "ON" if enabled else "OFF"
    draw_button(screen, font, button_rect, f"{label}: {state}", pygame.mouse.get_pos())


def draw_hud(
    screen,
    font,
    button_font,
    ai_name,
    speed_kmh,
    current_lap_time,
    last_lap_time,
    best_lap_time,
    show_rays,
    show_checkpoints,
    raycasts_button_rect,
    checkpoints_button_rect,
    generation=None,
    lap_delta=None,
):
    draw_toggle_button(screen, button_font, raycasts_button_rect, "Raycasts", show_rays)
    draw_toggle_button(screen, button_font, checkpoints_button_rect, "Checkpoints", show_checkpoints)

    ai_parts = [f"AI: {ai_name}"]
    if generation is not None:
        ai_parts.append(f"Gen: {generation}")
    ai_text = font.render(" | ".join(ai_parts), True, BLACK)
    ai_rect = ai_text.get_rect(midtop=(screen.get_width() // 2, HUD_TEXT_TOP))
    screen.blit(ai_text, ai_rect)

    speed_display = "---.-" if speed_kmh is None else f"{float(speed_kmh):5.1f}"
    speed_text = font.render(f"Speed: {speed_display} km/h", True, BLACK)
    speed_rect = speed_text.get_rect(topright=(screen.get_width() - HUD_MARGIN_RIGHT, HUD_MARGIN_TOP))
    screen.blit(speed_text, speed_rect)

    current_text = font.render(f"Current: {format_lap_time(current_lap_time)}", True, BLACK)
    current_rect = current_text.get_rect(topright=(screen.get_width() - HUD_MARGIN_RIGHT, HUD_CURRENT_TOP))
    screen.blit(current_text, current_rect)

    lap_text = font.render(
        f"Last: {format_lap_time(last_lap_time)} | "
        f"Best: {format_lap_time(best_lap_time)} | "
        f"{format_delta(lap_delta)}",
        True,
        BLACK,
    )
    lap_rect = lap_text.get_rect(topright=(screen.get_width() - HUD_MARGIN_RIGHT, HUD_LAST_TOP))
    screen.blit(lap_text, lap_rect)
