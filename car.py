import numpy as np


class Car:
    def __init__(self, x, y, angle=0.0):
        self.pos = np.array([x, y], dtype=float)
        self.angle = float(angle)
        self.speed = 2.0

        self.checkpoint = 0
        self.total_checkpoints = 0
        self.last_checkpoint = 0
        self.checkpoint_passed = False
        self.lap_completed = False

        self.prev_pos = np.array([x, y], dtype=float)

        self.score = 0

    def update(self, action):
        self.prev_pos = self.pos.copy()
        steer, throttle = action

        self.angle += steer * 0.1

        self.speed = 2.0 + throttle

        dx = np.cos(self.angle) * self.speed
        dy = np.sin(self.angle) * self.speed

        self.pos += np.array([dx, dy])
