"""
Save/Load Module for Bio-Sim
Handles saving and loading simulation states
"""

import os
import json
import datetime
import pickle
import numpy as np
import time  # Add time module for locking
from src.organisms import create_organism

# Simple file-based lock to prevent duplicate saves
_save_in_progress = False

def save_simulation(environment, organisms, filepath=None):
    """
    Save the current simulation state to a file
    
    Args:
        environment: The environment object
        organisms: List of organisms in the simulation
        filepath: Optional file path to save to. If None, auto-generates a name
        
    Returns:
        str: Path where the save file was created
    """
    global _save_in_progress
    
    # Check if a save is already in progress
    if _save_in_progress:
        print("Save already in progress, ignoring duplicate save request")
        return None
    
    try:
        # Set lock
        _save_in_progress = True
        
        print(f"save_simulation called with {len(organisms)} organisms")  # Debug log
        
        # Generate timestamp for filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create default filepath if none provided
        if filepath is None:
            # Ensure the directory exists
            os.makedirs("data", exist_ok=True)
            filepath = f"data/sim_save_{timestamp}.biosim"
        
        print(f"Saving to file: {filepath}")  # Debug log
        
        # Prepare serializable data
        save_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "config": environment.config,
            "organisms": [],
            "environment": {
                "width": environment.width,
                "height": environment.height,
                "tick_count": environment.tick_count,
                "temperature_grid": environment.temperature_grid.tolist(),
                "ph_grid": environment.ph_grid.tolist(),
                "nutrient_grid": environment.nutrient_grid.tolist(),
                "flow_rate_grid": environment.flow_rate_grid.tolist()
            }
        }
        
        # Save organism data
        for organism in organisms:
            if not organism.is_alive:
                continue
            
            # Common organism data
            org_data = {
                "type": organism.get_type(),
                "x": organism.x,
                "y": organism.y,
                "size": organism.size,
                "color": organism.color,
                "base_speed": organism.base_speed,
                "velocity": organism.velocity,
                "age": organism.age,
                "energy": organism.energy,
                "health": organism.health,
                "is_alive": organism.is_alive,
                "dna": organism.dna,
                "id": organism.id
            }
            
            # Type-specific properties
            if organism.get_type() == "bacteria":
                org_data.update({
                    "reproduction_rate": organism.reproduction_rate,
                    "nutrient_consumption": organism.nutrient_consumption,
                    "optimal_temperature": organism.optimal_temperature,
                    "optimal_ph": organism.optimal_ph
                })
            elif organism.get_type() == "virus":
                org_data.update({
                    "infection_chance": organism.infection_chance,
                    "virulence": organism.virulence,
                    "replication_rate": organism.replication_rate,
                    "host_id": organism.host.id if organism.host else None,
                    "dormant_counter": organism.dormant_counter
                })
            elif organism.get_type() == "white_blood_cell":
                org_data.update({
                    "detection_radius": organism.detection_radius,
                    "attack_strength": organism.attack_strength,
                    "memory_capacity": organism.memory_capacity,
                    "pathogen_memory": organism.pathogen_memory,
                    "target_id": organism.target.id if organism.target else None
                })
            
            save_data["organisms"].append(org_data)
        
        # Save data to file
        with open(filepath, 'wb') as f:
            pickle.dump(save_data, f)
        
        print(f"Simulation saved to {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Error saving simulation: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Release lock
        _save_in_progress = False

def load_simulation(filepath):
    """
    Load a simulation state from a file
    
    Args:
        filepath (str): Path to the save file
        
    Returns:
        tuple: (environment, organisms) loaded from the save file
    """
    try:
        with open(filepath, 'rb') as f:
            save_data = pickle.load(f)
        
        # Get configuration
        config = save_data["config"]
        
        # Recreate environment
        from src.environment import Environment
        
        env_data = save_data["environment"]
        environment = Environment(
            env_data["width"],
            env_data["height"],
            config
        )
        
        # Restore environment grids
        environment.tick_count = env_data["tick_count"]
        environment.temperature_grid = np.array(env_data["temperature_grid"])
        environment.ph_grid = np.array(env_data["ph_grid"])
        environment.nutrient_grid = np.array(env_data["nutrient_grid"])
        environment.flow_rate_grid = np.array(env_data["flow_rate_grid"])
        
        # Attach simulation reference to environment for compatibility
        environment.simulation = None  # This will be set by the simulation later
        
        # Recreate organisms
        organisms = []
        organism_lookup = {}  # For resolving references
        
        # Import necessary classes directly for restoration
        # Import bacteria types
        from src.organisms.bacteria import EColi, Streptococcus, BeneficialBacteria
        
        # Import virus types
        from src.organisms.virus import Influenza, Rhinovirus, Coronavirus, Adenovirus
        
        # Import immune cell types
        from src.organisms.white_blood_cell import Neutrophil, Macrophage, TCell
        
        # Import body cell types
        from src.organisms.body_cells import RedBloodCell, EpithelialCell, Platelet
        
        # Map organism type strings to their classes
        organism_classes = {
            "bacteria": EColi,  # Default to EColi for generic bacteria
            "beneficial_bacteria": BeneficialBacteria,
            "EColi": EColi,
            "Streptococcus": Streptococcus,
            "BeneficialBacteria": BeneficialBacteria,
            "virus": Influenza,  # Default to Influenza for generic virus
            "Influenza": Influenza,
            "Rhinovirus": Rhinovirus,
            "Coronavirus": Coronavirus,
            "Adenovirus": Adenovirus,
            "white_blood_cell": Neutrophil,  # Default to Neutrophil for generic WBC
            "Neutrophil": Neutrophil,
            "Macrophage": Macrophage,
            "TCell": TCell,
            "RedBloodCell": RedBloodCell,
            "EpithelialCell": EpithelialCell,
            "Platelet": Platelet
        }
        
        for org_data in save_data["organisms"]:
            # Get the class for this organism type
            org_class = organism_classes.get(org_data["type"])
            
            if org_class:
                # Create instance directly
                organism = org_class(
                    org_data["x"],
                    org_data["y"],
                    org_data["size"],
                    org_data["color"],
                    org_data["base_speed"]
                )
                
                # Restore common properties
                organism.velocity = org_data["velocity"]
                organism.age = org_data["age"]
                organism.energy = org_data["energy"]
                organism.health = org_data["health"]
                organism.is_alive = org_data["is_alive"]
                organism.dna = org_data["dna"]
                organism.id = org_data["id"]
                
                # Restore type-specific properties
                if "reproduction_rate" in org_data:
                    organism.reproduction_rate = org_data["reproduction_rate"]
                if "infection_chance" in org_data:
                    organism.infection_chance = org_data["infection_chance"]
                if "detection_radius" in org_data:
                    organism.detection_radius = org_data["detection_radius"]
                
                # Track for lookup
                organism_lookup[organism.id] = organism
                organisms.append(organism)
            else:
                print(f"Warning: Unknown organism type '{org_data['type']}' in save file")
        
        # Restore relationships between organisms
        for i, org_data in enumerate(save_data["organisms"]):
            # Restore host relationship for viruses
            if "host_id" in org_data and org_data["host_id"] and org_data["host_id"] in organism_lookup:
                organisms[i].host = organism_lookup[org_data["host_id"]]
            
            # Restore target relationship for white blood cells
            if "target_id" in org_data and org_data["target_id"] and org_data["target_id"] in organism_lookup:
                organisms[i].target = organism_lookup[org_data["target_id"]]
        
        # Print summary of loaded state
        print(f"Loaded {len(organisms)} organisms from save")
        return environment, organisms
        
    except Exception as e:
        print(f"Error loading simulation: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def list_saved_simulations():
    """
    List all saved simulation files
    
    Returns:
        list: List of saved simulation file paths
    """
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Find all .biosim files
    save_files = []
    for filename in os.listdir("data"):
        if filename.endswith(".biosim"):
            filepath = os.path.join("data", filename)
            save_files.append(filepath)
    
    return save_files 