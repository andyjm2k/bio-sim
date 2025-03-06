# Bio-Sim

A biological simulation system that models interactions between various microorganisms, immune cells, and environmental factors.

## Overview

Bio-Sim is a comprehensive simulation of biological systems at the microscopic level. It features:

- **Multiple Organism Types**: Bacteria (E. Coli, Streptococcus, Salmonella, Staphylococcus, Beneficial Bacteria), Viruses (Influenza, Rhinovirus, Coronavirus, Adenovirus), and Immune Cells (Neutrophils, Macrophages, T-Cells)
- **Dynamic Environment**: Simulates different body environments with varying temperature, pH levels, nutrient availability, and flow rates
- **Realistic Behaviors**: Organisms reproduce, interact, attack, defend, and respond to environmental changes
- **Immune Response Simulation**: Immune cells actively seek out and neutralize threats based on sophisticated targeting algorithms
- **Visualization System**: Real-time rendering of the simulation with statistics display

## Requirements

- Python 3.8+
- PyGame 2.0+
- NumPy

## Installation

1. Clone this repository
2. Create a virtual environment (optional)
3. Install dependencies:

```bash
pip install pygame numpy
```

## Running the Simulation

Run the main simulation script:

```bash
python run_simulation.py
```

You can configure the simulation by editing the `config.json` file to change organism counts, environmental settings, and visualization options.

## Features

### Organism Types

- **Bacteria**: Various species with different properties, reproduction rates, and environmental preferences
- **Viruses**: Can infect cells and reproduce through their host
- **Immune Cells**: Actively hunt pathogens with different targeting strategies
- **Body Cells**: Represent the host organism's cells that can be infected or damaged

### Environment Simulation

The simulation supports multiple environment types (intestine, skin, mouth) with different properties:
- Temperature
- pH level
- Nutrient availability
- Flow rate

### Interaction System

Organisms interact with each other in various ways:
- Bacteria can consume nutrients and reproduce
- Viruses can infect host cells
- Immune cells can target and neutralize threats
- Environmental factors can affect organism behavior and health

## Configuration

The `config.json` file allows you to customize:

- Initial organism counts
- Environmental settings
- Organism properties (size, speed, color)
- Simulation rules (reproduction thresholds, interaction distances)

## License

[MIT License](LICENSE)
