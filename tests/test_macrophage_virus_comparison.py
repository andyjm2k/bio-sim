"""
Comparison test for Macrophage targeting of different virus types.
Directly compares Macrophage interaction with Influenza and Coronavirus.
"""

import unittest
import sys
import os
import random
import copy
from unittest.mock import MagicMock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.organisms.white_blood_cell import Macrophage
from src.organisms.virus import Influenza, Coronavirus

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

class TestMacrophageVirusComparison(unittest.TestCase):
    """Direct comparison of Macrophage interaction with different virus types"""
    
    def setUp(self):
        """Set up test environment and organisms"""
        self.env = MockEnvironment()
        
        # Store original random function
        self.original_random = random.random
        
        # Create a macrophage
        self.macrophage = Macrophage(100, 100, 12, (150, 150, 220), 0.5)
        self.macrophage.engulfed_pathogens = []
        self.macrophage.max_engulf_capacity = 5
        self.macrophage.engulfing_target = None
        self.macrophage.phagocytosis_radius = 20
        
        # Create viruses
        self.influenza = Influenza(105, 105, 3, (255, 50, 50), 2.0)
        self.coronavirus = Coronavirus(105, 105, 3, (180, 100, 180), 2.0)
        
        # We'll use these backup copies for restoring state between tests
        self.original_macrophage = copy.deepcopy(self.macrophage)
        self.original_influenza = copy.deepcopy(self.influenza)
        self.original_coronavirus = copy.deepcopy(self.coronavirus)
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore original random function
        random.random = self.original_random
    
    def test_virus_property_comparison(self):
        """Compare basic properties of different virus types"""
        print("\n=== VIRUS PROPERTY COMPARISON ===")
        
        # Compare type and name
        print(f"Influenza type: {self.influenza.get_type()}")
        print(f"Coronavirus type: {self.coronavirus.get_type()}")
        print(f"Influenza name: {self.influenza.get_name()}")
        print(f"Coronavirus name: {self.coronavirus.get_name()}")
        
        # Check if in targeting lists
        print(f"\nInfluenza in potential_targets: {'Influenza' in self.macrophage.potential_targets}")
        print(f"Coronavirus in potential_targets: {'Coronavirus' in self.macrophage.potential_targets}")
        print(f"Generic 'Virus' in potential_targets: {'Virus' in self.macrophage.potential_targets}")
        
        # Check if in excluded lists
        print(f"\nInfluenza in excluded_targets: {'Influenza' in self.macrophage.excluded_targets}")
        print(f"Coronavirus in excluded_targets: {'Coronavirus' in self.macrophage.excluded_targets}")
        
        # Compare targeting logic
        inf_type_match = "virus" in self.influenza.get_type().lower()
        corona_type_match = "virus" in self.coronavirus.get_type().lower()
        inf_name_match = "virus" in self.influenza.get_name().lower()
        corona_name_match = "virus" in self.coronavirus.get_name().lower()
        
        print(f"\nInfluenza type contains 'virus': {inf_type_match}")
        print(f"Coronavirus type contains 'virus': {corona_type_match}")
        print(f"Influenza name contains 'virus': {inf_name_match}")
        print(f"Coronavirus name contains 'virus': {corona_name_match}")
        
        # Should be the same for both
        self.assertEqual(self.influenza.get_type(), self.coronavirus.get_type(), 
                         "Both should return the same type")
        
        # They should both be in potential_targets
        self.assertIn('Influenza', self.macrophage.potential_targets)
        self.assertIn('Coronavirus', self.macrophage.potential_targets)
    
    def test_interaction_with_forced_random(self):
        """Compare interactions with forced random value"""
        print("\n=== INTERACTION WITH FORCED RANDOM ===")
        
        # Force random to always return 0.1 (below the engulf chance)
        random.random = lambda: 0.1
        
        # Test Influenza interaction
        print("\nTesting Influenza interaction...")
        influenza_result = self.macrophage.interact(self.influenza, self.env)
        print(f"Interaction result: {influenza_result}")
        print(f"Engulfing target: {self.macrophage.engulfing_target}")
        print(f"Is target Influenza: {self.macrophage.engulfing_target is self.influenza}")
        
        # Reset macrophage state
        self.macrophage = copy.deepcopy(self.original_macrophage)
        
        # Test Coronavirus interaction
        print("\nTesting Coronavirus interaction...")
        coronavirus_result = self.macrophage.interact(self.coronavirus, self.env)
        print(f"Interaction result: {coronavirus_result}")
        print(f"Engulfing target: {self.macrophage.engulfing_target}")
        print(f"Is target Coronavirus: {self.macrophage.engulfing_target is self.coronavirus}")
        
        # Compare results
        print(f"\nSame interaction result: {influenza_result == coronavirus_result}")
        
        # Reset for next test
        self.macrophage = copy.deepcopy(self.original_macrophage)
    
    def test_debug_interact_method(self):
        """Debug the interaction method with both virus types"""
        print("\n=== DEBUGGING INTERACT METHOD ===")
        
        # Let's manually trace through the interact method for both viruses
        # Follow the same logic as in the Macrophage.interact method
        
        print("\n--- Influenza Debugging ---")
        self._debug_interaction(self.influenza)
        
        print("\n--- Coronavirus Debugging ---")
        self._debug_interaction(self.coronavirus)
    
    def _debug_interaction(self, organism):
        """Trace through the interaction logic step by step"""
        # Skip if already engulfing something
        if self.macrophage.engulfing_target:
            print("Already engulfing something - skipping")
            return
            
        # Skip if already at capacity
        if len(self.macrophage.engulfed_pathogens) >= self.macrophage.max_engulf_capacity:
            print("At capacity - skipping")
            return
        
        # Get organism type information
        org_type = None
        org_name = None
        
        # Extract type information using available methods/attributes
        if hasattr(organism, 'type'):
            org_type = organism.type
            print(f"Using organism.type: {org_type}")
        elif hasattr(organism, 'get_type') and callable(getattr(organism, 'get_type')):
            org_type = organism.get_type()
            print(f"Using organism.get_type(): {org_type}")
        else:
            print("Cannot determine type - skipping")
            return
            
        # Get name if available
        if hasattr(organism, 'get_name') and callable(getattr(organism, 'get_name')):
            org_name = organism.get_name()
            print(f"Using organism.get_name(): {org_name}")
            
        # Skip non-target organisms
        is_target = False
        
        # List of organism types that should be skipped
        exempt_types = [
            "neutrophil", "macrophage", "tcell", "t_cell", "t-cell", 
            "blood_cell", "red_blood_cell", "redbloodcell", "whitebloodcell",
            "white_blood_cell", "platelet", "epithelialcell", "epithelial_cell",
            "beneficialbacteria", "beneficial_bacteria"
        ]
        
        # Skip friendly or immune cells
        if org_type.lower() in exempt_types:
            print(f"Type {org_type} is in exempt_types - skipping")
            return
            
        if org_name and org_name.lower() in exempt_types:
            print(f"Name {org_name} is in exempt_types - skipping")
            return
        
        # Check if this is a pathogen or damaged cell we should target
        if ("virus" in org_type.lower()):
            is_target = True
            print(f"'virus' found in type {org_type} - is_target=True")
        elif ("bacteria" in org_type.lower() and "beneficial" not in org_type.lower()):
            is_target = True
            print(f"'bacteria' found in type {org_type} without 'beneficial' - is_target=True")
        elif ("damaged" in org_type.lower()):
            is_target = True
            print(f"'damaged' found in type {org_type} - is_target=True")
        elif ("dead" in org_type.lower()):
            is_target = True
            print(f"'dead' found in type {org_type} - is_target=True")
        else:
            print(f"Type {org_type} doesn't match targeting criteria")
            
        # Also check the name
        if org_name and ("virus" in org_name.lower()):
            is_target = True
            print(f"'virus' found in name {org_name} - is_target=True")
        elif org_name and ("bacteria" in org_name.lower() and "beneficial" not in org_name.lower()):
            is_target = True
            print(f"'bacteria' found in name {org_name} without 'beneficial' - is_target=True")
        elif org_name and ("damaged" in org_name.lower()):
            is_target = True
            print(f"'damaged' found in name {org_name} - is_target=True")
        elif org_name and ("dead" in org_name.lower()):
            is_target = True
            print(f"'dead' found in name {org_name} - is_target=True")
        else:
            print(f"Name {org_name} doesn't match targeting criteria")
            
        # If not a valid target, skip
        if not is_target:
            print("Not a valid target - skipping")
            return
        else:
            print("Is a valid target - continuing")
            
        # Calculate distance
        dx = organism.x - self.macrophage.x
        dy = organism.y - self.macrophage.y
        distance = (dx**2 + dy**2)**0.5
        print(f"Distance: {distance}")
        print(f"Phagocytosis radius: {self.macrophage.phagocytosis_radius}")
        
        # Check if within engulfing range
        if distance <= self.macrophage.phagocytosis_radius:
            print("Within phagocytosis radius - continuing")
            # Higher success rate for antibody-marked viruses
            engulf_chance = 0.4  # Base chance for live pathogens
            
            # Modify for different target types
            if hasattr(organism, 'antibody_marked') and organism.antibody_marked:
                engulf_chance = 0.8  # Better chance for marked viruses
                print(f"Using marked virus chance: {engulf_chance}")
            elif "virus" in org_type.lower():
                engulf_chance = 0.25  # Harder to engulf unmarked viruses
                print(f"Using normal virus chance: {engulf_chance}")
            elif "bacteria" in org_type.lower() and "beneficial" not in org_type.lower():
                engulf_chance = 0.5  # Easier to engulf harmful bacteria
                print(f"Using bacteria chance: {engulf_chance}")
            elif "damaged" in org_type.lower() or "dead" in org_type.lower():
                engulf_chance = 0.7  # Easy to clean up damaged/dead cells
                print(f"Using damaged/dead cell chance: {engulf_chance}")
            
            # Try to engulf
            random_value = 0.1  # Force for testing
            print(f"Forcing random value: {random_value}")
            print(f"Engulf chance: {engulf_chance}")
            if random_value < engulf_chance:
                print("Random value < engulf_chance - SUCCESS")
                # Start engulfing process
                print("Would set engulfing_target to the organism")
                return True
            else:
                print("Random value >= engulf_chance - FAILURE")
        else:
            print("Outside phagocytosis radius - skipping")
        
        print("Interaction failed")
        return False
        
    def test_class_differences(self):
        """Compare class differences that might affect interaction"""
        print("\n=== CLASS DIFFERENCES ===")
        
        # Check classes and inheritance
        print(f"Influenza class: {self.influenza.__class__.__name__}")
        print(f"Coronavirus class: {self.coronavirus.__class__.__name__}")
        print(f"Influenza base classes: {self.influenza.__class__.__bases__}")
        print(f"Coronavirus base classes: {self.coronavirus.__class__.__bases__}")
        
        # Check key attributes
        print("\nKey attributes:")
        print(f"Influenza has 'type': {hasattr(self.influenza, 'type')}")
        print(f"Coronavirus has 'type': {hasattr(self.coronavirus, 'type')}")
        
        if hasattr(self.influenza, 'type') and hasattr(self.coronavirus, 'type'):
            print(f"Influenza.type: {self.influenza.type}")
            print(f"Coronavirus.type: {self.coronavirus.type}")
        
        # Check special attributes
        inf_attrs = set(dir(self.influenza))
        corona_attrs = set(dir(self.coronavirus))
        diff_attrs = (inf_attrs - corona_attrs).union(corona_attrs - inf_attrs)
        
        if diff_attrs:
            print("\nDifferent attributes:")
            for attr in sorted(diff_attrs):
                if attr.startswith('__'):
                    continue  # Skip built-in attributes
                
                inf_has = hasattr(self.influenza, attr)
                corona_has = hasattr(self.coronavirus, attr)
                
                if inf_has and not corona_has:
                    print(f"Only Influenza has: {attr}")
                elif corona_has and not inf_has:
                    print(f"Only Coronavirus has: {attr}")
        else:
            print("\nNo attribute differences found")
    
    def test_direct_internal_state(self):
        """Directly compare internal state of both viruses"""
        print("\n=== INTERNAL STATE COMPARISON ===")
        
        # Create fresh copies
        influenza = Influenza(105, 105, 3, (255, 50, 50), 2.0)
        coronavirus = Coronavirus(105, 105, 3, (180, 100, 180), 2.0)
        
        # Check specific attributes that might affect interaction
        print("\nVirus-specific traits:")
        print(f"Influenza health: {influenza.health}")
        print(f"Coronavirus health: {coronavirus.health}")
        
        print(f"\nInfluenza structure: {influenza.structure if hasattr(influenza, 'structure') else 'N/A'}")
        print(f"Coronavirus structure: {coronavirus.structure if hasattr(coronavirus, 'structure') else 'N/A'}")
        
        # Check antibody marking
        print(f"\nInfluenza antibody_marked: {influenza.antibody_marked if hasattr(influenza, 'antibody_marked') else 'N/A'}")
        print(f"Coronavirus antibody_marked: {coronavirus.antibody_marked if hasattr(coronavirus, 'antibody_marked') else 'N/A'}")
        
    def test_macrophage_debugging(self):
        """Debug the Macrophage class setup"""
        print("\n=== MACROPHAGE DEBUGGING ===")
        
        # Check macrophage's key attributes
        print(f"Macrophage class: {self.macrophage.__class__.__name__}")
        print(f"Macrophage base classes: {self.macrophage.__class__.__bases__}")
        
        # Check for the interact method
        has_interact = hasattr(self.macrophage, 'interact')
        print(f"Has interact method: {has_interact}")
        
        if has_interact:
            # Get the actual method
            interact_method = getattr(self.macrophage, 'interact')
            
            # Check where it's defined (class vs inherited)
            method_class = interact_method.__self__.__class__ if hasattr(interact_method, '__self__') else None
            print(f"Method defined in class: {method_class}")
            
            # Print method signature if available
            from inspect import signature, getdoc
            if hasattr(interact_method, '__func__'):
                sig = signature(interact_method.__func__)
                print(f"Method signature: interact{sig}")
                doc = getdoc(interact_method.__func__)
                if doc:
                    print(f"Method docstring: {doc.split(chr(10))[0]}")
            
        # Check inheritance chain for the interact method
        print("\nMethod resolution order:")
        for cls in self.macrophage.__class__.__mro__:
            has_method = 'interact' in cls.__dict__
            print(f"{cls.__name__}: {'Has interact method' if has_method else 'Does not have interact method'}")
    
    def test_interaction_with_modified_macrophage(self):
        """Test interactions with a modified Macrophage"""
        print("\n=== TEST WITH MODIFIED MACROPHAGE ===")
        
        # Create a new macrophage
        modified_macrophage = Macrophage(100, 100, 12, (150, 150, 220), 0.5)
        modified_macrophage.engulfed_pathogens = []
        modified_macrophage.max_engulf_capacity = 5
        modified_macrophage.engulfing_target = None
        modified_macrophage.phagocytosis_radius = 20
        
        # Add both virus types to explicit potential targets
        if not hasattr(modified_macrophage, 'potential_targets'):
            modified_macrophage.potential_targets = []
        
        if 'Influenza' not in modified_macrophage.potential_targets:
            modified_macrophage.potential_targets.append('Influenza')
        
        if 'Coronavirus' not in modified_macrophage.potential_targets:
            modified_macrophage.potential_targets.append('Coronavirus')
            
        # Ensure 'Virus' is also in the targets
        if 'Virus' not in modified_macrophage.potential_targets:
            modified_macrophage.potential_targets.append('Virus')
        
        print(f"Modified potential_targets: {modified_macrophage.potential_targets}")
        
        # Force random to always return 0.1 (below the engulf chance)
        random.random = lambda: 0.1
        
        # Test Influenza interaction
        print("\nTesting Influenza interaction with modified Macrophage...")
        influenza_result = modified_macrophage.interact(self.influenza, self.env)
        print(f"Interaction result: {influenza_result}")
        print(f"Engulfing target: {modified_macrophage.engulfing_target}")
        print(f"Is target Influenza: {modified_macrophage.engulfing_target is self.influenza}")
        
        # Reset macrophage state
        modified_macrophage.engulfing_target = None
        
        # Test Coronavirus interaction
        print("\nTesting Coronavirus interaction with modified Macrophage...")
        coronavirus_result = modified_macrophage.interact(self.coronavirus, self.env)
        print(f"Interaction result: {coronavirus_result}")
        print(f"Engulfing target: {modified_macrophage.engulfing_target}")
        print(f"Is target Coronavirus: {modified_macrophage.engulfing_target is self.coronavirus}")

if __name__ == "__main__":
    unittest.main() 