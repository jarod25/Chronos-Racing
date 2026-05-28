import numpy as np

from ai.genetic_ai import GeneticAI
from save_manager import load_ai, replace_best_save
from training.training_game import TrainingGame


class GeneticTrainingGame(TrainingGame):

    def create_population(self):
        self.pop_size = 50
        if self.load_path is not None:
            base_ai = load_ai(GeneticAI, self.load_path)
            ais = [base_ai.copy() for _ in range(self.pop_size)]
            for i in range(1, self.pop_size):
                ais[i].mutate(rate=0.02)
            return ais
        return [GeneticAI(input_size=self.input_size) for _ in range(self.pop_size)]

    def compute_action(self, ai, car):
        vision = self.sensor.get_distances(self.circuit, car)
        vision.append(car.speed_kmh / car.max_speed_kmh)
        vision.append(np.sin(car.angle))
        vision.append(np.cos(car.angle))
        action = ai.forward(np.array(vision))
        action += np.random.randn(2) * 0.02
        action = np.clip(action, -1, 1)
        return action

    def on_new_best(self, best_ai):
        replace_best_save(
            ai=best_ai,
            ai_name=self.ai_name,
            circuit_name=self.circuit_name,
            time_s=self.best_time,
            extension="npz",
        )

    def evolve(self, scores):
        sorted_idx = np.argsort(scores)[::-1]
        parent_count = min(20, len(sorted_idx))
        parents = sorted_idx[:parent_count]
        new_ais = [self.ais[parents[0]].copy()]
        while len(new_ais) < self.pop_size:
            parent = self.ais[np.random.choice(parents)]
            child = parent.copy()
            child.mutate(rate=0.05)
            new_ais.append(child)
        self.ais = new_ais
