class SimpleAI:
    def __init__(self, turn_strength=1.0):
        self.turn_strength = turn_strength

    def forward(self, vision):
        middle = len(vision) // 2

        left = sum(vision[:middle])
        right = sum(vision[middle + 1:])
        front = vision[middle]

        steer = (right - left) * self.turn_strength

        if front < 0.25:
            steer *= 1.8

        steer = max(-1, min(1, steer))

        return steer, 0
