# Bio-Sim: Human Microbiome Simulation

## Project Overview
This is a visual simulation of a micro organism world located in the human body. It simulates all the interactions between the micro organisms in the human body in the most accurate way possible. Each organism has its own unique characteristics and behaviors replicating the real world. Each organism has its own unique DNA sequence and is powered by a custom made unique neural network.

## Core Functionalities
- **Realistic Microorganism Simulation**: Accurate modeling of various microorganisms found in the human body
- **Interactive Visualization**: Real-time visual representation of microorganism interactions
- **DNA Sequence Modeling**: Custom DNA sequences for each organism that influence behavior and characteristics
- **Neural Network Integration**: Each organism operates based on a unique neural network
- **Environmental Factors**: Simulation of different body conditions and their effects on microorganisms
- **User Interaction**: Ability to modify simulation parameters and observe changes in the ecosystem
- **Pathogen Visualization**: Distinctive visual representations for different pathogen types
- **Dynamic Organism Interactions**: Realistic interactions between organisms based on their type and proximity

## Recent Updates

### Bug Fixes
- **Environment Object Attribute Fix**: Resolved an issue where the Environment object was missing the `get_nearby_organisms` method, which caused errors when virus organisms attempted to reproduce.
- **Virus Visualization**: Improved rendering for all virus types to ensure distinctive appearances.
- **Default Configuration**: Updated the default configuration to include at least one of each pathogen type for a more comprehensive simulation experience.

### New Features & Improvements
- **Enhanced Environment API**: Improved the Environment class with better methods for spatial organism queries.
- **Comprehensive Unit Tests**: Added tests for the Environment class and its spatial query capabilities.
- **Documentation Updates**: Expanded README with detailed information about all project components.
- **Improved Pathogen Ecology**: Balanced pathogen reproduction and interaction systems.

## Completed Features

The following features have been implemented:

### Organism Types
- **Bacteria**: 
  - **EColi**: Common gut bacteria with distinct rod shape
  - **Streptococcus**: Spherical bacteria often found in chains
  - **BeneficialBacteria**: Probiotic bacteria that improve gut health
  - **Staphylococcus**: Resilient spherical bacteria with antibiotic resistance
  - **Salmonella**: Pathogenic bacteria with high virulence
- **Viruses**: 
  - **Influenza**: Flu virus that infects respiratory cells with distinctive hemagglutinin and neuraminidase spikes
  - **Rhinovirus**: Common cold virus with enhanced reproduction in cooler temperatures
  - **Coronavirus**: Respiratory virus with crown of distinctive spike proteins
  - **Adenovirus**: DNA virus with icosahedral shape and fiber projections
- **Immune Cells**: 
  - **WhiteBloodCell**: General immune system cell
  - **Macrophage**: Large immune cell that engulfs pathogens
  - **TCell**: Specialized immune cell that targets specific pathogens
- **Other Cells**:
  - **RedBloodCell**: Carries oxygen through the bloodstream
  - **EpithelialCell**: Forms protective barriers in the body
  - **Platelet**: Small cell fragments involved in blood clotting

### DNA and Neural Networks
- **DNA Influence**: Each organism has a unique DNA sequence that affects its properties
- **DNA Traits**: Specialized traits like temperature preferences, pH preferences, and antibiotic resistance
- **Neural Network Decision-Making**: Organisms make decisions using simple neural networks
- **DNA-Based Mutations**: Offspring inherit traits with random mutations
- **Trait Expression**: DNA sequences directly influence organism behavior and environmental responses

### Environmental Factors
- **Temperature Gradients**: Different body environments have varying temperatures
- **pH Levels**: Environments have different acidity levels affecting organisms
- **Nutrient Distribution**: Nutrients are distributed throughout the environment
- **Flow Simulation**: Simple fluid dynamics affecting nutrient distribution
- **Environmental Transitions**: Smooth transitions between different body environments (intestine, skin, mouth)
- **Spatial Organism Tracking**: Environment maintains spatial relationships between organisms
- **Environmental Conditions Effect**: Organisms respond differently to environmental conditions based on their type

