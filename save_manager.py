import os

import numpy as np

SAVE_DIR = "saves"


def save_ai(ai, filename):
    path = os.path.join(SAVE_DIR, filename)

    np.savez(path, W1=ai.W1, b1=ai.b1, W2=ai.W2, b2=ai.b2)

    print(f"[SAVE] AI saved : {path}")


def load_ai(ai_class, filename):
    path = os.path.join(SAVE_DIR, filename)

    data = np.load(path)

    ai = ai_class()

    ai.W1 = data["W1"]
    ai.b1 = data["b1"]

    ai.W2 = data["W2"]
    ai.b2 = data["b2"]

    print(f"[LOAD] AI Loaded : {path}")

    return ai
