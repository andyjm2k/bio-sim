"""
Organisms Package Initialization
Contains classes for all microorganisms in the simulation
"""

from src.organisms.bacteria import Bacteria, EColi, Streptococcus, BeneficialBacteria, Salmonella, Staphylococcus
from src.organisms.virus import Virus, Influenza, Rhinovirus, Coronavirus, Adenovirus
from src.organisms.white_blood_cell import Neutrophil, Macrophage, TCell
from src.organisms.body_cells import BodyCell, RedBloodCell, EpithelialCell, Platelet

def create_organism(organism_type, x, y, environment):
    """
    Factory function to create organisms of the specified type
    
    Args:
        organism_type (str): Type of organism to create 
            Bacteria: 'EColi', 'Streptococcus', 'BeneficialBacteria', 'Salmonella', 'Staphylococcus'
            Viruses: 'Influenza', 'Rhinovirus', 'Coronavirus', 'Adenovirus'
            Immune cells: 'Neutrophil', 'Macrophage', 'TCell'
            Body cells: 'RedBloodCell', 'EpithelialCell', 'Platelet'
        x (float): Initial x position
        y (float): Initial y position
        environment: The simulation environment containing configuration
        
    Returns:
        Organism: An instance of the specified organism type
    """
    # Get configuration
    config = environment.config
    
    # Get type-specific config
    org_config = config["organism_types"].get(organism_type, {})
    
    # Set default values if config doesn't contain them
    size_range = org_config.get("size_range", [3, 8])
    speed_range = org_config.get("speed_range", [0.5, 2.0])
    
    # Generate random properties
    # Random size within range
    size = environment.random.uniform(size_range[0], size_range[1])
    
    # Random speed within range
    speed = environment.random.uniform(speed_range[0], speed_range[1])
    
    # Default color - we'll let each organism class handle its own coloring
    color = (200, 200, 200)
    
    # Debug print
    print(f"Creating {organism_type} at ({x:.1f}, {y:.1f}) with size={size:.1f}, speed={speed:.1f}")
    
    try:
        # Create organism based on type
        if organism_type == "EColi":
            return EColi(x, y, size, color, speed)
        elif organism_type == "Streptococcus":
            return Streptococcus(x, y, size, color, speed)
        elif organism_type == "BeneficialBacteria":
            return BeneficialBacteria(x, y, size, color, speed)
        elif organism_type == "Salmonella":
            return Salmonella(x, y, size, color, speed)
        elif organism_type == "Staphylococcus":
            return Staphylococcus(x, y, size, color, speed)
        elif organism_type == "Influenza":
            return Influenza(x, y, size, color, speed)
        elif organism_type == "Rhinovirus":
            return Rhinovirus(x, y, size, color, speed)
        elif organism_type == "Coronavirus":
            return Coronavirus(x, y, size, color, speed)
        elif organism_type == "Adenovirus":
            return Adenovirus(x, y, size, color, speed)
        elif organism_type == "Neutrophil":
            return Neutrophil(x, y, size, color, speed)
        elif organism_type == "Macrophage":
            return Macrophage(x, y, size, color, speed)
        elif organism_type == "TCell":
            return TCell(x, y, size, color, speed)
        # Add new body cell types
        elif organism_type == "RedBloodCell":
            return RedBloodCell(x, y, size, color, speed)
        elif organism_type == "EpithelialCell":
            return EpithelialCell(x, y, size, color, speed)
        elif organism_type == "Platelet":
            return Platelet(x, y, size, color, speed)
        else:
            # Fallback to generic types
            if "bacteria" in organism_type.lower():
                return Bacteria(x, y, size, color, speed)
            elif "virus" in organism_type.lower():
                return Virus(x, y, size, color, speed)
            elif "blood" in organism_type.lower() or "cell" in organism_type.lower():
                return Neutrophil(x, y, size, color, speed)
            else:
                print(f"Warning: Unknown organism type: {organism_type}, using generic Bacteria")
                return Bacteria(x, y, size, color, speed)
    except Exception as e:
        print(f"Error creating {organism_type}: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    return None 