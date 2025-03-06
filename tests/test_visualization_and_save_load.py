import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import numpy as np
import pygame
import tempfile
import shutil

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.visualization.renderer import Renderer
from src.environment.environment import Environment
from src.simulation import BioSimulation
from src.utils.save_load import save_simulation, load_simulation, list_saved_simulations

class TestEnvironmentViewMode(unittest.TestCase):
    """Test cases for the environment view mode functionality"""
    
    def setUp(self):
        """Set up test environment and renderer"""
        # Initialize pygame
        pygame.init()
        
        # Create a test screen
        self.screen = pygame.Surface((800, 600))
        
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
            },
            "visualization": {
                "show_stats": True,
                "show_grid": False
            }
        }
        
        # Create the renderer
        self.renderer = Renderer(self.screen, self.config)
        
        # Create a mock environment
        self.environment = MagicMock()
        self.environment.width = 800
        self.environment.height = 600
        self.environment.temperature_grid = np.ones((10, 10)) * 37.0
        self.environment.ph_grid = np.ones((10, 10)) * 7.0
        self.environment.nutrient_grid = np.ones((10, 10)) * 100
        self.environment.flow_rate_grid = np.ones((10, 10)) * 0.5
        self.environment.get_grid_dimensions.return_value = (10, 10)
        
    def test_toggle_environment_view(self):
        """Test toggling environment visualization on and off"""
        # Initially environment view should be off
        self.assertFalse(self.renderer.show_environment)
        
        # Toggle on
        self.renderer.toggle_environment_view()
        self.assertTrue(self.renderer.show_environment)
        
        # Toggle off
        self.renderer.toggle_environment_view()
        self.assertFalse(self.renderer.show_environment)
    
    def test_cycle_visualization_mode(self):
        """Test cycling through the visualization modes"""
        # Initial mode is 0 (Temperature)
        self.assertEqual(self.renderer.env_view_mode, 0)
        
        # First cycle: Temperature -> pH
        self.renderer.cycle_visualization_mode()
        self.assertEqual(self.renderer.env_view_mode, 1)
        
        # Second cycle: pH -> Nutrients
        self.renderer.cycle_visualization_mode()
        self.assertEqual(self.renderer.env_view_mode, 2)
        
        # Third cycle: Nutrients -> Flow
        self.renderer.cycle_visualization_mode()
        self.assertEqual(self.renderer.env_view_mode, 3)
        
        # Fourth cycle: Flow -> Temperature (wraps around)
        self.renderer.cycle_visualization_mode()
        self.assertEqual(self.renderer.env_view_mode, 0)
        
        # Also ensures environment view is enabled
        self.assertTrue(self.renderer.show_environment)
    
    def test_tab_key_handling(self):
        """Test handling of the Tab key event"""
        # Create a mock event
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_TAB
        
        # Initially set both modes to known states
        self.renderer.show_environment = False
        self.renderer.env_view_mode = 0
        
        # Handle the Tab key event
        result = self.renderer.handle_input(event)
        
        # Verify the result and state changes
        self.assertTrue(result)  # Event was handled
        self.assertTrue(self.renderer.show_environment)  # View should be enabled
        self.assertEqual(self.renderer.env_view_mode, 1)  # Mode should be incremented
        
    def tearDown(self):
        """Clean up resources"""
        pygame.quit()


