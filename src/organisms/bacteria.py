"""
Bacteria Module for Bio-Sim
Implements the Bacteria class, representing bacterial microorganisms
"""

import numpy as np
import pygame
from pygame import gfxdraw
import random
from src.organisms.organism import Organism

class Bacteria(Organism):
    """
    Bacteria class representing bacterial microorganisms in the simulation.
    Bacteria tend to reproduce quickly and are affected by environmental factors.
    """
    
    def __init__(self, x, y, size, color, speed, dna_length=100):
        """
        Initialize a new bacteria organism
        
        Args:
            x (float): Initial x position
            y (float): Initial y position
            size (float): Size of the bacteria
            color (tuple): RGB color tuple
            speed (float): Base movement speed
            dna_length (int): Length of the DNA sequence
        """
        super().__init__(x, y, size, color, speed, dna_length)
        
        # Bacteria-specific properties
        self.reproduction_rate = 0.04  # Increased from lower value
        self.nutrient_consumption = 0.05  # Amount of nutrients consumed per update
        self.optimal_temperature = 37.0  # Optimal temperature for growth
        self.optimal_ph = 7.0  # Optimal pH for growth
        self.reproduction_energy_threshold = 80  # Reduced from higher value
        self.age = 0
        self.metabolic_rate = 0.1  # Energy consumption rate
        self.nutrient_absorption = 0.3  # Nutrient absorption rate
        
        # Modify properties based on DNA
        self._apply_dna_effects()
    
    def _apply_dna_effects(self):
        """Apply effects of the DNA sequence to the bacteria's properties"""
        # Count bases in DNA to determine traits
        base_counts = {
            'A': self.dna.count('A'),
            'T': self.dna.count('T'),
            'G': self.dna.count('G'),
            'C': self.dna.count('C')
        }
        
        # Normalize counts
        total = sum(base_counts.values())
        for base in base_counts:
            base_counts[base] /= total
        
        # Apply effects based on DNA composition
        # More A: Better reproduction
        # More T: Better temperature resistance
        # More G: Better pH resistance
        # More C: Better nutrient efficiency
        
        self.reproduction_rate += base_counts['A'] * 0.002
        self.optimal_temperature += (base_counts['T'] - 0.25) * 5
        self.optimal_ph += (base_counts['G'] - 0.25) * 2
        self.nutrient_consumption -= base_counts['C'] * 0.03
    
    def _apply_environmental_effects(self, environment):
        """
        Apply environmental effects to the bacteria
        
        Args:
            environment: The environment object
        """
        # Get environment variables for current position
        env_data = environment.get_conditions_at(self.x, self.y)
        
        # Temperature effect
        temp_diff = abs(env_data['temperature'] - self.optimal_temperature)
        temp_effect = max(0, 1 - (temp_diff / 10))
        
        # pH effect
        ph_diff = abs(env_data['ph_level'] - self.optimal_ph)
        ph_effect = max(0, 1 - (ph_diff / 2))
        
        # Nutrient effect
        nutrient_level = env_data['nutrients'] / 100
        
        # Apply combined environmental effects
        overall_effect = (temp_effect + ph_effect + nutrient_level) / 3
        
        # Consume nutrients
        consumed = self.nutrient_consumption * overall_effect
        environment.consume_nutrients(self.x, self.y, consumed)
        
        # Gain energy based on nutrients consumed
        self.energy += consumed * 10
        
        # Cap energy at 150
        self.energy = min(150, self.energy)
        
        # Health is affected by environmental conditions
        if overall_effect < 0.5:
            self.health -= (0.5 - overall_effect) * 2
    
    def reproduce(self, environment):
        """
        Attempt to reproduce based on energy level and reproduction rate
        
        Args:
            environment: The environment object
            
        Returns:
            Bacteria: A new bacteria instance or None if reproduction fails
        """
        # Check population cap from environment config
        max_organisms = environment.config.get("simulation_settings", {}).get("max_organisms", 0)
        
        # Check if enough energy and random chance for reproduction
        if (self.energy > self.reproduction_energy_threshold and 
            self.is_alive and 
            np.random.random() < self.reproduction_rate):
            
            # Create mutation in DNA
            child_dna = self.dna.copy()
            if np.random.random() < environment.config['simulation_settings']['mutation_rate']:
                mutation_idx = np.random.randint(0, len(child_dna))
                bases = ['A', 'T', 'G', 'C']
                child_dna[mutation_idx] = bases[np.random.randint(0, 4)]
            
            # Slightly mutate color
            r, g, b = self.color
            color_mutation = 10
            new_color = (
                max(0, min(255, r + np.random.randint(-color_mutation, color_mutation))),
                max(0, min(255, g + np.random.randint(-color_mutation, color_mutation))),
                max(0, min(255, b + np.random.randint(-color_mutation, color_mutation)))
            )
            
            # Create child with random position deviation
            offset = 10
            new_x = max(0, min(environment.width, self.x + np.random.randint(-offset, offset)))
            new_y = max(0, min(environment.height, self.y + np.random.randint(-offset, offset)))
            
            # Consume more energy for reproduction
            self.energy -= 50  # Changed from 70 to increase population growth
            
            # Create child of the same specific type as the parent
            child = None
            # Use the actual class of the instance (not Bacteria base class)
            child_class = self.__class__
            
            try:
                # Create a new instance of the same class
                child = child_class(new_x, new_y, self.size * 0.8, new_color, self.base_speed * 0.9)
                
                # Copy over DNA to child
                child.dna = child_dna
                
                # Apply DNA effects to update child attributes
                child._apply_dna_effects()
                
                # Start with reduced energy
                child.energy = 60
                
                return child
            except Exception as e:
                print(f"Error during reproduction: {e}")
                import traceback
                traceback.print_exc()
        
        return None
    
    def interact(self, other_organism, environment):
        """
        Interact with another organism
        
        Args:
            other_organism: Another organism instance
            environment: The environment object
        """
        # Skip if not alive
        if not self.is_alive:
            return
            
        # Get type of other organism
        other_type = getattr(other_organism, 'get_type', lambda: 'unknown')()
        
        # Bacteria can attack cells
        if "cell" in other_type.lower() and not "white" in other_type.lower():
            # Harmful bacteria attack body cells
            if self.get_type() != "BeneficialBacteria":
                # Calculate distance
                dx = self.x - other_organism.x
                dy = self.y - other_organism.y
                distance = np.sqrt(dx**2 + dy**2)
                
                # If close enough, damage cell
                if distance <= self.size + other_organism.size + 5:
                    damage = 0.8  # Increased from lower value
                    
                    # More dangerous bacteria cause more damage
                    if self.get_type() == "Salmonella" or self.get_type() == "Staphylococcus":
                        damage = 1.5  # Increased from lower value
                    
                    # Apply damage if target can take damage
                    if hasattr(other_organism, 'take_damage'):
                        other_organism.take_damage(damage)
                        
                        # Bacteria gains energy from damaging cells
                        self.energy += damage * 2
        
        # Can feed on nutrients from dead organisms
        if hasattr(other_organism, 'is_alive') and not other_organism.is_alive:
            self.energy += 5
            return
        
        # Special interaction with red blood cells - some bacteria attack RBCs
        if other_type == "RedBloodCell" and hasattr(other_organism, 'take_damage'):
            # Only some bacteria attack red blood cells
            bacteria_type = self.get_type()
            if bacteria_type in ["EColi", "Streptococcus"]:  # These bacteria can attack RBCs
                damage_amount = 2
                if bacteria_type == "Streptococcus":
                    damage_amount = 4  # Streptococcus is more damaging to RBCs
                
                # Attack the red blood cell
                other_organism.take_damage(damage_amount)
                
                # Gain energy from attacking
                self.energy += 3
                
        # Interaction with other bacteria
        if "bacteria" in other_type.lower():
            # Competition for resources
            # The stronger bacteria (more energy/health) takes resources from the weaker
            my_strength = self.energy * (self.health / 100)
            other_strength = getattr(other_organism, 'energy', 50) * (getattr(other_organism, 'health', 50) / 100)
            
            if my_strength > other_strength * 1.2:  # Need significant advantage
                # Take resources
                self.energy += 2
                if hasattr(other_organism, 'energy'):
                    other_organism.energy -= 2
            
        # Can be attacked by immune cells
        if "whiteb" in other_type.lower() or "tcell" in other_type.lower() or "macro" in other_type.lower():
            # Check if this type of bacteria is targeted by this immune cell
            targeted = True  # Default assumption
            
            # T-Cells target specific bacteria more effectively
            if "tcell" in other_type.lower() and hasattr(other_organism, 'targets'):
                if self.get_type() not in getattr(other_organism, 'targets', [self.get_type()]):
                    targeted = False
            
            if targeted:
                # Calculate attack chance
                attack_chance = 0.1  # Base chance
                
                # Macrophages are better at engulfing bacteria
                if "macro" in other_type.lower():
                    attack_chance = 0.25
                
                # Check if attack succeeds
                if environment.random.random() < attack_chance:
                    self.health -= 15
                    
                    # If killed, give energy to the immune cell
                    if self.health <= 0 and hasattr(other_organism, 'energy'):
                        other_organism.energy += 10
    
    def get_type(self):
        """Return the type of organism"""
        return "bacteria"
        
    def infect(self, virus):
        """
        Get infected by a virus
        
        Args:
            virus: The virus attempting to infect this bacteria
            
        Returns:
            bool: True if infection was successful, False otherwise
        """
        # Bacteria can be infected by viruses
        self.is_infected = True
        self.health -= 5  # Initial damage from infection
        return True

