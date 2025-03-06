import json
import sys
from src.simulation import BioSimulation
from src.organisms import create_organism
from src.environment import Environment

def debug_organisms_creation():
    """Debug script to analyze organism creation"""
    print("Loading config...")
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    print("Creating simulation...")
    sim = BioSimulation(config)
    
    # Manually initialize to ensure organisms are created
    sim.initialize_simulation()
    
    # Count organism types
    organism_counts = {}
    for org in sim.organisms:
        org_type = type(org).__name__
        if org_type not in organism_counts:
            organism_counts[org_type] = 0
        organism_counts[org_type] += 1
    
    print("\nOrganism counts in simulation:")
    print("-" * 40)
    for org_type, count in organism_counts.items():
        print(f"{org_type}: {count}")
    
    print("\nConfig organism counts:")
    print("-" * 40)
    for org_type, org_config in config.get("organism_types", {}).items():
        print(f"{org_type}: {org_config.get('count', 0)}")
    
    # Check for mismatches
    print("\nChecking for mismatches...")
    print("-" * 40)
    for org_type, org_config in config.get("organism_types", {}).items():
        config_count = org_config.get("count", 0)
        actual_count = organism_counts.get(org_type, 0)
        
        if config_count != actual_count:
            print(f"Mismatch for {org_type}: Config={config_count}, Actual={actual_count}")
    
    return 0

if __name__ == "__main__":
    sys.exit(debug_organisms_creation()) 