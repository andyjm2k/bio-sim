import os
import sys
import pygame

# Set headless mode for pygame
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# Import necessary modules
from src.organisms.white_blood_cell import Neutrophil, Macrophage, TCell
from src.organisms.bacteria import BeneficialBacteria
from src.environment.environment import Environment

def test_bacteria_interaction():
    print("Starting bacteria interaction test...")
    
    # Initialize pygame
    pygame.init()
    
    # Create a simple config
    config = {
        "simulation": {
            "world_width": 2560,
            "world_height": 1920,
            "temperature": 37.0,
            "ph": 7.4,
            "environment": "bloodstream"
        },
        "environment_settings": {
            "bloodstream": {
                "temperature": 37.0,
                "ph": 7.4,
                "nutrient_level": 0.8,
                "oxygen_level": 0.95
            }
        }
    }
    
    # Create environment
    env = Environment(width=2560, height=1920, config=config)
    
    # Create test organisms
    neutrophil = Neutrophil(x=100, y=100, size=10, color=(255, 255, 255), speed=0.5)
    beneficial_bacteria = BeneficialBacteria(x=110, y=110, size=5, color=(0, 255, 0), speed=0.2)
    
    print(f"Created Neutrophil at ({neutrophil.x}, {neutrophil.y})")
    print(f"Created BeneficialBacteria at ({beneficial_bacteria.x}, {beneficial_bacteria.y})")
    
    # Test interaction
    print("Testing interaction...")
    result = neutrophil.interact(beneficial_bacteria, env)
    print(f"Interaction result: {result}")
    
    # Test type checking
    print(f"BeneficialBacteria get_type(): {beneficial_bacteria.get_type()}")
    
    # Print Neutrophil attributes
    print(f"Neutrophil has target: {neutrophil.has_target}")
    print(f"Neutrophil detection radius: {neutrophil.detection_radius}")
    
    print("Interaction test completed successfully!")

if __name__ == "__main__":
    test_bacteria_interaction() 