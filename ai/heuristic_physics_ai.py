class HeuristicPhysicsAI:
    def __init__(self, steering_gain=1.7, edge_gain=0.45):
        self.steering_gain = steering_gain
        self.edge_gain = edge_gain

        self.previous_steering = 0.0
        self.previous_throttle = 0.0
        self.previous_brake = 0.0

        self.sector_memory = {}
        self.current_sector = None
        self.previous_sector = None
        self.sector_stats = None

    @staticmethod
    def _clamp(value, low, high):
        return max(low, min(high, value))

    @staticmethod
    def _sample_rays(vision):
        n = len(vision)
        if n == 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0

        def pick(idx):
            idx = max(0, min(n - 1, idx))
            return float(vision[idx])

        left = pick(0)
        front_left = pick(int((n - 1) * 0.25))
        front = pick((n - 1) // 2)
        front_right = pick(int((n - 1) * 0.75))
        right = pick(n - 1)

        return left, front_left, front, front_right, right

    def _classify_situation(self, front, turn_amount):
        if front < 0.10:
            return "emergency"
        if front < 0.18:
            return "critical"
        if front < 0.28:
            return "danger"
        if turn_amount > 0.85:
            return "hairpin"
        if turn_amount > 0.65:
            return "very_sharp_turn"
        if turn_amount > 0.45:
            return "sharp_turn"
        if turn_amount > 0.30:
            return "medium_turn"
        if turn_amount > 0.15:
            return "light_turn"
        if front > 0.85 and turn_amount < 0.15:
            return "full_straight"
        return "straight"

    @staticmethod
    def _target_speed_for(situation):
        table = {
            "full_straight": 350.0,
            "straight": 320.0,
            "light_turn": 270.0,
            "medium_turn": 220.0,
            "sharp_turn": 160.0,
            "very_sharp_turn": 115.0,
            "hairpin": 75.0,
            "danger": 55.0,
            "critical": 30.0,
            "emergency": 0.0,
        }
        return table.get(situation, 220.0)

    @staticmethod
    def _new_sector_memory():
        return {
            "speed_bonus": 0.0,
            "brake_offset": 0.0,
            "steering_bias": 0.0,
            "success_count": 0,
            "fail_count": 0,
        }

    @staticmethod
    def _new_sector_stats():
        return {
            "min_clearance": 1.0,
            "max_speed_kmh": 0.0,
            "turn_sum": 0.0,
            "frames": 0,
            "last_steering": 0.0,
            "had_emergency": False,
            "had_critical": False,
        }

    def _get_sector_id(self, sector_hint, speed_kmh):
        if sector_hint is None:
            bucket = int(speed_kmh // 25)
            return ("speed", bucket)
        return ("cp", int(sector_hint))

    def _ensure_sector_memory(self, sector_id):
        if sector_id not in self.sector_memory:
            self.sector_memory[sector_id] = self._new_sector_memory()
        return self.sector_memory[sector_id]

    def _update_sector_memory(self, sector_id, stats, crashed=False):
        memory = self._ensure_sector_memory(sector_id)

        min_clearance = stats["min_clearance"]
        avg_turn = stats["turn_sum"] / max(1, stats["frames"])
        turn_dir = 1.0 if stats["last_steering"] > 0 else -1.0

        if crashed:
            memory["speed_bonus"] -= 22.0
            memory["brake_offset"] += 0.12
            memory["steering_bias"] -= turn_dir * 0.05
            memory["fail_count"] += 1
        elif min_clearance < 0.18 or stats["had_emergency"]:
            memory["speed_bonus"] -= 12.0
            memory["brake_offset"] += 0.08
            memory["steering_bias"] -= turn_dir * 0.03
            memory["fail_count"] += 1
        elif min_clearance < 0.30 or stats["had_critical"]:
            memory["speed_bonus"] -= 5.0
            memory["brake_offset"] += 0.04
            memory["fail_count"] += 1
        elif min_clearance > 0.55 and avg_turn > 0.20:
            memory["speed_bonus"] += 4.0
            memory["brake_offset"] -= 0.02
            memory["steering_bias"] += turn_dir * 0.02
            memory["success_count"] += 1
        elif min_clearance > 0.30:
            memory["speed_bonus"] += 1.5
            memory["brake_offset"] -= 0.005
            memory["success_count"] += 1

        memory["speed_bonus"] = self._clamp(memory["speed_bonus"], -80.0, 60.0)
        memory["brake_offset"] = self._clamp(memory["brake_offset"], -0.25, 0.35)
        memory["steering_bias"] = self._clamp(memory["steering_bias"], -0.25, 0.25)

    def forward(self, vision, speed_kmh=0.0, max_speed_kmh=350.0, sector_hint=None, crashed=False):
        side_left, front_left, front_clearance, front_right, side_right = self._sample_rays(vision)

        sector_id = self._get_sector_id(sector_hint, speed_kmh)
        memory = self._ensure_sector_memory(sector_id)

        if self.current_sector is None:
            self.current_sector = sector_id
            self.sector_stats = self._new_sector_stats()

        if sector_id != self.current_sector:
            self._update_sector_memory(self.current_sector, self.sector_stats, crashed=crashed)
            self.previous_sector = self.current_sector
            self.current_sector = sector_id
            self.sector_stats = self._new_sector_stats()
            memory = self._ensure_sector_memory(sector_id)

        space_diff = front_right - front_left
        edge_balance = side_right - side_left
        raw_steering = space_diff * self.steering_gain + edge_balance * self.edge_gain

        if front_clearance > 0.12:
            raw_steering += memory["steering_bias"]

        steering = self._clamp(raw_steering, -1.0, 1.0)
        turn_amount = abs(steering)

        situation = self._classify_situation(front_clearance, turn_amount)
        base_target_speed_kmh = self._target_speed_for(situation)

        if situation in ("emergency", "critical"):
            target_speed_kmh = min(base_target_speed_kmh, base_target_speed_kmh)
        elif situation == "danger":
            target_speed_kmh = base_target_speed_kmh + min(memory["speed_bonus"], 10.0)
        else:
            target_speed_kmh = base_target_speed_kmh + memory["speed_bonus"]

        target_speed_kmh = self._clamp(target_speed_kmh, 0.0, max_speed_kmh)

        speed_error = target_speed_kmh - speed_kmh

        if situation == "emergency":
            throttle = 0.0
            brake = 1.0
        elif situation == "critical":
            throttle = 0.0
            brake = 0.85
        else:
            if speed_error > 90:
                throttle = 1.0
                brake = 0.0
            elif speed_error > 60:
                throttle = 0.9
                brake = 0.0
            elif speed_error > 35:
                throttle = 0.75
                brake = 0.0
            elif speed_error > 15:
                throttle = 0.55
                brake = 0.0
            elif speed_error > 0:
                throttle = 0.30
                brake = 0.0
            elif speed_error > -15:
                throttle = 0.05
                brake = 0.0
            elif speed_error > -35:
                throttle = 0.0
                brake = 0.20
            elif speed_error > -70:
                throttle = 0.0
                brake = 0.45
            else:
                throttle = 0.0
                brake = 0.70

        if situation not in ("emergency", "critical"):
            brake += memory["brake_offset"]

        if situation == "full_straight":
            if front_clearance > 0.85 and turn_amount < 0.15:
                throttle = max(throttle, 1.0)
            if speed_kmh < target_speed_kmh and brake < 0.1:
                brake = 0.0

        if situation == "straight" and speed_error > 40:
            throttle = max(throttle, 0.7)

        if situation == "light_turn" and speed_error > -20:
            brake = 0.0
            throttle = min(0.55, max(throttle, 0.25))

        if situation == "medium_turn" and speed_error > -30:
            brake = min(brake, 0.2)

        if situation in ("sharp_turn", "very_sharp_turn") and speed_error < -10:
            brake = max(brake, 0.35)

        if front_clearance > 0.80 and turn_amount < 0.25 and situation not in ("danger", "critical", "emergency"):
            brake = min(brake, 0.05)

        if brake > 0.1:
            throttle = 0.0

        if speed_kmh < 10.0 and situation != "emergency":
            brake = 0.0
            throttle = max(throttle, 0.3)

        if speed_kmh >= max_speed_kmh:
            throttle = 0.0
            brake = max(brake, 0.3)

        steering = self.previous_steering * 0.65 + steering * 0.35
        throttle = self.previous_throttle * 0.4 + throttle * 0.6

        if situation in ("emergency", "critical", "danger"):
            brake = brake
        else:
            brake = self.previous_brake * 0.3 + brake * 0.7

        steering = self._clamp(steering, -1.0, 1.0)
        throttle = self._clamp(throttle, 0.0, 1.0)
        brake = self._clamp(brake, 0.0, 1.0)

        self.previous_steering = steering
        self.previous_throttle = throttle
        self.previous_brake = brake

        self.sector_stats["min_clearance"] = min(self.sector_stats["min_clearance"], side_left, front_left,
                                                 front_clearance, front_right, side_right)
        self.sector_stats["max_speed_kmh"] = max(self.sector_stats["max_speed_kmh"], speed_kmh)
        self.sector_stats["turn_sum"] += turn_amount
        self.sector_stats["frames"] += 1
        self.sector_stats["last_steering"] = steering
        self.sector_stats["had_emergency"] = self.sector_stats["had_emergency"] or situation == "emergency"
        self.sector_stats["had_critical"] = self.sector_stats["had_critical"] or situation == "critical"

        return {
            "throttle": throttle,
            "brake": brake,
            "steering": steering,
        }
