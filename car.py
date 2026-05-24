import numpy as np


class Car:
    def __init__(
            self,
            x,
            y,
            angle=0.0,
            max_steering_angle=0.2,
            max_speed_kmh=350.0,
            acceleration_power_kmh_s=45.0,
            brake_power_kmh_s=120.0
    ):
        self.pos = np.array([x, y], dtype=float)
        self.angle = float(angle)

        self.speed_kmh = 0.0
        self.max_speed_kmh = float(max_speed_kmh)
        self.acceleration_power_kmh_s = float(acceleration_power_kmh_s)
        self.brake_power_kmh_s = float(brake_power_kmh_s)
        self.max_steering_angle = float(max_steering_angle)

        self.checkpoint = 0
        self.total_checkpoints = 0
        self.last_checkpoint = 0
        self.checkpoint_passed = False
        self.lap_completed = False

        self.prev_pos = np.array([x, y], dtype=float)

        self.score = 0

    def _extract_controls(self, action):
        throttle = 0.0
        brake = 0.0
        steering = 0.0

        if isinstance(action, dict):
            throttle = float(action.get("throttle", 0.0))
            brake = float(action.get("brake", 0.0))
            steering = float(action.get("steering", 0.0))
        else:
            acceleration, steering = action
            acceleration = float(acceleration)
            steering = float(steering)

            if acceleration >= 0:
                throttle = acceleration
            else:
                brake = -acceleration

        throttle = np.clip(throttle, 0.0, 1.0)
        brake = np.clip(brake, 0.0, 1.0)
        steering = np.clip(steering, -1.0, 1.0)

        return throttle, brake, steering

    def _to_pixels_per_frame(self, fps=60.0):
        return self.speed_kmh / (fps * 3.6)

    def update(self, action):
        self.prev_pos = self.pos.copy()
        throttle, brake, steering = self._extract_controls(action)

        steer_angle = np.clip(
            steering * self.max_steering_angle,
            -self.max_steering_angle,
            self.max_steering_angle,
        )
        self.angle += steer_angle

        dt = 1.0 / 60.0
        self.speed_kmh += throttle * self.acceleration_power_kmh_s * dt
        self.speed_kmh -= brake * self.brake_power_kmh_s * dt

        self.speed_kmh = max(0.0, self.speed_kmh)
        self.speed_kmh = min(self.speed_kmh, self.max_speed_kmh)

        speed_px_frame = self._to_pixels_per_frame()
        dx = np.cos(self.angle) * speed_px_frame
        dy = np.sin(self.angle) * speed_px_frame

        self.pos += np.array([dx, dy])
