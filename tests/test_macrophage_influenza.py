"""
Specific test for Macrophage targeting Influenza.
Focuses on detailed debugging of the interaction mechanics.
"""

import unittest
import sys
import os
import random
from unittest.mock import MagicMock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.organisms.white_blood_cell import Macrophage
from src.organisms.virus import Influenza

class MockEnvironment:
    """Simple mock environment for testing"""
    def __init__(self):
        self.width = 800
        self.height = 600
        self.nutrients = 100
        self.oxygen = 95
        self.temperature = 37.0
        self.ph_level = 7.0
        self.flow_rate = 0.5
        self.simulation = MagicMock()
        self.simulation.organisms = []
    
    def get_conditions_at(self, x, y):
        return {
            "pH": self.ph_level,
            "temperature": self.temperature,
            "nutrients": self.nutrients,
            "oxygen": self.oxygen,
            "flow_rate": self.flow_rate
        }
    
    def get_nearby_organisms(self, x, y, radius):
        return []

class TestMacrophageInfluenzaInteraction(unittest.TestCase):
    """Direct test of Macrophage-Influenza interaction"""
    
    def test_interaction_mechanics(self):
        """Test the mechanics of Macrophage-Influenza interaction step by step"""
        # Create environment
        env = MockEnvironment()
        
        # Create macrophage and influenza
        macrophage = Macrophage(100, 100, 12, (150, 150, 220), 0.5)
        influenza = Influenza(105, 105, 3, (255, 50, 50), 2.0)
        
        # Set up macrophage for testing
        macrophage.engulfed_pathogens = []
        macrophage.max_engulf_capacity = 5
        macrophage.engulfing_target = None
        macrophage.phagocytosis_radius = 20
        
        # Define the original method to avoid patching issues
        original_random = random.random
        
        # Debug step 1: Check if Influenza is in the potential targets
        print("\nStep 1: Check Macrophage targeting lists")
        print(f"Potential targets: {macrophage.potential_targets}")
        print(f"Is 'Influenza' in potential_targets: {'Influenza' in macrophage.potential_targets}")
        print(f"Excluded targets: {macrophage.excluded_targets}")
        print(f"Is 'Influenza' in excluded_targets: {'Influenza' in macrophage.excluded_targets}")
        
        # Debug step 2: Verify Influenza type and name
        print("\nStep 2: Verify Influenza properties")
        print(f"Influenza type: {influenza.get_type()}")
        print(f"Influenza name: {influenza.get_name()}")
        print(f"Influenza health: {influenza.health}")
        
        # Debug step 3: Check distance calculation
        dx = influenza.x - macrophage.x
        dy = influenza.y - macrophage.y
        distance = (dx**2 + dy**2)**0.5
        print("\nStep 3: Check distance")
        print(f"Influenza position: ({influenza.x}, {influenza.y})")
        print(f"Macrophage position: ({macrophage.x}, {macrophage.y})")
        print(f"Distance between them: {distance}")
        print(f"Macrophage phagocytosis_radius: {macrophage.phagocytosis_radius}")
        print(f"Is within range: {distance <= macrophage.phagocytosis_radius}")
        
        # Debug step 4: Check targeting logic - using direct logic from interact method
        print("\nStep 4: Check targeting logic")
        org_type = influenza.get_type()
        org_name = influenza.get_name()
        
        # Check exempt types
        exempt_types = [
            "neutrophil", "macrophage", "tcell", "t_cell", "t-cell", 
            "blood_cell", "red_blood_cell", "redbloodcell", "whitebloodcell",
            "white_blood_cell", "platelet", "epithelialcell", "epithelial_cell",
            "beneficialbacteria", "beneficial_bacteria"
        ]
        
        is_exempt_by_type = org_type.lower() in exempt_types
        is_exempt_by_name = org_name.lower() in exempt_types
        
        print(f"Is exempt by type: {is_exempt_by_type}")
        print(f"Is exempt by name: {is_exempt_by_name}")
        
        # Check if this is a pathogen that should be targeted
        is_target = False
        if ("virus" in org_type.lower() or 
            "bacteria" in org_type.lower() and "beneficial" not in org_type.lower() or
            "damaged" in org_type.lower() or
            "dead" in org_type.lower()):
            is_target = True
            
        # Also check the name
        if org_name and ("virus" in org_name.lower() or 
                        ("bacteria" in org_name.lower() and "beneficial" not in org_name.lower()) or
                        "damaged" in org_name.lower() or
                        "dead" in org_name.lower()):
            is_target = True
            
        print(f"Is target by logic: {is_target}")
        
        # Debug step 5: Manually calculate engulf_chance
        print("\nStep 5: Calculate engulf chance")
        engulf_chance = 0.4  # Base chance for live pathogens
        
        # Modify for different target types
        if hasattr(influenza, 'antibody_marked') and influenza.antibody_marked:
            engulf_chance = 0.8  # Better chance for marked viruses
            print("Using marked virus chance: 0.8")
        elif "virus" in org_type.lower():
            engulf_chance = 0.25  # Harder to engulf unmarked viruses
            print("Using normal virus chance: 0.25")
        elif "bacteria" in org_type.lower() and "beneficial" not in org_type.lower():
            engulf_chance = 0.5  # Easier to engulf harmful bacteria
            print("Using bacteria chance: 0.5")
        elif "damaged" in org_type.lower() or "dead" in org_type.lower():
            engulf_chance = 0.7  # Easy to clean up damaged/dead cells
            print("Using damaged/dead cell chance: 0.7")
        else:
            print("Using default chance: 0.4")
        
        print(f"Final engulf_chance: {engulf_chance}")
        
        # Debug step 6: Test with natural random value
        print("\nStep 6: Test with natural random (no forcing)")
        # Record initial health
        initial_health_natural = influenza.health
        
        # Try the interaction with natural randomness
        random.random = original_random
        interaction_result_natural = macrophage.interact(influenza, env)
        
        print(f"Natural interaction result: {interaction_result_natural}")
        print(f"Engulfing target after natural interaction: {macrophage.engulfing_target}")
        print(f"Influenza health after natural interaction: {influenza.health}")
        
        # Reset for next test
        macrophage.engulfing_target = None
        influenza.health = initial_health_natural  # Restore health
        
        # Debug step 7: Test with forced successful random value
        print("\nStep 7: Force successful engulfing with random=0.1")
        # Force random to return a low value (ensuring engulfing)
        random.random = lambda: 0.1
        
        # Try the interaction with forced randomness
        interaction_result_forced = macrophage.interact(influenza, env)
        
        print(f"Forced interaction result: {interaction_result_forced}")
        print(f"Engulfing target after forced interaction: {macrophage.engulfing_target}")
        print(f"Is engulfing target the influenza: {macrophage.engulfing_target is influenza}")
        print(f"Influenza health after forced interaction: {influenza.health}")
        
        # Reset random
        random.random = original_random
        
        # Final assertions - test with forced random value
        self.assertTrue(interaction_result_forced, "The interaction should succeed with forced random value")
        self.assertEqual(macrophage.engulfing_target, influenza, 
                       "Macrophage should be engulfing the influenza with forced random value")
        self.assertLess(influenza.health, initial_health_natural, 
                       "Influenza health should be reduced after forced interaction")
        
        # Additional test: Create a marked influenza to test antibody-marked behavior
        print("\nStep 8: Test with antibody-marked influenza")
        
        # Create a new marked influenza
        marked_influenza = Influenza(105, 105, 3, (255, 50, 50), 2.0)
        marked_influenza.antibody_marked = True
        marked_influenza.antibody_level = 0.5
        
        # Record initial health
        initial_health_marked = marked_influenza.health
        
        # Reset macrophage state
        macrophage.engulfing_target = None
        
        # Try interaction with natural randomness on marked influenza
        random.random = original_random
        interaction_result_marked = macrophage.interact(marked_influenza, env)
        
        print(f"Marked influenza interaction result: {interaction_result_marked}")
        print(f"Engulfing target after marked interaction: {macrophage.engulfing_target}")
        print(f"Is engulfing marked influenza: {macrophage.engulfing_target is marked_influenza}")
        print(f"Marked influenza health after interaction: {marked_influenza.health}")
        
        # Note: This test might sometimes fail due to randomness, but antibody-marked viruses 
        # have a much higher chance (0.8) of being engulfed

if __name__ == "__main__":
    unittest.main() 