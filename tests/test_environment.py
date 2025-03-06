import unittest
from unittest.mock import MagicMock
import sys
import os
import numpy as np

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.environment.environment import Environment
from src.organisms.virus import Virus

class TestEnvironment(unittest.TestCase):
    """Test cases for the Environment class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test config
        self.config = {
            "simulation": {
                "width": 800,
                "height": 600,
                "environment": "test_env"
            },
            "environment_settings": {
                "test_env": {
                    "temperature": 37.0,
                    "ph_level": 7.0,
                    "nutrients": 100,
                    "flow_rate": 0.5
                }
            }
        }
        
        # Create environment
        self.environment = Environment(800, 600, self.config)
        
        # Create mock simulation with organisms
        self.environment.simulation = MagicMock()
        
        # Create test organisms
        self.org1 = MagicMock()
        self.org1.x = 100
        self.org1.y = 100
        self.org1.is_alive = True
        
        self.org2 = MagicMock()
        self.org2.x = 150
        self.org2.y = 100
        self.org2.is_alive = True
        
        self.org3 = MagicMock()
        self.org3.x = 300
        self.org3.y = 300
        self.org3.is_alive = True
        
        self.dead_org = MagicMock()
        self.dead_org.x = 120
        self.dead_org.y = 120
        self.dead_org.is_alive = False
        
        # Set up simulation organisms
        self.environment.simulation.organisms = [self.org1, self.org2, self.org3, self.dead_org]
    
    def test_get_conditions_at(self):
        """Test retrieving environmental conditions at coordinates"""
        conditions = self.environment.get_conditions_at(100, 100)
        
        # Check that we get expected conditions
        self.assertIn("temperature", conditions)
        self.assertIn("ph_level", conditions)
        self.assertIn("nutrients", conditions)
        self.assertIn("flow_rate", conditions)
    
    def test_get_nearby_organisms(self):
        """Test that get_nearby_organisms returns organisms within radius"""
        # Test with small radius (should only get org1)
        nearby = self.environment.get_nearby_organisms(100, 100, 10)
        self.assertEqual(len(nearby), 1)
        self.assertEqual(nearby[0], self.org1)
        
        # Test with larger radius (should get org1 and org2 but not org3)
        nearby = self.environment.get_nearby_organisms(100, 100, 60)
        self.assertEqual(len(nearby), 2)
        self.assertIn(self.org1, nearby)
        self.assertIn(self.org2, nearby)
        self.assertNotIn(self.org3, nearby)
        
        # Test with very large radius (should get all live organisms)
        nearby = self.environment.get_nearby_organisms(100, 100, 1000)
        self.assertEqual(len(nearby), 3)
        self.assertIn(self.org1, nearby)
        self.assertIn(self.org2, nearby)
        self.assertIn(self.org3, nearby)
        
        # Verify dead organisms are not included
        self.assertNotIn(self.dead_org, nearby)
        
    def test_get_nearby_organisms_no_simulation(self):
        """Test behavior when simulation is not set"""
        # Remove simulation reference
        self.environment.simulation = None
        
        # Should return empty list and not crash
        nearby = self.environment.get_nearby_organisms(100, 100, 50)
        self.assertEqual(nearby, [])

if __name__ == '__main__':
    unittest.main() 