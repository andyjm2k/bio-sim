#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bio-Sim: Human Microbiome Simulation
Main entry point for running the simulation
"""

import sys
import os
import json
import argparse
import pygame
import numpy as np
from pygame.locals import *
import traceback

# Import custom modules
from src.organisms import create_organism
from src.environment import Environment
from src.visualization import Renderer, TreatmentPanel
from src.utils import save_simulation, load_simulation, list_saved_simulations
from src.simulation import BioSimulation

# Initialize default configuration
DEFAULT_CONFIG = {
    "simulation": {
        "width": 800,
        "height": 600,
        "fps": 60,
        "background_color": (10, 10, 40),
        "initial_organisms": 100,
        "environment": "intestine"  # Options: intestine, skin, mouth, etc.
    },
    "simulation_settings": {
        "max_organisms": 200,
        "performance_mode": True,
        "mutation_rate": 0.001,
        "interaction_radius": 20
    },
    "environment_settings": {
        "intestine": {
            "ph_level": 6.5,
            "temperature": 37.0,
            "nutrients": 100,
            "flow_rate": 0.5
        },
        "skin": {
            "ph_level": 5.5,
            "temperature": 33.0,
            "nutrients": 50,
            "flow_rate": 0.1
        },
        "mouth": {
            "ph_level": 7.0,
            "temperature": 36.5,
            "nutrients": 80,
            "flow_rate": 0.3
        }
    },
    "organism_types": {
        "EColi": {
            "count": 40,
            "size_range": [4, 7],
            "speed_range": [0.8, 1.8],
            "colors": [[200, 100, 100]],
            "description": "Common gut bacteria, rod-shaped"
        },
        "Streptococcus": {
            "count": 40,
            "size_range": [3, 6],
            "speed_range": [0.5, 1.5],
            "colors": [[100, 200, 100]],
            "description": "Spherical bacteria often found in chains"
        },
        "BeneficialBacteria": {
            "count": 20,
            "size_range": [3, 8],
            "speed_range": [0.6, 1.6],
            "colors": [[100, 180, 220]],
            "description": "Probiotic bacteria that improve gut health"
        },
        "Influenza": {
            "count": 15,
            "size_range": [2, 4],
            "speed_range": [1.2, 2.8],
            "colors": [[255, 50, 50]],
            "description": "Flu virus that infects respiratory cells"
        },
        "Rhinovirus": {
            "count": 15,
            "size_range": [2, 3],
            "speed_range": [1.0, 2.5],
            "colors": [[255, 150, 50]],
            "description": "Common cold virus"
        },
        "Neutrophil": {
            "count": 10,
            "size_range": [8, 12],
            "speed_range": [0.4, 1.2],
            "colors": [[220, 220, 250]],
            "description": "General immune system cell that targets bacteria and viruses"
        },
        "Macrophage": {
            "count": 5,
            "size_range": [10, 15],
            "speed_range": [0.3, 0.9],
            "colors": [[200, 200, 240]],
            "description": "Large immune cell that engulfs pathogens"
        },
        "TCell": {
            "count": 5,
            "size_range": [7, 10],
            "speed_range": [0.6, 1.4],
            "colors": [[240, 240, 255]],
            "description": "Specialized immune cell that targets specific pathogens"
        }
    }
}

def load_config(config_path):
    """
    Load configuration from a JSON file
    
    Args:
        config_path (str): Path to configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
            # Convert color arrays to tuples for pygame
            if "simulation" in config and "background_color" in config["simulation"]:
                config["simulation"]["background_color"] = tuple(config["simulation"]["background_color"])
            
            return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading configuration: {e}")
        print("Using default configuration.")
        return DEFAULT_CONFIG

def main():
    """Entry point for the simulation"""
    parser = argparse.ArgumentParser(description="Bio-Sim: Human Microbiome Simulation")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--load", help="Path to saved simulation file to load")
    args = parser.parse_args()
    
    try:
        print("Starting simulation...")
        
        # Load configuration
        config = None
        if args.config:
            config = load_config(args.config)
            if config is None:
                print(f"Failed to load config from {args.config}, using default")
                config = DEFAULT_CONFIG
        else:
            config = DEFAULT_CONFIG
        
        print(f"Loaded configuration with {len(config)} top-level keys")
        
        # Display initial settings
        max_organisms = config.get("simulation_settings", {}).get("max_organisms", 0)
        performance_mode = config.get("simulation_settings", {}).get("performance_mode", False)
        print(f"Starting with max organisms: {max_organisms if max_organisms > 0 else 'unlimited'}")
        print(f"Performance mode: {'enabled' if performance_mode else 'disabled'}")
        print(f"Organism types: {list(config.get('organism_types', {}).keys())}")
        
        # Create and run simulation
        print("Initializing simulation...")
        simulation = BioSimulation(config)
        
        # Load saved state if specified
        if args.load and os.path.exists(args.load):
            environment, organisms = load_simulation(args.load)
            if environment and organisms:
                simulation.environment = environment
                simulation.organisms = organisms
                simulation.environment.simulation = simulation
                print(f"Loaded simulation from {args.load}")
            else:
                print(f"Failed to load simulation from {args.load}")
        
        print("Running simulation main loop...")
        return simulation.run()
    except Exception as e:
        print(f"Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main() 