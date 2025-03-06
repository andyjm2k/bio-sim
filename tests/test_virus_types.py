"""
Test file for virus-related functionality, specifically focused on Coronavirus and Adenovirus
and the updated viral burst conditions.
"""

import unittest
import math
import pygame
import random
from unittest.mock import MagicMock, patch

from src.organisms.virus import Virus, Coronavirus, Adenovirus
from src.organisms.body_cells import BodyCell
from src.environment import Environment

class MockEnvironment:
    """
    Mock environment with the specific attributes needed for testing
    """
    def __init__(self, config=None):
        self.config = config or {"simulation_settings": {"viral_burst_count": 4}}
        self.width = 800
        self.height = 600
        self.nutrients = 100
        self.flow_rate = 0.5
        self.random = random.Random(42)  # Fixed seed for reproducibility
        self.simulation = MagicMock()
        self.simulation.organisms = []
        
    def get_nearby_organisms(self, x, y, radius):
        return []
        
    def get_conditions_at(self, x, y):
        """Mock method to return environmental conditions at coordinates"""
        return {
            "temperature": 37.0,
            "ph_level": 7.0,
            "nutrients": 100,
            "flow_rate": 0.5
        }

class TestViralBurstConditions(unittest.TestCase):
    """Test the updated viral burst conditions"""
    
    def setUp(self):
        # Create a mock environment
        self.env = MockEnvironment()
        
        # Create a virus and a host cell
        self.virus = Virus(100, 100, 3, (255, 50, 50), 2.0)
        self.cell = BodyCell(100, 100, 8, (230, 180, 180), 0.2)
        
        # Add get_name method to Virus for testing
        self.virus.get_name = MagicMock(return_value="Virus")
    
    def test_viral_burst_conditions(self):
        """Test that viral burst happens with the new lenient conditions"""
        # Infect the host
        self.virus.host = self.cell
        self.virus.dormant_counter = 11  # Just above the minimum threshold (10)
        self.virus.energy = 45  # Above the minimum energy threshold (40)
        
        # Mock host death with appropriate negative health
        self.cell.health = -11  # Below the threshold (-10)
        self.cell.is_alive = False
        
        # Mock necessary methods to avoid test failures
        self.virus._apply_decision = MagicMock()
        self.virus._get_neural_inputs = MagicMock(return_value=[0.5, 0.5, 0.5])
        self.virus._apply_dna_effects = MagicMock()
        self.virus._apply_environmental_effects = MagicMock()
        
        # Update virus to trigger burst check
        self.virus.update(self.env)
        
        # Print debug info
        print(f"Virus energy: {self.virus.energy}")
        print(f"Organisms created: {len(self.env.simulation.organisms)}")
        print(f"Replication cooldown: {self.virus.replication_cooldown}")
        
        # Should have created new viruses based on viral_burst_count (4)
        self.assertEqual(len(self.env.simulation.organisms), 4)
        
        # Virus should have used energy
        self.assertLess(self.virus.energy, 45)
        
        # Virus should have a replication cooldown
        self.assertEqual(self.virus.replication_cooldown, 39)
        
        # Host reference should be cleared
        self.assertIsNone(self.virus.host)
    
    def test_config_viral_burst_count(self):
        """Test that the viral burst count from config is used"""
        # Set custom viral burst count
        self.env.config["simulation_settings"]["viral_burst_count"] = 3
        
        # Infect the host
        self.virus.host = self.cell
        self.virus.dormant_counter = 11
        self.virus.energy = 45
        
        # Mock host death with appropriate negative health
        self.cell.health = -11
        self.cell.is_alive = False
        
        # Mock necessary methods to avoid test failures
        self.virus._apply_decision = MagicMock()
        self.virus._get_neural_inputs = MagicMock(return_value=[0.5, 0.5, 0.5])
        self.virus._apply_dna_effects = MagicMock()
        self.virus._apply_environmental_effects = MagicMock()
        
        # Update virus to trigger burst
        self.virus.update(self.env)
        
        # Print debug info
        print(f"Virus energy: {self.virus.energy}")
        print(f"Organisms created: {len(self.env.simulation.organisms)}")
        
        # Should have created exactly 3 viruses based on config
        self.assertEqual(len(self.env.simulation.organisms), 3)