### Visualization System
- **Real-time Rendering**: Organisms are displayed with distinctive colors and sizes
- **Environmental Visualization**: Toggle different views (temperature, pH, nutrients, flow)
- **Zoom and Pan**: Navigate through the simulation view
- **Statistics Display**: Real-time organism counts and simulation metrics
- **Grid Display**: Optional coordinate grid for better spatial understanding
- **Unique Virus Rendering**: Each virus type has custom visualization:
  - **Influenza**: Red spherical particles with alternating hemagglutinin (bulb-ended) and neuraminidase (mushroom-shaped) surface proteins
  - **Coronavirus**: Purple particles with crown of distinctive spikes with bulbs at the ends
  - **Adenovirus**: Red icosahedral structure with fiber projections at vertices
  - **Rhinovirus**: Blue circular particles (uses base virus rendering)
- **Antibody Visualization**: Pulsating, dashed circles appear around viruses when marked by immune system
- **Organism State Indicators**: Visual cues for infection status, damage, and other organism states

### Simulation Architecture
- **Modular Design**: Clear separation between organism behavior, environment, and visualization
- **Spatial Optimization**: Grid-based spatial partitioning for efficient organism interaction queries
- **Centralized Simulation Control**: Main simulation class coordinates all components
- **Environment Delegation**: Environment class provides consistent API for accessing conditions and nearby organisms
- **Event-Driven Interactions**: Organisms respond to events and interact based on proximity and type
- **Reproducible Randomness**: Controlled random number generation for deterministic outcomes
- **Configuration-Driven Setup**: All simulation parameters controllable through JSON configuration

### Simulation Controls
- **Save/Load States**: Save simulation state and load it later
- **Pause/Resume**: Control simulation flow
- **Parameter Adjustment**: Configure simulation through the config.json file
- **Reset**: Restart the simulation with initial conditions
- **Environment Switching**: Cycle between different body environments
- **Performance Modes**: Toggle between standard and high-performance rendering

### Treatment Panel
- **Interactive Treatments**: Apply synthetic treatments to the simulation through an interactive panel
- **Treatment Types**:
  - **Antibiotics**: Target and kill bacteria with configurable specificity
  - **Antivirals**: Reduce viral reproduction and efficacy
  - **Probiotics**: Introduce beneficial bacteria to the environment
  - **Immunizations**: Boost immune system response against specific pathogens
- **Real-time Effects**: Observe how treatments affect the microorganism population
- **Treatment Resistance**: Organisms can develop resistance to treatments over time

## Installation

### Prerequisites
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- Any modern operating system (Windows, macOS, Linux)

### Setup Instructions
1. Clone this repository:
   ```
   git clone https://github.com/yourusername/bio-sim.git
   cd bio-sim
   ```

