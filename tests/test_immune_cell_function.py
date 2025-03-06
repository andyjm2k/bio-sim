"""
Tests for comprehensive immune cell targeting and behavior
Verifies that each immune cell (Neutrophil, Macrophage, TCell) 
targets the appropriate pathogens in the correct way.
"""

import unittest
import numpy as np
import random
import math
import pygame
from unittest.mock import MagicMock, patch
import sys
import os
from tabulate import tabulate  # For table formatting

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import all relevant organism classes
from src.organisms.bacteria import Bacteria, EColi, Streptococcus, BeneficialBacteria
from src.organisms.virus import Virus, Influenza, Rhinovirus, Coronavirus, Adenovirus 
from src.organisms.white_blood_cell import Neutrophil, Macrophage, TCell
from src.organisms.body_cells import BodyCell, RedBloodCell, EpithelialCell
from src.environment import Environment

# Mock environment class for testing
class MockEnvironment:
    """
    Mock environment with the specific attributes needed for testing
    """
    def __init__(self, config=None):
        self.config = config or {"simulation_settings": {"viral_burst_count": 4}}
        self.width = 800
        self.height = 600
        self.nutrients = 100
        self.ph_level = 7.0
        self.temperature = 37.0
        self.oxygen = 95.0
        self.flow_rate = 0.5
        self.random = random.Random(42)  # Fixed seed for reproducibility
        self.simulation = MagicMock()
        self.simulation.organisms = []
        
    def get_nearby_organisms(self, x, y, radius):
        return []
        
    def get_conditions_at(self, x, y):
        return {
            "pH": 7.0,
            "ph_level": 7.0,
            "temperature": 37.0,
            "oxygen": 95.0,
            "nutrients": 100,
            "flow_rate": 0.5
        }
    
    def consume_nutrients(self, x, y, amount):
        # Mock the consumption of nutrients
        consumed = min(amount, self.nutrients)
        self.nutrients -= consumed
        return consumed
    
    def get_organism_at(self, x, y, radius):
        # Mock getting an organism at the specified location
        return None
    
    def add_organism(self, organism):
        # Mock adding an organism to the environment
        if hasattr(self.simulation, 'organisms'):
            self.simulation.organisms.append(organism)
        return True