class EColi(Bacteria):
    """E. coli bacteria class"""
    
    def __init__(self, x, y, size, color, speed):
        """Initialize E. coli with specific traits"""
        super().__init__(x, y, size, color, speed)
        self.color = (30, 180, 30)  # Green
        self.shape = "rod"
        self.flagella_count = random.randint(4, 8)  # E. coli have multiple flagella
        
        # E. coli specific traits - use a separate dictionary for traits
        self.dna_traits = {
            "ph_preference": 6.0,  # Prefers slightly acidic
            "temperature_preference": 37.0,  # Human body temp
            "metabolism_rate": 1.5,  # Fast metabolism
            "resistance": 0.3
        }
        
        # Update resistance profile
        self.antibiotic_resistance = {
            "penicillin": 0.4,  # More resistant to penicillin
            "amoxicillin": 0.3,
            "ciprofloxacin": 0.1,
            "tetracycline": 0.2
        }
    
    def get_type(self):
        return "bacteria"
        
    def get_name(self):
        return "E. coli"
        
    def render(self, screen, camera_x, camera_y, zoom):
        """Render E. coli with distinctive rod shape and flagella"""
        if not self.is_alive:
            return
            
        import pygame
        
        # Calculate screen position
        screen_x = int((self.x - camera_x) * zoom + screen.get_width() / 2)
        screen_y = int((self.y - camera_y) * zoom + screen.get_height() / 2)
        
        # Skip if off screen
        if (screen_x < -50 or screen_x > screen.get_width() + 50 or
            screen_y < -50 or screen_y > screen.get_height() + 50):
            return
        
        # Rod shape - elongated rectangle rather than circle
        radius = max(2, int(self.size * zoom))
        length = radius * 2  # Make it twice as long as it is wide
        
        # Draw rod body (rounded rectangle)
        self.color = (100, 180, 100)  # Consistent green for E. coli
        
        # Create the rod surface with transparency
        rod_surface = pygame.Surface((length + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.ellipse(rod_surface, self.color, (0, 0, length + 2, radius * 2 + 2))
        
        # Rotation based on movement direction
        angle = 0
        if hasattr(self, 'vx') and hasattr(self, 'vy'):
            if abs(self.vx) > 0.01 or abs(self.vy) > 0.01:
                angle = pygame.math.Vector2(self.vx, self.vy).angle_to((1, 0))
        
        # Rotate the surface
        rod_surface = pygame.transform.rotate(rod_surface, angle)
        
        # Get the rect for positioning
        rect = rod_surface.get_rect(center=(screen_x, screen_y))
        
        # Draw the rod
        screen.blit(rod_surface, rect.topleft)
        
        # Draw flagella (thin curves extending from the back)
        # Get direction vector
        direction = pygame.math.Vector2(1, 0).rotate(angle)
        
        # Flagella start point is at the back of the bacteria
        flagella_start = pygame.math.Vector2(screen_x, screen_y) - direction * (length / 2)
        
        # Draw multiple small flagella
        for offset in [-0.3, 0, 0.3]:
            # Perpendicular vector for offset
            perp = pygame.math.Vector2(-direction.y, direction.x) * radius * offset
            start_point = (int(flagella_start.x + perp.x), int(flagella_start.y + perp.y))
            
            # Draw a wavy flagellum
            prev_point = start_point
            flagella_length = radius * 3
            
            for i in range(1, 6):
                # Wavy pattern
                wave_offset = perp * 0.5 * (-1 if i % 2 == 0 else 1)
                point = (
                    int(start_point[0] - direction.x * i * flagella_length / 5 + wave_offset.x),
                    int(start_point[1] - direction.y * i * flagella_length / 5 + wave_offset.y)
                )
                pygame.draw.line(screen, (50, 120, 50), prev_point, point, 1)
                prev_point = point

class Streptococcus(Bacteria):
    """Streptococcus bacteria class"""
    
    def __init__(self, x, y, size, color, speed):
        """Initialize Streptococcus with specific traits"""
        super().__init__(x, y, size, color, speed)
        self.color = (180, 100, 100)  # Reddish
        self.shape = "spherical"
        self.flagella_count = 0  # No flagella
        self.chain_length = random.randint(3, 8)  # Forms chains of cocci
        
        # Streptococcus specific traits
        self.dna_traits = {
            "ph_preference": 7.0,
            "temperature_preference": 37.0,
            "virulence": 0.7  # More virulent
        }
        
        # Update resistance profile
        self.antibiotic_resistance = {
            "penicillin": 0.2,
            "amoxicillin": 0.2,
            "ciprofloxacin": 0.3,
            "tetracycline": 0.2
        }
    
    def get_type(self):
        return "bacteria"
        
    def get_name(self):
        return "Streptococcus"
        
    def render(self, screen, camera_x, camera_y, zoom):
        """Render Streptococcus as chains of cocci (spherical cells)"""
        if not self.is_alive:
            return
            
        import pygame
        import math
        
        # Calculate screen position for the lead cell
        screen_x = int((self.x - camera_x) * zoom + screen.get_width() / 2)
        screen_y = int((self.y - camera_y) * zoom + screen.get_height() / 2)
        
        # Skip if off screen
        if (screen_x < -50 or screen_x > screen.get_width() + 50 or
            screen_y < -50 or screen_y > screen.get_height() + 50):
            return
        
        # Get direction vector based on movement
        angle = 0
        if hasattr(self, 'vx') and hasattr(self, 'vy'):
            if abs(self.vx) > 0.01 or abs(self.vy) > 0.01:
                angle = math.atan2(self.vy, self.vx)
        
        # Chain properties
        self.color = (80, 150, 80)  # Green for Streptococcus
        radius = max(2, int(self.size * zoom * 0.8))  # Slightly smaller cells but more of them
        chain_length = 4  # Number of cells in the chain
        
        # Calculate the position of each cell in the chain
        # They follow behind the lead cell in a chain formation
        for i in range(chain_length):
            # Position each cell behind the previous one
            cell_x = screen_x - int(math.cos(angle) * radius * 1.8 * i)
            cell_y = screen_y - int(math.sin(angle) * radius * 1.8 * i)
            
            # Skip if this cell is off screen
            if (cell_x < -20 or cell_x > screen.get_width() + 20 or
                cell_y < -20 or cell_y > screen.get_height() + 20):
                continue
            
            # Draw cell
            pygame.draw.circle(screen, self.color, (cell_x, cell_y), radius)
            
            # Draw outline
            pygame.draw.circle(screen, (min(255, self.color[0] + 40), 
                                        min(255, self.color[1] + 40), 
                                        min(255, self.color[2] + 40)), 
                              (cell_x, cell_y), radius, 1)
            
            # If not the last cell, draw connection to next cell
            if i < chain_length - 1:
                next_x = screen_x - int(math.cos(angle) * radius * 1.8 * (i + 1))
                next_y = screen_y - int(math.sin(angle) * radius * 1.8 * (i + 1))
                
                # Draw connection line
                pygame.draw.line(screen, (self.color[0], self.color[1], self.color[2], 128),
                                (cell_x, cell_y), (next_x, next_y), 1)

class Staphylococcus(Bacteria):
    """Staphylococcus bacteria class"""
    
    def __init__(self, x, y, size, color, speed):
        """Initialize Staphylococcus with specific traits"""
        super().__init__(x, y, size, color, speed)
        self.color = (180, 180, 50)  # Yellow/golden
        self.shape = "spherical"
        self.flagella_count = 0  # No flagella
        self.cluster_size = random.randint(4, 12)  # Forms clusters
        
        # Staphylococcus specific traits
        self.dna_traits = {
            "ph_preference": 7.5,  # Slightly alkaline
            "temperature_preference": 37.0,
            "virulence": 0.8,  # Very virulent
            "resistance": 0.7  # High resistance
        }
        
        # Update resistance profile
        self.antibiotic_resistance = {
            "penicillin": 0.8,  # High resistance
            "amoxicillin": 0.7,
            "ciprofloxacin": 0.4,
            "tetracycline": 0.5
        }
    
    def get_type(self):
        return "Staphylococcus"
        
    def get_name(self):
        return "Staphylococcus"
        
    def render(self, screen, camera_x, camera_y, zoom):
        """Render Staphylococcus as cluster of cocci"""
        if not self.is_alive:
            return
            
        # Calculate screen position for the center
        screen_x = int((self.x - camera_x) * zoom + screen.get_width() / 2)
        screen_y = int((self.y - camera_y) * zoom + screen.get_height() / 2)
        
        # Skip if off screen
        if (screen_x < -50 or screen_x > screen.get_width() + 50 or
            screen_y < -50 or screen_y > screen.get_height() + 50):
            return
            
        # Scale size with zoom
        display_size = max(2, int(self.size * zoom))
        
        # Draw cluster of cocci
        for i in range(self.cluster_size):
            # Position each coccus randomly in a cluster
            offset_dir = random.uniform(0, 2 * np.pi)
            offset_dist = random.uniform(0, display_size * 1.2)
            pos_x = screen_x + int(np.cos(offset_dir) * offset_dist)
            pos_y = screen_y + int(np.sin(offset_dir) * offset_dist)
            
            # Draw the coccus
            pygame.draw.circle(screen, self.color, (pos_x, pos_y), display_size - 1)
            
            # Add a darker border
            pygame.draw.circle(
                screen, 
                tuple(max(0, c-80) for c in self.color), 
                (pos_x, pos_y), 
                display_size - 1, 
                1
            )

class Salmonella(Bacteria):
    """Salmonella bacteria class"""
    
    def __init__(self, x, y, size, color, speed):
        """Initialize Salmonella with specific traits"""
        super().__init__(x, y, size, color, speed)
        self.color = (200, 100, 180)  # Pinkish
        self.shape = "rod"
        self.flagella_count = random.randint(5, 10)  # Many flagella
        
        # Salmonella specific traits
        self.dna_traits = {
            "ph_preference": 6.5,  # Slightly acidic
            "temperature_preference": 38.0,  # Slight fever
            "metabolism_rate": 1.2,
            "virulence": 0.9  # Highly virulent
        }
        
        # Update resistance profile
        self.antibiotic_resistance = {
            "penicillin": 0.5,
            "amoxicillin": 0.4,
            "ciprofloxacin": 0.2,
            "tetracycline": 0.3
        }
    
    def get_type(self):
        return "Salmonella"
        
    def get_name(self):
        return "Salmonella"
        
    def render(self, screen, camera_x, camera_y, zoom):
        """Render Salmonella with distinctive rod shape and many flagella"""
        # Use base rendering with right color
        self.color = (200, 100, 180)  # Pinkish color
        super().render(screen, camera_x, camera_y, zoom)
        
        # Additional distinctive flagella pattern
        if self.is_alive:
            screen_x = int((self.x - camera_x) * zoom + screen.get_width() / 2)
            screen_y = int((self.y - camera_y) * zoom + screen.get_height() / 2)
            display_size = max(2, int(self.size * zoom))
            
            # Calculate direction from velocity
            if hasattr(self, 'velocity') and (abs(self.velocity[0]) > 0.01 or abs(self.velocity[1]) > 0.01):
                direction = np.arctan2(self.velocity[1], self.velocity[0])
            else:
                # Default direction if velocity is too small
                direction = np.random.uniform(0, 2 * np.pi)
            
            # Add additional flagella along sides
            for i in range(3):
                side_angle1 = direction + np.pi/2
                side_angle2 = direction - np.pi/2
                
                # Side points
                side_x1 = screen_x + int(np.cos(side_angle1) * display_size/2)
                side_y1 = screen_y + int(np.sin(side_angle1) * display_size/2)
                side_x2 = screen_x + int(np.cos(side_angle2) * display_size/2)
                side_y2 = screen_y + int(np.sin(side_angle2) * display_size/2)
                
                # Draw side flagella
                pygame.draw.line(
                    screen,
                    tuple(max(0, c-50) for c in self.color),
                    (side_x1, side_y1),
                    (side_x1 + int(np.cos(side_angle1 + 0.5) * display_size), 
                     side_y1 + int(np.sin(side_angle1 + 0.5) * display_size)),
                    max(1, display_size // 4)
                )
                
                pygame.draw.line(
                    screen,
                    tuple(max(0, c-50) for c in self.color),
                    (side_x2, side_y2),
                    (side_x2 + int(np.cos(side_angle2 - 0.5) * display_size), 
                     side_y2 + int(np.sin(side_angle2 - 0.5) * display_size)),
                    max(1, display_size // 4)
                )

class BeneficialBacteria(Bacteria):
    """
    BeneficialBacteria class representing probiotic bacteria that improve gut health.
    These bacteria have positive interactions with the host and can outcompete harmful bacteria.
    """
    
    def __init__(self, x, y, size, color, speed):
        """
        Initialize a new beneficial bacteria organism
        
        Args:
            x (float): Initial x position
            y (float): Initial y position
            size (float): Size of the bacteria
            color (tuple): RGB color tuple
            speed (float): Base movement speed
        """
        super().__init__(x, y, size, color, speed)
        
        # Beneficial bacteria-specific properties
        self.reproduction_rate = 0.0008  # Slower reproduction than harmful bacteria
        self.nutrient_consumption = 0.03  # Consumes fewer nutrients
        self.optimal_temperature = 37.5  # Slight preference for warmer conditions
        self.optimal_ph = 6.8  # Slightly acidic environment preference
        self.reproduction_energy_threshold = 100  # Lower threshold for reproduction
        self.antibiotic_resistance = 0.7  # Higher resistance to antibiotics
        self.host_benefit = 0.2  # Positive effect on the host (theoretical)
        
    def interact(self, other_organism, environment):
        """
        Specialized interaction behavior for beneficial bacteria
        
        Args:
            other_organism: The organism to interact with
            environment: The simulation environment
            
        Returns:
            bool: True if interaction occurred, False otherwise
        """
        result = super().interact(other_organism, environment)
        
        # Beneficial bacteria can inhibit harmful bacteria growth
        if result is False and "Bacteria" in other_organism.__class__.__name__:
            if "EColi" in other_organism.__class__.__name__ or "Salmonella" in other_organism.__class__.__name__:
                # Chance to reduce harmful bacteria energy
                if environment.random.random() < 0.2:
                    other_organism.energy -= environment.random.uniform(0, 5)
                    return True
                    
        return result
        
    def get_type(self):
        """Return the organism type"""
        return "beneficial_bacteria"
        
    def get_name(self):
        """Return the organism name"""
        return "Beneficial Bacteria"
        
    def render(self, screen, camera_x, camera_y, zoom):
        """
        Render the beneficial bacteria with a distinctive appearance
        that conveys its probiotic nature and gut health benefits
        
        Args:
            screen: Pygame screen to render on
            camera_x (float): Camera x position
            camera_y (float): Camera y position
            zoom (float): Zoom level
        """
        if not self.is_alive:
            return
            
        import pygame
        import math
        
        # Calculate screen position
        screen_x = int((self.x - camera_x) * zoom + screen.get_width() / 2)
        screen_y = int((self.y - camera_y) * zoom + screen.get_height() / 2)
        
        # Skip if off screen
        if (screen_x < -50 or screen_x > screen.get_width() + 50 or
            screen_y < -50 or screen_y > screen.get_height() + 50):
            return
        
        # Size and color
        radius = max(2, int(self.size * zoom))
        self.color = (100, 180, 220)  # Blue color representing beneficial/healthy bacteria
        
        # Draw with a glow effect to convey "beneficial" nature
        for r in range(3):
            glow_radius = radius + (2-r)
            alpha = 100 - r * 30
            glow_color = (100, 180, 220, alpha)
            
            # Create a surface for the glowing circle
            glow_surface = pygame.Surface((glow_radius * 2 + 4, glow_radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, glow_color, (glow_radius + 2, glow_radius + 2), glow_radius)
            
            # Blit the glow surface
            screen.blit(glow_surface, (screen_x - glow_radius - 2, screen_y - glow_radius - 2))
        
        # Draw the main body of the bacteria (yogurt-like)
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), radius)
        
        # Add a lighter border to emphasize healthiness
        pygame.draw.circle(
            screen, 
            (min(255, self.color[0] + 50), min(255, self.color[1] + 50), min(255, self.color[2] + 50)),
            (screen_x, screen_y), 
            radius, 
            1
        )
        
        # Draw small spots within the bacteria to represent diverse beneficial properties
        # These could symbolize different probiotic strains or nutrients
        for i in range(3):
            angle = i * (2 * math.pi / 3)
            offset_x = int(radius * 0.5 * math.cos(angle))
            offset_y = int(radius * 0.5 * math.sin(angle))
            spot_radius = max(1, int(radius * 0.2))
            
            # Draw a small white spot
            pygame.draw.circle(
                screen, 
                (240, 240, 255),
                (screen_x + offset_x, screen_y + offset_y), 
                spot_radius
            ) 