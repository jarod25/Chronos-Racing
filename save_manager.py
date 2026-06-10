import json
import math
import os
import re

import numpy as np

SAVE_DIR = "saves"


def _coerce_lap_time(value):
    try:
        lap_time = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(lap_time) or lap_time <= 0:
        return None
    return lap_time


def _path_for_save(filename):
    return filename if os.path.isabs(filename) else os.path.join(SAVE_DIR, filename)


def load_best_time_from_save(load_path):
    if not load_path:
        return None

    path = _path_for_save(load_path)
    basename = os.path.basename(str(load_path))

    if str(path).lower().endswith(".json") and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            data = None

        if isinstance(data, dict):
            lap_time = _coerce_lap_time(data.get("best_lap_time"))
            if lap_time is not None:
                return lap_time

    for match in re.finditer(r"(?<!\d)(\d+[.,]\d+)(?!\d)", basename):
        lap_time = _coerce_lap_time(match.group(1).replace(",", "."))
        if lap_time is not None:
            return lap_time

    return None


def _sanitize_name(value, fallback="unknown"):
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9._-]+", "_", text)
    text = text.strip("_")
    return text or fallback


def normalize_circuit_name(circuit_name):
    normalized = _sanitize_name(circuit_name, fallback="ellipse")

    if normalized in {"", "unknown", "unknown_circuit", "none"}:
        return "imported"

    return normalized


def build_save_filename(ai_name, circuit_name, time_s, extension="npz"):
    ai_part = _sanitize_name(ai_name, fallback="ai")
    circuit_part = normalize_circuit_name(circuit_name)
    ext = extension.lower().lstrip(".")

    return f"{ai_part}_{circuit_part}_{time_s:.2f}.{ext}"


def save_ai(ai, filename):
    os.makedirs(SAVE_DIR, exist_ok=True)
    safe_filename = os.path.basename(filename)
    path = os.path.join(SAVE_DIR, safe_filename)

    np.savez(path, W1=ai.W1, b1=ai.b1, W2=ai.W2, b2=ai.b2)

    print(f"[SAVE] AI saved : {path}")


def load_ai(ai_class, filename):
    path = _path_for_save(filename)

    data = np.load(path)

    ai = ai_class()

    ai.W1 = data["W1"]
    ai.b1 = data["b1"]

    ai.W2 = data["W2"]
    ai.b2 = data["b2"]

    print(f"[LOAD] AI Loaded : {path}")

    return ai


def delete_ai_save(filename):
    safe_filename = os.path.basename(filename)
    path = os.path.join(SAVE_DIR, safe_filename)

    if not os.path.exists(path):
        print(f"[DELETE] File not found : {path}")
        return False

    os.remove(path)

    print(f"[DELETE] AI save deleted : {path}")

    return True


def replace_best_save(
        ai,
        ai_name=None,
        circuit_name=None,
        time_s=None,
        extension="npz",
        old_filename=None,
        new_filename=None,
):
    if new_filename is None:
        if ai_name is None or circuit_name is None or time_s is None:
            raise ValueError(
                "replace_best_save needs either new_filename or (ai_name, circuit_name, time_s)."
            )
        new_filename = build_save_filename(
            ai_name=ai_name,
            circuit_name=circuit_name,
            time_s=time_s,
            extension=extension,
        )

    old_safe_filename = os.path.basename(old_filename) if old_filename is not None else None
    if old_safe_filename is not None and old_safe_filename != new_filename:
        delete_ai_save(old_safe_filename)

    save_ai(ai, new_filename)

    return new_filename
