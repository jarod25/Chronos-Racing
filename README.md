# Chronos Racing

Chronos Racing is a circuit-based autonomous driving simulation project that combines realistic physics modeling and
artificial intelligence to optimize racing performance.

## Current state

The project currently includes:

- a basic car simulation
- a simple AI model
- a default oval track
- support for importing custom track images
- automatic track detection from the selected start point
- manual selection of the car start position and direction

At this stage, the project is still experimental. The AI is very simple and does not really learn yet. The current focus
is mainly on building a clean simulation base before improving the training system.

## Project goal

Later versions should include:

- better vehicle physics
- improved steering and acceleration behavior
- AI training
- lap timing
- support for different tracks
- performance comparison between runs

## Run

```bash
python main.py
```

## Tracks

Imported tracks should be placed in:

```
assets/tracks/
```

The program lets you choose a track image, then click on the track to set the start position and driving direction.