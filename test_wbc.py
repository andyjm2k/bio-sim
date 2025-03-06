import os
# Set headless mode for pygame
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import sys
from src.organisms.white_blood_cell import Neutrophil
from src.organisms.virus import Rhinovirus
from src.environment.environment import Environment

print("Creating test environment...")
config = {
    "simulation": {
        "width": 2560,
        "height": 1920,
        "world_width": 2560,
        "world_height": 1920,
        "max_organisms": 3000,
        "environment": "bloodstream"
    },
    "environment_settings": {
        "bloodstream": {
            "temperature": 37.0,
            "ph": 7.4,
            "oxygen_level": 95.0,
            "nutrient_level": 80.0
        }
    }
}
env = Environment(2560, 1920, config)

print("Creating test Neutrophil...")
neutrophil = Neutrophil(x=100, y=100, size=10, color=(255, 255, 255), speed=0.5)

print("Creating test Rhinovirus...")
rhinovirus = Rhinovirus(x=120, y=120, size=3, color=(255, 0, 0), speed=1.5)

print("Setting Rhinovirus as Neutrophil's target...")
neutrophil.target = rhinovirus

print("Calling update method...")
try:
    neutrophil.update(env)
    print("Target successfully processed!")
    print("Test completed successfully!")
except Exception as e:
    print(f"Error during update: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc() 