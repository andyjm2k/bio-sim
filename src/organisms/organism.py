"""
Base Organism Module for Bio-Sim
Defines the core Organism class that all microorganisms inherit from
"""

import numpy as np
from abc import ABC, abstractmethod
import uuid

class Organism(ABC):
    """
    Abstract base class for all organisms in the simulation.
    All specific organism types should inherit from this class.
    """
    
    def __init__(self, x, y, size, color, speed, dna_length=100):
        """
        Initialize a new organism
        
        Args:
            x (float): Initial x position
            y (float): Initial y position
            size (float): Size of the organism
            color (tuple): RGB color tuple
            speed (float): Base movement speed
            dna_length (int): Length of the DNA sequence
        """
        self.id = str(uuid.uuid4())[:8]  # Unique identifier
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.base_speed = speed
        self.velocity = [np.random.uniform(-1, 1) * speed, 
                        np.random.uniform(-1, 1) * speed]
        
        # Core properties
        self.age = 0
        self.energy = 100.0
        self.health = 100.0
        self.is_alive = True
        
        # Generate DNA sequence
        self.dna = self._generate_dna(dna_length)
        
        # Initialize neural network weights
        self.nn_weights = self._initialize_neural_network()
        
    def _generate_dna(self, length):
        """
        Generate a random DNA sequence
        
        Args:
            length (int): Length of DNA sequence
            
        Returns:
            list: DNA sequence as a list of bases (A, T, G, C)
        """
        bases = ['A', 'T', 'G', 'C']
        return [bases[np.random.randint(0, 4)] for _ in range(length)]
    
    def _initialize_neural_network(self):
        """
        Initialize neural network weights for the organism
        Simple 3-layer network with 5 input neurons, 8 hidden neurons, and 4 output neurons
        
        Returns:
            dict: Neural network weights
        """
        return {
            # Input -> Hidden weights (5 inputs x 8 hidden)
            'w1': np.random.randn(5, 8) * 0.1,
            # Hidden -> Output weights (8 hidden x 4 outputs)
            'w2': np.random.randn(8, 4) * 0.1,
            # Biases
            'b1': np.random.randn(8) * 0.1,
            'b2': np.random.randn(4) * 0.1
        }
    
    def neural_network_decision(self, inputs):
        """
        Make a decision using the organism's neural network
        
        Args:
            inputs (list): List of input values
            
        Returns:
            list: Output values representing the decision
        """
        # Convert inputs to numpy array
        x = np.array(inputs)
        
        # Forward pass through neural network
        z1 = np.dot(x, self.nn_weights['w1']) + self.nn_weights['b1']
        a1 = np.tanh(z1)  # Hidden layer activation
        z2 = np.dot(a1, self.nn_weights['w2']) + self.nn_weights['b2']
        a2 = np.tanh(z2)  # Output layer activation
        
        return a2
    
    def update(self, environment):
        """
        Update the organism's state based on its environment and internal state
        
        Args:
            environment: The environment object containing state information
        """
        if not self.is_alive:
            return
            
        # Age the organism
        self.age += 1
        
        # Process inputs for neural network
        inputs = self._get_neural_network_inputs(environment)
        
        # Get decision from neural network
        decision = self.neural_network_decision(inputs)
        
        # Apply decision to movement and actions
        self._apply_decision(decision, environment)
        
        # Apply environmental effects
        self._apply_environmental_effects(environment)
        
        # Check if organism should die
        self._check_vitals()
    
    def _get_neural_network_inputs(self, environment):
        """
        Prepare inputs for the neural network
        
        Args:
            environment: The environment object
            
        Returns:
            list: Input values for neural network
        """
        # Example inputs:
        # 1. Normalized x position
        # 2. Normalized y position
        # 3. Normalized energy level
        # 4. Nearest food distance (normalized)
        # 5. Nearest threat distance (normalized)
        
        return [
            self.x / environment.width,
            self.y / environment.height,
            self.energy / 100.0,
            0.5,  # Placeholder for nearest food
            0.5   # Placeholder for nearest threat
        ]
    
    def _apply_decision(self, decision, environment):
        """
        Apply the neural network decision to the organism's state
        
        Args:
            decision (list): Output from neural network
            environment: The environment object
        """
        # Example decision application:
        # decision[0] and decision[1] control movement direction
        # decision[2] controls speed
        # decision[3] controls action (feed, reproduce, etc.)
        
        # Update velocity based on decision
        dx = decision[0] * self.base_speed
        dy = decision[1] * self.base_speed
        
        # Add some randomness
        dx += np.random.normal(0, 0.1)
        dy += np.random.normal(0, 0.1)
        
        # Apply movement
        self.velocity = [dx, dy]
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        
        # Boundary wrapping (toroidal world)
        world_width = environment.width
        world_height = environment.height
        
        if self.x < 0:
            self.x += world_width
        elif self.x >= world_width:
            self.x -= world_width
            
        if self.y < 0:
            self.y += world_height
        elif self.y >= world_height:
            self.y -= world_height
        
        # Scale movement cost by size - smaller organisms like viruses use less energy
        size_factor = min(1.0, self.size / 10.0)  # Size factor maxes out at 1.0 for organisms size 10+
        
        # Consume energy for movement - scaled by size
        movement_cost = (abs(dx) + abs(dy)) * 0.1 * size_factor
        
        # Young organisms (like newly created viruses) use even less energy for movement
        if hasattr(self, 'age') and self.age < 10:
            movement_cost *= 0.5  # Half energy consumption for very young organisms
        
        self.energy -= movement_cost
    
    def _apply_environmental_effects(self, environment):
        """
        Apply environmental effects to the organism
        
        Args:
            environment: The environment object
        """
        # Placeholder for environment effects
        # This will be implemented in subclasses
        pass
    
    def _check_vitals(self):
        """Check if the organism should die based on its vital signs"""
        if self.energy <= 0 or self.health <= 0:
            self.is_alive = False
    
    def interact(self, other_organism, environment):
        """
        Interact with another organism
        
        Args:
            other_organism: Another organism instance
            environment: The environment object
        """
        # This will be implemented in subclasses
        pass
    
    def reproduce(self, environment):
        """
        Reproduce to create a new organism
        
        Args:
            environment: The environment object
            
        Returns:
            Organism: A new organism instance or None if reproduction fails
        """
        # This will be implemented in subclasses
        return None
    
    @abstractmethod
    def get_type(self):
        """
        Get the type of organism as a string.
        
        Returns:
            str: The organism type
        """
        pass
        
    def render(self, screen, camera_x, camera_y, zoom):
        """
        Base rendering method for organisms.
        This is a placeholder that can be called by child classes.
        
        Args:
            screen: Pygame screen surface
            camera_x (float): Camera x position
            camera_y (float): Camera y position
            zoom (float): Zoom level
        """
        # Base implementation can be empty or provide common rendering logic
        if not self.is_alive:
            return
            
        # Calculate screen position - common for all organisms
        screen_x = int((self.x - camera_x) * zoom + screen.get_width() / 2)
        screen_y = int((self.y - camera_y) * zoom + screen.get_height() / 2)
        
        # Skip if off screen (optimization)
        if (screen_x < -50 or screen_x > screen.get_width() + 50 or
            screen_y < -50 or screen_y > screen.get_height() + 50):
            return 