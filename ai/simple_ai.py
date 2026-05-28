class SimpleAI:
    def __init__(self, turn_strength=1.0):
        self.turn_strength = turn_strength

    @staticmethod
    def _clamp(value, min_value, max_value):
        return max(min_value, min(max_value, value))

    def forward(self, vision, speed_kmh=0.0, max_speed_kmh=350.0):
        middle = len(vision) // 2

        left_rays = vision[:middle]
        right_rays = vision[middle + 1:]
        left = sum(left_rays) / max(1, len(left_rays))
        right = sum(right_rays) / max(1, len(right_rays))
        front = vision[middle]

        steering = (right - left) * self.turn_strength
        if front < 0.25:
            steering *= 1.8
        steering = self._clamp(steering, -1.0, 1.0)

        if front > 0.75:
            target_speed = 260.0
        elif front > 0.45:
            target_speed = 180.0
        elif front > 0.25:
            target_speed = 100.0
        else:
            target_speed = 40.0

        target_speed *= max(0.35, 1.0 - abs(steering) * 0.6)
        target_speed = min(target_speed, max_speed_kmh)

        speed_error = target_speed - speed_kmh
        if speed_error > 20.0:
            throttle = 1.0
            brake = 0.0
        elif speed_error > 5.0:
            throttle = 0.5
            brake = 0.0
        elif speed_error < -30.0:
            throttle = 0.0
            brake = 0.7
        elif speed_error < -10.0:
            throttle = 0.0
            brake = 0.3
        else:
            throttle = 0.1
            brake = 0.0

        if front < 0.15:
            throttle = 0.0
            brake = 1.0

        if speed_kmh < 3.0 and front > 0.2:
            throttle = max(throttle, 0.4)
            brake = 0.0

        return {
            "throttle": float(self._clamp(throttle, 0.0, 1.0)),
            "brake": float(self._clamp(brake, 0.0, 1.0)),
            "steering": float(self._clamp(steering, -1.0, 1.0)),
        }