2. Set up the virtual environment:
   ```
   # On Windows
   python -m venv bio_py
   bio_py\Scripts\activate

   # On macOS/Linux
   python -m venv bio_py
   source bio_py/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the Simulation
1. Activate your virtual environment (if not already activated):
   ```
   # On Windows
   bio_py\Scripts\activate

   # On macOS/Linux
   source bio_py/bin/activate
   ```

2. Start the simulation:
   ```
   python run_simulation.py
   ```

   With custom configuration:
   ```
   python run_simulation.py --config custom_config.json
   ```

   Load a saved state:
   ```
   python run_simulation.py --load data/sim_save_20250228.biosim
   ```

### Basic Controls
- **ESC**: Quit the simulation
- **Space**: Pause/Resume simulation
- **Arrow Keys**: Navigate the view
- **+/-**: Zoom in/out
- **R**: Reset simulation
- **S**: Save current state
- **L**: Load saved state
- **E**: Toggle between environments (intestine, skin, mouth)
- **Tab**: Cycle through environment views (temperature, pH, nutrients, flow)
- **G**: Toggle grid display
- **H**: Toggle statistics display
- **T**: Toggle treatment panel
- **Click on Organism**: Display detailed information about the selected organism

### Treatment Panel
The treatment panel allows you to introduce synthetic treatments to the microorganism environment:

1. Press **T** to open the treatment panel
2. Use the **Up/Down arrow keys** or **mouse** to select a treatment
3. Press **Space/Enter** or click the **Apply** button to administer the selected treatment
4. Observe how the treatment affects the simulation

Available treatments include:
- **Antibiotics**: Kill bacteria (broad-spectrum or targeted)
- **Antivirals**: Inhibit virus reproduction
- **Probiotics**: Introduce beneficial bacteria
- **Immunizations**: Boost immune system response against specific pathogens

## Project Structure
```
bio-sim/
├── bio_py/              # Python virtual environment
├── data/                # Simulation data files and save states
├── models/              # Neural network models 
├── src/                 # Source code
│   ├── organisms/       # Microorganism implementations
│   │   ├── bacteria.py  # Bacterial organism classes
│   │   ├── virus.py     # Virus classes with custom rendering
│   │   ├── white_blood_cell.py  # Immune cell implementations
│   │   └── body_cells.py  # Host cell implementations
│   ├── environment/     # Simulation environment
│   │   └── environment.py  # Environment class with condition management
│   ├── visualization/   # Rendering and UI components
│   │   ├── renderer.py  # Main rendering engine
│   │   └── treatment_panel.py  # Treatment UI
│   └── utils/           # Utility functions and treatments
├── tests/               # Unit tests
│   ├── test_organisms.py  # Tests for organism behaviors
│   ├── test_environment.py  # Tests for environment class
│   └── test_virus_types.py  # Tests for virus-specific behaviors
├── run_simulation.py    # Main entry point
├── config.json          # Simulation configuration
├── requirements.txt     # Project dependencies
└── README.md            # Project documentation
```

## Technical Details

### Technologies Used
- **Python**: Core programming language
- **NumPy/SciPy**: Scientific computing and data processing
- **Pygame**: Visualization and user interface
- **Random State Generation**: Deterministic random number generation for reproducibility
- **Matplotlib**: Data visualization and analysis

### Simulation Parameters
The simulation can be configured through the `config.json` file with the following parameters:
- Initial organism population and counts for each type
- Size and speed ranges for different organism types
- Environmental conditions (pH, temperature, nutrients, flow)
- Visualization settings
- Performance settings (max organism count, performance mode)
- Treatment efficacy settings

### Environment System
The Environment class manages all environmental conditions and organism interactions:
- **Condition Grids**: Maintains grids for temperature, pH, nutrients, and flow
- **Spatial Queries**: Methods to find organisms within a specific radius
- **Condition Access**: Provides access to environmental conditions at any coordinate
- **Organism Delegation**: Delegates organism queries to the main simulation
- **Resource Management**: Handles nutrient consumption and distribution

### Organism Interaction System
The organism interaction system manages how different organisms interact:
- **Proximity Detection**: Uses spatial grid for efficient nearby organism queries
- **Type-Based Behavior**: Interactions differ based on organism types
- **Host-Pathogen Dynamics**: Pathogens can infect host cells and reproduce
- **Immune Response**: Immune cells detect and target pathogens
- **Resource Competition**: Organisms compete for nutrients and space

### Visualization Pipeline
The visualization system renders all simulation elements:
- **Layer-Based Rendering**: Different elements are rendered in specific order
- **Custom Organism Sprites**: Each organism type has custom rendering function
- **Environmental Overlays**: Optional views of environmental conditions
- **Camera Controls**: Pan and zoom functionality
- **UI Elements**: Statistics, control panels, and interactive elements
- **Performance Optimization**: Selective rendering for off-screen elements

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Running Tests
The project includes a comprehensive test suite to ensure all components work correctly. We use Python's `unittest` framework for testing.

### Using the Test Runner
We provide a master test runner script that can discover and run all tests:

```bash
# Run all tests
python run_tests.py

# Run tests with verbose output
python run_tests.py -v

# Run a specific test file
python run_tests.py tests/test_environment.py

# Run tests matching a specific pattern
python run_tests.py -p "*virus*.py"
```

### Test Organization
- **Unit Tests**: Located in the `tests/` directory
- **Integration Tests**: Test files in the project root with name pattern `test_*.py`
- **Test Coverage**: Tests cover core simulation logic, organism behavior, visualization, and save/load functionality

### Adding New Tests
When adding new features, include corresponding test cases following these guidelines:
1. Place unit tests in the `tests/` directory
2. Follow the naming convention `test_*.py`
3. Use the `unittest.TestCase` base class
4. Include proper docstrings and comments

## Acknowledgements
- [Reference Paper 1]
- [Reference Paper 2]
- [Relevant Research Project]
