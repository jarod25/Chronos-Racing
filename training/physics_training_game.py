import json

from ai.heuristic_physics_ai import HeuristicPhysicsAI
from save_manager import build_save_filename, SAVE_DIR
from training.training_game import TrainingGame


class PhysicsTrainingGame(TrainingGame):

    def create_population(self):
        self.pop_size = 1
        ai = HeuristicPhysicsAI()
        if self.load_path is not None and self.load_path.endswith('.json'):
            with open(f"saves/{self.load_path}", "r", encoding="utf-8") as f:
                data = json.load(f)
            memory = data.get("sector_memory", {})
            ai.sector_memory = {int(k) if str(k).isdigit() else k: v for k, v in memory.items()}
        return [ai]

    def compute_action(self, ai, car):
        vision = self.sensor.get_distances(self.circuit, car)
        return ai.forward(
            vision,
            speed_kmh=car.speed_kmh,
            max_speed_kmh=car.max_speed_kmh,
            sector_hint=getattr(car, "last_checkpoint", None),
            crashed=not self.circuit.is_on_track(car.pos),
        )

    def on_new_best(self, best_ai):
        filename = build_save_filename(self.ai_name, self.circuit_name, self.best_time, extension="json")
        payload = {"ai_name": self.ai_name, "circuit_name": self.circuit_name, "best_lap_time": round(self.best_time, 4), "sector_memory": {str(k): v for k, v in best_ai.sector_memory.items()}}
        import os
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(os.path.join(SAVE_DIR, filename), "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def evolve(self, scores):
        return None
