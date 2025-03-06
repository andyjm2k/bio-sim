#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to validate the simulation initialization and update logic
"""

import json
import os
import sys
import traceback
import time

# Set environment variable for headless pygame
os.environ['SDL_VIDEODRIVER'] = 'dummy'

from src.simulation import BioSimulation

def test_simulation():
    """
    Test the simulation by loading configuration and running a few update cycles.
    """
    print("Testing simulation...")
    
    try:
        # Load configuration
        config_path = 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        print("Configuration loaded successfully!")
        print(f"Max organisms: {config.get('simulation', {}).get('max_organisms', 'Not specified')}")
        
        # Initialize simulation
        print("Initializing simulation...")
        simulation = BioSimulation(config)
        print("Simulation initialized successfully!")
        
        # Run a few update cycles
        print("Testing a few update cycles...")
        for i in range(5):
            print(f"Update cycle {i+1}")
            simulation.update_organisms()
            time.sleep(0.1)  # Brief pause to prevent excessive CPU usage
            
        print("All update cycles completed successfully!")
        print("Test result: SUCCESS")
        return True
    except Exception as e:
        print(f"Error during {sys._getframe().f_back.f_code.co_name if sys._getframe().f_back else 'unknown'}: {str(e)}")
        print(traceback.format_exc())
        print("Test result: FAILURE")
        return False

if __name__ == "__main__":
    result = test_simulation()
    exit(0 if result else 1) 