class TestSaveLoadSimulation(unittest.TestCase):
    """Test cases for saving and loading simulation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
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
        
        # Create test organisms
        self.organisms = []
        
        # Mock organism that implements the required interfaces
        for i in range(5):
            organism = MagicMock()
            organism.x = i * 100
            organism.y = i * 100
            organism.size = 5
            organism.color = (255, 0, 0)
            organism.base_speed = 1.0
            organism.velocity = [0.5, 0.5]
            organism.age = i * 10
            organism.energy = 100
            organism.health = 100
            organism.is_alive = True
            organism.dna = "AGTC" * 10
            organism.id = f"test-org-{i}"
            organism.get_type.return_value = "test_organism"
            self.organisms.append(organism)
    
    def test_save_simulation(self):
        """Test saving a simulation state"""
        # Define a test filepath
        test_filepath = os.path.join(self.test_dir, "test_save.biosim")
        
        # Save the simulation
        filepath = save_simulation(self.environment, self.organisms, test_filepath)
        
        # Verify the file was created
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(test_filepath))
        
    @patch('src.utils.save_load.load_simulation')
    def test_list_saved_simulations(self, mock_load):
        """Test listing saved simulation files"""
        # Create a few test save files
        for i in range(3):
            with open(os.path.join(self.test_dir, f"test_save_{i}.biosim"), 'w') as f:
                f.write("test")
        
        # Patch the function to look in our test directory
        with patch('os.listdir', return_value=["test_save_0.biosim", "test_save_1.biosim", "test_save_2.biosim"]), \
             patch('src.utils.save_load.os.path.join', return_value="test_path"):
            
            # List the saved simulations
            save_files = list_saved_simulations()
            
            # Verify we got the expected number of files
            self.assertEqual(len(save_files), 3)
    
    @patch('src.utils.save_load.pickle.dump')
    @patch('src.utils.save_load.pickle.load')
    def test_save_load_simulation_integration(self, mock_load, mock_dump):
        """Test the full save and load simulation process"""
        # Mock the pickle load to return our test data
        mock_load.return_value = {
            "timestamp": "2023-03-05T12:00:00",
            "config": self.config,
            "organisms": [
                {
                    "type": "EColi",
                    "x": 100,
                    "y": 100,
                    "size": 5,
                    "color": (255, 0, 0),
                    "base_speed": 1.0,
                    "velocity": [0.5, 0.5],
                    "age": 10,
                    "energy": 100,
                    "health": 100,
                    "is_alive": True,
                    "dna": "AGTC" * 10,
                    "id": "test-org-0"
                }
            ],
            "environment": {
                "width": 800,
                "height": 600,
                "tick_count": 100,
                "temperature_grid": np.ones((10, 10)).tolist(),
                "ph_grid": np.ones((10, 10)).tolist(),
                "nutrient_grid": np.ones((10, 10)).tolist(),
                "flow_rate_grid": np.ones((10, 10)).tolist()
            }
        }
        
        # Test filepath
        test_filepath = os.path.join(self.test_dir, "test_save_load.biosim")
        
        # Save the simulation
        with patch('builtins.open', create=True):
            save_path = save_simulation(self.environment, self.organisms, test_filepath)
            self.assertEqual(save_path, test_filepath)
            
            # Now load the simulation
            with patch('src.organisms.bacteria.EColi', MagicMock()), \
                 patch('src.organisms.bacteria.Streptococcus', MagicMock()), \
                 patch('src.organisms.bacteria.BeneficialBacteria', MagicMock()), \
                 patch('src.organisms.virus.Influenza', MagicMock()), \
                 patch('src.organisms.virus.Rhinovirus', MagicMock()), \
                 patch('src.organisms.virus.Coronavirus', MagicMock()), \
                 patch('src.organisms.virus.Adenovirus', MagicMock()), \
                 patch('src.organisms.white_blood_cell.Neutrophil', MagicMock()), \
                 patch('src.organisms.white_blood_cell.Macrophage', MagicMock()), \
                 patch('src.organisms.white_blood_cell.TCell', MagicMock()), \
                 patch('src.organisms.body_cells.RedBloodCell', MagicMock()), \
                 patch('src.organisms.body_cells.EpithelialCell', MagicMock()), \
                 patch('src.organisms.body_cells.Platelet', MagicMock()):
                
                env, orgs = load_simulation(test_filepath)
                
                # Verify we got something back
                self.assertIsNotNone(env)
                self.assertIsNotNone(orgs)
    
    def test_simulation_save_load_methods(self):
        """Test the simulation class methods for saving and loading"""
        # Initialize pygame for the test
        pygame.init()
        
        # Create a mock screen
        screen = pygame.Surface((800, 600))
        
        # Create a BioSimulation instance
        with patch('pygame.display.set_mode', return_value=screen), \
             patch('src.simulation.BioSimulation.initialize_simulation'):
            
            simulation = BioSimulation(self.config)
            simulation.environment = self.environment
            simulation.organisms = self.organisms
            
            # Test save_simulation_dialog
            with patch('src.simulation.save_simulation', return_value="test_save_path.biosim"):
                simulation.save_simulation_dialog()
                # We just want to make sure it doesn't raise an exception
            
            # Test load_simulation_dialog
            with patch('src.simulation.list_saved_simulations', return_value=["test_save_path.biosim"]), \
                 patch('src.simulation.load_simulation', return_value=(self.environment, self.organisms)):
                simulation.load_simulation_dialog()
                # Again, just ensure it doesn't raise an exception
        
        # Clean up pygame
        pygame.quit()
    
    def tearDown(self):
        """Clean up resources"""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)


if __name__ == '__main__':
    unittest.main() 