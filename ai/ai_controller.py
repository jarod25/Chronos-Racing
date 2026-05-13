import numpy as np

from ai.genetic_ai import GeneticAI
from ai.simple_ai import SimpleAI
from save_manager import load_ai


class SimpleAIController:
    def __init__(self):
        self.ai = SimpleAI(1.8)

    def get_action(self, circuit, car, sensor):
        vision = sensor.get_distances(circuit, car)
        return self.ai.forward(vision)


class GeneticAIController:
    def __init__(self, load_path):
        if load_path is None:
            raise ValueError("Une IA génétique doit être chargée avec --load.")

        self.ai = load_ai(GeneticAI, load_path)

    def get_action(self, circuit, car, sensor):
        vision = sensor.get_distances(circuit, car)

        vision.append(car.speed / 5.0)
        vision.append(np.sin(car.angle))
        vision.append(np.cos(car.angle))

        vision = np.array(vision)

        return self.ai.forward(vision)


def create_ai_controller(ai_name, load_path=None):
    if ai_name == "simple":
        return SimpleAIController()

    if ai_name == "genetic":
        return GeneticAIController(load_path)

    raise ValueError(f"IA inconnue : {ai_name}")