class TestImmuneTargeting(unittest.TestCase):
    """Comprehensive test for immune cells targeting behavior"""
    
    def setUp(self):
        """Set up test environment and organisms"""
        self.environment = MockEnvironment()
        
        # Create immune cells
        self.neutrophil = Neutrophil(100, 100, 10, (220, 220, 250), 1.0)
        self.macrophage = Macrophage(100, 100, 12, (150, 150, 220), 0.5)
        self.tcell = TCell(100, 100, 8, (100, 180, 255), 0.8)
        
        # Set necessary properties for testing
        self.macrophage.phagocytosis_radius = 20
        self.macrophage.engulfing_target = None
        self.macrophage.engulfing_progress = 0
        self.macrophage.engulfed_pathogens = []
        self.macrophage.digesting = False
        
        self.tcell.antibody_production_cooldown = 0
        self.tcell.energy = 100
        
        # Create pathogens (bacteria)
        self.ecoli = EColi(105, 105, 5, (200, 100, 100), 1.0)
        self.streptococcus = Streptococcus(105, 105, 5, (180, 100, 100), 1.0)
        self.beneficial_bacteria = BeneficialBacteria(105, 105, 5, (100, 180, 220), 1.0)
        
        # Create pathogens (viruses)
        self.influenza = Influenza(105, 105, 3, (255, 50, 50), 2.0)
        self.rhinovirus = Rhinovirus(105, 105, 3, (255, 150, 50), 2.0)
        self.coronavirus = Coronavirus(105, 105, 3, (180, 100, 180), 2.0)
        self.adenovirus = Adenovirus(105, 105, 3, (220, 100, 100), 2.0)
        
        # Create non-pathogens
        self.body_cell = BodyCell(105, 105, 8, (230, 180, 180), 0.2)
        self.red_blood_cell = RedBloodCell(105, 105, 7, (220, 40, 40), 1.0)
        self.epithelial_cell = EpithelialCell(105, 105, 9, (230, 180, 180), 0.3)
        
        # Create antibody-marked virus for testing
        self.marked_virus = Influenza(105, 105, 3, (255, 50, 50), 2.0)
        self.marked_virus.antibody_marked = True
        self.marked_virus.antibody_level = 0.5
        
        # All organisms for testing
        self.all_organisms = [
            self.ecoli, self.streptococcus, self.beneficial_bacteria,
            self.influenza, self.rhinovirus, self.coronavirus, self.adenovirus,
            self.body_cell, self.red_blood_cell, self.epithelial_cell,
            self.marked_virus
        ]
        
        # All immune cells
        self.immune_cells = [
            self.neutrophil,
            self.macrophage,
            self.tcell
        ]
    
    def test_immune_cell_targeting(self):
        """
        Comprehensive test of all immune cells against all pathogen types.
        Generates a report of which pathogens each immune cell targets.
        """
        # Test matrix: for each immune cell type, test interaction with each organism
        # Store results in a structured way
        results = []
        
        # Headers for the table
        results.append(["Organism", "Type", "Neutrophil", "Macrophage", "T-Cell"])
        
        # Test each organism against each immune cell
        for organism in self.all_organisms:
            row = []
            
            # Get organism name and type
            if hasattr(organism, 'get_name') and callable(getattr(organism, 'get_name')):
                org_name = organism.get_name()
            else:
                org_name = organism.__class__.__name__
                
            if hasattr(organism, 'get_type') and callable(getattr(organism, 'get_type')):
                org_type = organism.get_type()
            else:
                org_type = "unknown"
                
            row.append(org_name)
            row.append(org_type)
            
            # Test each immune cell
            for immune_cell in [self.neutrophil, self.macrophage, self.tcell]:
                # Reset immune cell state
                if hasattr(immune_cell, 'engulfing_target'):
                    immune_cell.engulfing_target = None
                
                # Test interaction
                result = immune_cell.interact(organism, self.environment)
                
                # For macrophage, also check if target was set
                if immune_cell == self.macrophage:
                    engulfing = immune_cell.engulfing_target is organism if immune_cell.engulfing_target else False
                    row.append(f"✅ {result}" if result and engulfing else f"❌ {result}")
                else:
                    # For other cells, just check the result
                    row.append(f"✅ {result}" if result else f"❌ {result}")
            
            results.append(row)
        
        # Print the table
        print("\n=== IMMUNE CELL TARGETING REPORT ===")
        print(tabulate(results, headers="firstrow", tablefmt="grid"))
        print()
        
        # Print summary of targeting behaviors
        print("=== TARGETING BEHAVIOR SUMMARY ===")
        
        # Check Neutrophil behavior
        print("Neutrophil:")
        print("- Should target bacteria (except beneficial): " + 
              ("✅ Working" if self.neutrophil.interact(self.ecoli, self.environment) else "❌ Not Working"))
        print("- Should target viruses: " + 
              ("✅ Working" if self.neutrophil.interact(self.influenza, self.environment) else "❌ Not Working"))
        print("- Should ignore beneficial bacteria: " + 
              ("✅ Working" if not self.neutrophil.interact(self.beneficial_bacteria, self.environment) else "❌ Not Working"))
        print("- Should ignore body cells: " + 
              ("✅ Working" if not self.neutrophil.interact(self.body_cell, self.environment) else "❌ Not Working"))
        
        # Check Macrophage behavior
        print("\nMacrophage:")
        
        # Reset state
        self.macrophage.engulfing_target = None
        ecoli_result = self.macrophage.interact(self.ecoli, self.environment)
        ecoli_engulfing = self.macrophage.engulfing_target is self.ecoli if self.macrophage.engulfing_target else False
        
        # Reset state
        self.macrophage.engulfing_target = None
        influenza_result = self.macrophage.interact(self.influenza, self.environment)
        influenza_engulfing = self.macrophage.engulfing_target is self.influenza if self.macrophage.engulfing_target else False
        
        # Reset state
        self.macrophage.engulfing_target = None
        corona_result = self.macrophage.interact(self.coronavirus, self.environment)
        corona_engulfing = self.macrophage.engulfing_target is self.coronavirus if self.macrophage.engulfing_target else False
        
        # Reset state
        self.macrophage.engulfing_target = None
        beneficial_result = self.macrophage.interact(self.beneficial_bacteria, self.environment)
        
        # Reset state
        self.macrophage.engulfing_target = None
        body_result = self.macrophage.interact(self.body_cell, self.environment)
        
        print("- Should engulf bacteria: " + 
              ("✅ Working" if ecoli_result and ecoli_engulfing else "❌ Not Working"))
        print("- Should engulf viruses: " + 
              ("✅ Working" if influenza_result and influenza_engulfing else "❌ Not Working"))
        print("- Should engulf coronavirus: " + 
              ("✅ Working" if corona_result and corona_engulfing else "❌ Not Working"))
        print("- Should ignore beneficial bacteria: " + 
              ("✅ Working" if not beneficial_result else "❌ Not Working"))
        print("- Should ignore body cells: " + 
              ("✅ Working" if not body_result else "❌ Not Working"))
        
        # Check T-Cell behavior  
        print("\nT-Cell:")
        print("- Should target viruses: " + 
              ("✅ Working" if self.tcell.interact(self.influenza, self.environment) else "❌ Not Working"))
        
        # Create a mock Staphylococcus for testing specific bacteria targeting
        staph = MagicMock()
        staph.get_type = MagicMock(return_value="bacteria")
        staph.get_name = MagicMock(return_value="Staphylococcus")
        staph.x, staph.y = 105, 105
        staph.size = 5
        staph.health = 1.0
        staph.is_alive = True
        
        print("- Should target specific bacteria (Staphylococcus): " + 
              ("✅ Working" if self.tcell.interact(staph, self.environment) else "❌ Not Working"))
        print("- Should ignore regular bacteria: " + 
              ("✅ Working" if not self.tcell.interact(self.ecoli, self.environment) else "❌ Not Working"))
        print("- Should ignore beneficial bacteria: " + 
              ("✅ Working" if not self.tcell.interact(self.beneficial_bacteria, self.environment) else "❌ Not Working"))
        print("- Should ignore body cells: " + 
              ("✅ Working" if not self.tcell.interact(self.body_cell, self.environment) else "❌ Not Working"))
        
        # Print conclusion for Coronavirus targeting
        print("\n=== CORONAVIRUS TARGETING CONCLUSION ===")
        
        # Reset state for a clear test
        self.macrophage.engulfing_target = None
        corona_result = self.macrophage.interact(self.coronavirus, self.environment)
        corona_engulfing = self.macrophage.engulfing_target is self.coronavirus if self.macrophage.engulfing_target else False
        
        if corona_result and corona_engulfing:
            print("✅ Macrophages DO successfully target and engulf Coronavirus pathogens.")
            print("   The observed issue might be related to simulation conditions or specific circumstances.")
            print("   Possible reasons for observed behavior:")
            print("   1. Pathogens might be too far away (outside phagocytosis_radius)")
            print("   2. Macrophages might be at max_engulf_capacity")
            print("   3. Macrophages might already be engulfing other targets")
            print("   4. There might be other conditions affecting the interaction")
        else:
            print("❌ Macrophages currently DO NOT target Coronavirus pathogens.")
            print("   This is likely a defect in the implementation.")
            print("   Recommended fix: Ensure 'Coronavirus' is properly detected in the Macrophage.interact method")
        
        print("\nImportant: This test was run in a controlled environment with pathogens positioned")
        print("close to immune cells. In the actual simulation, targeting behavior might vary based")
        print("on random movements, distances, and other dynamic factors.")

if __name__ == "__main__":
    unittest.main() 