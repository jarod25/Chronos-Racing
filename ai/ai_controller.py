import numpy as np

from ai.genetic_ai import GeneticAI
from ai.heuristic_physics_ai import HeuristicPhysicsAI
from ai.simple_ai import SimpleAI
from save_manager import load_ai


class SimpleAIController:
    def __init__(self):
        self.ai = SimpleAI(1.8)

    def get_action(self, circuit, car, sensor):
        vision = sensor.get_distances(circuit, car)
        return self.ai.forward(
            vision,
            speed_kmh=car.speed_kmh,
            max_speed_kmh=car.max_speed_kmh,
        )


class PhysicsAIController:
    def __init__(self):
        self.ai = HeuristicPhysicsAI(steering_gain=1.7, edge_gain=0.45)

    def get_action(self, circuit, car, sensor):
        vision = sensor.get_distances(circuit, car)
        return self.ai.forward(
            vision,
            speed_kmh=car.speed_kmh,
            max_speed_kmh=car.max_speed_kmh,
            sector_hint=getattr(car, "last_checkpoint", None),
            crashed=not circuit.is_on_track(car.pos),
        )


class GeneticAIController:
    def __init__(self, load_path=None):
        if load_path is None:
            self.ai = GeneticAI()
            print("Fresh Genetic AI created. It is untrained.")
        else:
            self.ai = load_ai(GeneticAI, load_path)

    def get_action(self, circuit, car, sensor):
        vision = sensor.get_distances(circuit, car)

        vision.append(car.speed_kmh / car.max_speed_kmh)
        vision.append(np.sin(car.angle))
        vision.append(np.cos(car.angle))

        vision = np.array(vision)
        output = self.ai.forward(vision)
        return GeneticAI.to_car_action(output)


def create_ai_controller(ai_name, load_path=None):
    if ai_name == "simple":
        return SimpleAIController()

    if ai_name == "physics":
        return PhysicsAIController()

    if ai_name == "genetic":
        return GeneticAIController(load_path)

    raise ValueError(f"IA inconnue : {ai_name}")