class TestCoronavirus(unittest.TestCase):
    """Test Coronavirus functionality"""
    
    def setUp(self):
        self.env = MockEnvironment()
        self.coronavirus = Coronavirus(100, 100, 3, (180, 100, 180), 2.0)
        # Create a host cell for the virus tests
        self.host_cell = BodyCell(100, 100, 8, (230, 180, 180), 0.2)
        
    def test_initialization(self):
        """Test Coronavirus initialization"""
        self.assertEqual(self.coronavirus.get_name(), "Coronavirus")
        self.assertEqual(self.coronavirus.color, (180, 100, 180))
        self.assertTrue(self.coronavirus.structure["has_spikes"])
    
    def test_reproduce(self):
        """Test Coronavirus reproduction with viral burst count"""
        # Set energy for reproduction
        self.coronavirus.energy = 100
        self.coronavirus.replication_cooldown = 0
        
        # Set host for the virus
        self.coronavirus.host = self.host_cell
        self.coronavirus.host.is_alive = True
        
        # Call reproduce
        children = self.coronavirus.reproduce(self.env)
        
        # Should have created viruses based on viral_burst_count (4)
        self.assertEqual(len(children), 4)
        self.assertEqual(len(self.env.simulation.organisms), 4)
        
        # Verify children are coronavirus
        for child in children:
            self.assertEqual(child.get_name(), "Coronavirus")
        
        # Check energy consumption
        self.assertLess(self.coronavirus.energy, 100)
        
        # Check cooldown
        self.assertEqual(self.coronavirus.replication_cooldown, 35)
    
    @patch('pygame.draw')
    def test_render(self, mock_draw):
        """Test coronavirus rendering with its crown of spikes"""
        # Mock screen
        screen = MagicMock()
        screen.get_width.return_value = 800
        screen.get_height.return_value = 600
        
        # Mock pygame.time.get_ticks for pulsating effect
        pygame.time.get_ticks = MagicMock(return_value=0)
        
        # Call render
        self.coronavirus.render(screen, 0, 0, 1.0)
        
        # Should have drawn the main body
        mock_draw.circle.assert_called()
        
        # Should have drawn spikes
        self.assertTrue(mock_draw.line.called)

    def test_coronavirus_environment_response(self):
        """Test that Coronavirus responds correctly to environmental conditions"""
        self.env.get_conditions_at = MagicMock(return_value={
            "temperature": 34.0,  # Cold temperature (below 36.0)
            "ph_level": 7.0,
            "nutrients": 100,
            "flow_rate": 0.5
        })
        
        # Set energy for reproduction
        self.coronavirus.energy = 100
        self.coronavirus.replication_cooldown = 0
        
        # Set host for the virus
        self.coronavirus.host = self.host_cell
        self.coronavirus.host.is_alive = True
        
        # Call reproduce in cold environment
        children = self.coronavirus.reproduce(self.env)
        
        # Should have created more viruses due to favorable cold conditions
        self.assertEqual(len(children), 4)
        self.assertEqual(len(self.env.simulation.organisms), 4)
        
        # Verify the get_conditions_at method was called
        self.env.get_conditions_at.assert_called_with(self.coronavirus.x, self.coronavirus.y)

class TestAdenovirus(unittest.TestCase):
    """Test Adenovirus functionality"""
    
    def setUp(self):
        self.env = MockEnvironment()
        self.adenovirus = Adenovirus(100, 100, 3, (220, 100, 100), 2.0)
        # Create a host cell for the virus tests
        self.host_cell = BodyCell(100, 100, 8, (230, 180, 180), 0.2)
        
    def test_initialization(self):
        """Test Adenovirus initialization"""
        self.assertEqual(self.adenovirus.get_name(), "Adenovirus")
        self.assertEqual(self.adenovirus.color, (220, 100, 100))
        self.assertFalse(self.adenovirus.structure["has_envelope"])
        self.assertTrue(self.adenovirus.structure["has_spikes"])
        self.assertTrue(hasattr(self.adenovirus, "fiber_count"))
    
    def test_reproduce(self):
        """Test Adenovirus reproduction with viral burst count"""
        # Set energy for reproduction
        self.adenovirus.energy = 100
        self.adenovirus.replication_cooldown = 0
        
        # Set host for the virus
        self.adenovirus.host = self.host_cell
        self.adenovirus.host.is_alive = True
        
        # Call reproduce
        children = self.adenovirus.reproduce(self.env)
        
        # Should have created viruses based on viral_burst_count (4)
        self.assertEqual(len(children), 4)
        self.assertEqual(len(self.env.simulation.organisms), 4)
        
        # Verify children are adenovirus
        for child in children:
            self.assertEqual(child.get_name(), "Adenovirus")
        
        # Check energy consumption
        self.assertLess(self.adenovirus.energy, 100)
        
        # Check cooldown
        self.assertEqual(self.adenovirus.replication_cooldown, 40)
    
    @patch('pygame.draw')
    def test_render(self, mock_draw):
        """Test adenovirus rendering with its icosahedral shape"""
        # Mock screen
        screen = MagicMock()
        screen.get_width.return_value = 800
        screen.get_height.return_value = 600
        
        # Mock pygame.time.get_ticks for pulsating effect
        pygame.time.get_ticks = MagicMock(return_value=0)
        
        # Call render
        self.adenovirus.render(screen, 0, 0, 1.0)
        
        # Should have drawn the main body
        mock_draw.circle.assert_called()
        
        # Should have drawn facets and fibers
        self.assertTrue(mock_draw.line.called)

    def test_adenovirus_environment_response(self):
        """Test that Adenovirus responds correctly to environmental conditions"""
        # Test in extreme pH environment
        self.env.get_conditions_at = MagicMock(return_value={
            "temperature": 37.0,
            "ph_level": 5.0,  # Acidic environment
            "nutrients": 100,
            "flow_rate": 0.5
        })
        
        # Set energy for reproduction
        self.adenovirus.energy = 100
        self.adenovirus.replication_cooldown = 0
        
        # Set host for the virus
        self.adenovirus.host = self.host_cell
        self.adenovirus.host.is_alive = True
        
        # Call reproduce in acidic environment
        children = self.adenovirus.reproduce(self.env)
        
        # Should still reproduce well in adverse pH
        self.assertEqual(len(children), 4)
        self.assertEqual(len(self.env.simulation.organisms), 4)
        
        # Verify the get_conditions_at method was called
        self.env.get_conditions_at.assert_called_with(self.adenovirus.x, self.adenovirus.y)

if __name__ == '__main__':
    unittest.main() 