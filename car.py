import numpy as np


class Car:
    def __init__(self, x, y):
        self.pos = np.array([x, y], dtype=float)
        self.angle = 0.0
        self.speed = 2.0

    def update(self, action):
        steer, throttle = action

        self.angle += steer * 0.1

        self.speed = 2.0 + throttle

        dx = np.cos(self.angle) * self.speed
        dy = np.sin(self.angle) * self.speed

        self.pos += np.array([dx, dy])