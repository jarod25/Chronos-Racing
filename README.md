# Chronos Racing

Chronos Racing is a Python project about autonomous driving on racing circuits.

The goal is to simulate a car on a 2D track and test different AI driving approaches. The car uses sensors to understand the track, tries to stay on the road, completes laps, and improves its performance depending on the selected AI mode.

This project was made as an end-of-year school project.

## Authors

* [KOHLER Jarod](https://github.com/jarod25)
* [RUNSER Lucas](https://github.com/Naegi-UHA)

## Current state

The project currently includes:

* a 2D driving simulation using Python and Pygame
* a launcher menu
* play mode
* training mode
* multiple AI types
* raycast sensors
* checkpoint detection
* lap timing
* best lap tracking
* AI save/load system
* support for imported track images
* visual options for raycasts and checkpoints
* graph mode for result comparison

The project is functional, but it is still a simplified simulation. It is not meant to be a realistic racing simulator or a production-grade autonomous driving system.

## AI modes

Chronos Racing includes three AI approaches.

### Simple AI

A basic AI that uses sensor data to control the car.
It is mainly used as a simple baseline.

### Physics AI

A heuristic AI that reacts to the track shape and car speed.
It tries to drive more naturally by adapting steering and speed depending on the situation.

### Genetic AI

An AI based on a small neural network trained with a genetic approach.
It can be trained, mutated, saved, and loaded again later.

The genetic AI uses sensor values and car information as inputs, then outputs driving actions such as steering, acceleration, and braking.

## Simulation

The car simulation handles:

* position
* speed
* acceleration
* braking
* steering
* direction
* maximum speed
* off-track detection
* checkpoint progress
* lap timing

The physics are intentionally simplified. The objective is to keep the simulation understandable while still having enough behavior to test autonomous driving logic.

## Sensors

The car uses raycasts to detect the track around it.

Raycasts are lines projected from the car in several directions. They measure how far the car is from the edge of the track. The AI uses these distances to decide how to drive.

Raycasts can also be displayed on screen.

## Tracks

Chronos Racing supports:

* a default track
* imported image-based tracks

Imported tracks should be placed in `assets/tracks/`.

When using an imported track, the program lets the user choose the start position and the initial driving direction manually.

The track system is based on image detection instead of a fixed mathematical equation, which makes it possible to test different circuit layouts.

## Lap timing and checkpoints

The project tracks the car’s progress using checkpoints.

The interface can display:

* current lap time
* last lap time
* best lap time
* delta between the last lap and the best lap
* current generation in training mode
* car speed in km/h
* AI name

This helps compare AI performance during play and training.

## Save system

Trained AI models can be saved in the `saves/` folder.

Save files include information such as:

* AI name
* circuit name
* best lap time

This makes it easier to identify which AI performed best on a given track.

## Requirements

The project requires Python and the dependencies listed in `requirements.txt`.

Main dependencies:

* Pygame
* NumPy
* Matplotlib
* Pandas

Install them with:

`pip install -r requirements.txt`

## How to run

Clone the repository:

`git clone https://github.com/jarod25/Chronos-Racing.git`

Go into the project folder:

`cd Chronos-Racing`

Run the project (if you have installed the dependencies):

`python main.py`

## Graph mode

To launch graph mode:

`python main.py --graph`

## Project structure

Main folders and files:

* `ai/` contains the AI controllers and AI implementations
* `circuits/` contains the track logic
* `gui/` contains the launcher and interface components
* `training/` contains the training modes
* `assets/tracks/` contains imported tracks
* `saves/` contains saved AI models
* `car.py` contains the car simulation
* `game.py` contains the main game loop
* `main.py` is the entry point
* `save_manager.py` handles AI saving and loading
* `graph.py` handles graph mode

## Main technical points

This project includes work on:

* real-time simulation with Pygame
* basic vehicle physics
* autonomous control
* raycast-based perception
* checkpoint-based progress tracking
* lap timing
* genetic algorithm logic
* save/load management
* custom track loading
* user interface states

## Limitations

The project has some known limitations:

* the car physics are simplified
* the AI is experimental
* the genetic training system is basic
* imported tracks need to be visually clear
* there is no realistic tire model
* there are no other cars on track
* there is no advanced collision system
* results may vary depending on the selected track

## Possible improvements

Possible future improvements include:

* better vehicle physics
* more advanced genetic training
* reinforcement learning
* improved track detection
* multiple cars
* ghost mode
* better training statistics
* configurable car parameters
* track editor
* improved UI for training analysis

## License

No license is currently specified.
