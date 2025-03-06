"""
Body Cells Module for Bio-Sim
Contains classes for various body cells that can be targets for microorganisms
"""

import pygame
import math
import numpy as np
from src.organisms.organism import Organism

class BodyCell(Organism):
    """
    Base class for body cells that can be targets for microorganisms.
    These cells are part of the host body, not invaders or defenders.
    """
    
    def __init__(self, x, y, size, color, speed, dna_length=80):
        """
        Initialize a body cell
        
        Args:
            x (float): Initial x position
            y (float): Initial y position
            size (float): Size of the cell
            color (tuple): RGB color tuple
            speed (float): Base movement speed
            dna_length (int): Length of the DNA sequence
        """
        super().__init__(x, y, size, color, speed, dna_length)
        self.damaged = False
        self.damage_level = 0
        self.infected_by = None
        self.regeneration_rate = 0.1  # Health recovery per update
        self.infection_resistance = 0.2  # Base resistance to infection
        self.infection_recovery_chance = 0.001  # Small chance to recover from infection naturally
        
        # Most body cells should not reproduce in the simulation 
        # (except maybe some special cases like stem cells)
        self.can_reproduce = False
        self.cell_type = "generic"
        
        # Print debug info for creation
        print(f"Created {self.__class__.__name__} at ({x:.1f}, {y:.1f}) with can_reproduce={self.can_reproduce}")
        
    def _decode_dna(self):
        """
        Decode DNA sequence to derive trait values.
        Returns a list of normalized values between 0 and 1 that can be used
        for various traits in derived cell classes.
        
        Returns:
            list: List of trait values derived from DNA
        """
        # Extract trait values from DNA sequences by splitting into sections
        if len(self.dna) < 3:
            # Default values if DNA is too short
            return [0.5, 0.5, 0.5]
            
        # Split DNA into sections for different traits
        section_size = len(self.dna) // 3
        sections = [
            self.dna[0:section_size],
            self.dna[section_size:2*section_size],
            self.dna[2*section_size:]
        ]
        
        # Calculate trait values from each section
        trait_values = []
        for section in sections:
            # Count GC content (G and C bases) as a simple metric
            gc_count = section.count('G') + section.count('C')
            # Normalize to 0-1 range
            trait_value = gc_count / len(section)
            trait_values.append(trait_value)
            
        return trait_values
        
    def _apply_environmental_effects(self, environment):
        """
        Apply environmental effects to the body cell
        
        Args:
            environment: The environment object
        """
        # Get environmental conditions
        conditions = environment.get_conditions_at(self.x, self.y)
        
        # Flow affects movement
        flow_rate = conditions["flow_rate"]
        if flow_rate > 0:
            # Add some movement in the flow direction (simplified to right/down)
            self.x += flow_rate * 0.5
            self.y += flow_rate * 0.2
            
            # Ensure within bounds
            self.x = max(0, min(environment.width, self.x))
            self.y = max(0, min(environment.height, self.y))
        
        # Cells slowly regenerate health when not severely damaged
        if self.health < 100 and self.damage_level < 50:
            self.health += self.regeneration_rate
            self.health = min(100, self.health)
            
        # Damaged cells consume more energy
        if self.damaged:
            self.energy -= 0.2 * self.damage_level / 100
            
        # Chance to recover from infection naturally
        if self.infected_by is not None and np.random.random() < self.infection_recovery_chance:
            self.clear_infection()
        
    def take_damage(self, amount):
        """
        Cell takes damage from an external source
        
        Args:
            amount (float): Amount of damage to take
            
        Returns:
            bool: True if the cell died from the damage
        """
        self.health -= amount
        self.damage_level += amount * 0.5
        self.damaged = True
        
        if self.health <= 0:
            self.is_alive = False
            return True
        return False
        
    def infect(self, infecting_organism):
        """
        Cell becomes infected by a virus or other pathogen
        
        Args:
            infecting_organism: The organism infecting this cell
            
        Returns:
            bool: True if infection was successful
        """
        # Check infection resistance - higher resistance means less chance of infection
        if np.random.random() < self.infection_resistance:
            return False
            
        # Increased chance of infection if not already infected
        if self.infected_by is None or np.random.random() < 0.2:  # Added chance to override existing infection
            self.infected_by = infecting_organism
            self.take_damage(10)  # Initial damage from infection
            # Change color to indicate infection (reddish tint)
            r, g, b = self.color
            self.color = (min(255, r + 50), max(0, g - 30), max(0, b - 30))
            
            # Add a small amount of additional damage to the cell
            # Much lower than before to prevent immediate death
            if hasattr(self.infected_by, 'virulence'):
                self.health -= self.infected_by.virulence * 1.5  # Reduced from 15
            
            return True
        return False
    
    def clear_infection(self):
        """Clear current infection and begin recovery"""
        if self.infected_by is not None:
            self.infected_by = None
            
            # Start recovery - restore original color gradually
            r, g, b = self.color
            self.color = (max(0, r - 30), min(255, g + 20), min(255, b + 20))
            
            # Slight health recovery
            self.health += 5
            self.health = min(100, self.health)
            
            # Reduce damage level
            self.damage_level = max(0, self.damage_level - 10)
            if self.damage_level == 0:
                self.damaged = False
    
    def interact(self, other_organism, environment):
        """
        Interact with another organism
        
        Args:
            other_organism: Another organism instance
            environment: The environment object
        """
        # Body cells don't initiate interactions, they respond to them
        pass
    
    def reproduce(self, environment):
        """
        Attempt to reproduce the body cell. Most body cells should not reproduce
        in the simulation, but this is included for stem cells or other special types.
        
        Args:
            environment: The simulation environment
            
        Returns:
            BodyCell: A new cell instance or None if reproduction fails
        """
        if not self.can_reproduce:
            print(f"{self.__class__.__name__} tried to reproduce but has can_reproduce=False!")
            return None
            
        # Energy cost for reproduction
        reproduction_cost = 60
        
        # Only reproduce if healthy
        if self.health < 80 or self.energy < 60:
            return None
            
        # Energy cost for reproduction
        self.energy -= reproduction_cost
        
        # Create child with slight mutations
        child_class = self.__class__
        child_x = self.x + environment.random.uniform(-10, 10)
        child_y = self.y + environment.random.uniform(-10, 10)
        
        # Ensure child is within bounds
        child_x = max(0, min(environment.width, child_x))
        child_y = max(0, min(environment.height, child_y))
        
        # Small variations in size and speed
        child_size = self.size * (1 + environment.random.uniform(-0.1, 0.1))
        child_speed = self.base_speed * (1 + environment.random.uniform(-0.1, 0.1))
        
        # Create the new cell
        return child_class(child_x, child_y, child_size, self.color, child_speed)
    
    def get_type(self):
        """Return the type of organism"""
        return "BodyCell"


class RedBloodCell(BodyCell):
    """
    Red Blood Cell (Erythrocyte) - Carries oxygen through the bloodstream
    Can be targets for certain bacteria and parasites
    """
    
    def __init__(self, x, y, size, color, speed):
        """Initialize a new red blood cell"""
        # Red blood cells are reddish
        color = (220, 40, 40)
        super().__init__(x, y, size, color, speed)
        self.oxygen_level = 100  # Full oxygen when created
        self.biconcave_ratio = 0.3  # For the distinctive biconcave shape
        
    def _apply_environmental_effects(self, environment):
        """Apply environmental effects to the red blood cell"""
        super()._apply_environmental_effects(environment)
        
        # Red blood cells move more with the flow than other cells
        conditions = environment.get_conditions_at(self.x, self.y)
        flow_rate = conditions["flow_rate"]
        
        # Additional flow effect
        self.x += flow_rate * 0.8
        self.y += flow_rate * 0.3
        
        # Ensure within bounds
        self.x = max(0, min(environment.width, self.x))
        self.y = max(0, min(environment.height, self.y))
        
        # Oxygen is gradually consumed
        self.oxygen_level -= 0.05
        
        # If it drops too low, we need to represent that the cell needs to
        # return to the lungs, but for simulation purposes we'll just refill it
        if self.oxygen_level < 20:
            self.oxygen_level = 100
            
    def render(self, screen, camera_x, camera_y, zoom):
        """
        Render the red blood cell as a biconcave disc
        
        Args:
            screen: Pygame screen to render on
            camera_x, camera_y: Camera position
            zoom: Zoom level
        """
        # Get screen dimensions
        screen_width, screen_height = screen.get_size()
        
        # Calculate screen position with proper centering
        screen_x = int((self.x - camera_x) * zoom + screen_width / 2)
        screen_y = int((self.y - camera_y) * zoom + screen_height / 2)
        
        # Skip rendering if off screen
        if (screen_x + self.size * zoom < 0 or screen_x - self.size * zoom > screen_width or
            screen_y + self.size * zoom < 0 or screen_y - self.size * zoom > screen_height):
            return
        
        # Calculate radius for screen
        radius = int(self.size * zoom)
        
        # Base color varies with oxygen level
        o2_factor = self.oxygen_level / 100
        red_value = int(120 + 100 * o2_factor)
        blue_value = int(20 + 20 * (1 - o2_factor))
        cell_color = (red_value, 40, blue_value)
        
        # Draw the main cell body
        pygame.draw.circle(screen, cell_color, (screen_x, screen_y), radius)
        
        # Draw the characteristic biconcave shape (indentation)
        indent_radius = int(radius * self.biconcave_ratio)
        indent_color = (min(255, red_value + 30), 50, blue_value)
        
        # Draw the indentations on both sides
        pygame.draw.circle(screen, indent_color, (screen_x, screen_y), indent_radius)
        
        # Draw a thin outline
        outline_color = (min(255, red_value + 20), 30, blue_value)
        pygame.draw.circle(screen, outline_color, (screen_x, screen_y), radius, 1)
        
        # If damaged, show visual indication
        if self.damaged:
            damage_color = (min(255, red_value + 50), 50, 50)
            damage_size = int(radius * (self.damage_level / 100))
            pygame.draw.circle(screen, damage_color, (screen_x, screen_y), damage_size)
    
    def get_type(self):
        """Return the type of organism"""
        return "RedBloodCell"
        
    def get_name(self):
        """Return the display name of the organism"""
        return "Red Blood Cell"


class EpithelialCell(BodyCell):
    """
    Epithelial Cell - Lines surfaces and cavities throughout the body
    Primary targets for respiratory viruses like Influenza and Rhinovirus
    """
    
    def __init__(self, x, y, size, color, speed):
        """Initialize a new epithelial cell"""
        # Epithelial cells are pinkish
        color = (230, 180, 180)
        super().__init__(x, y, size, color, speed)
        self.barrier_strength = 0.5  # Base barrier function
        self.adhesion_factor = 0.8   # Tends to stick to nearby cells
        
        # Epithelial cells are more stationary
        self.base_speed *= 0.3
        self.velocity = [self.velocity[0] * 0.3, self.velocity[1] * 0.3]
        
        # For polygon shape
        self.sides = 6  # Hexagonal
        self.rotation = np.random.uniform(0, 2 * np.pi)
        
        # Epithelial properties
        self.adhesion = 0.8  # High adhesion to other cells
        self.secretions = {
            "mucus": 0.0,  # Mucus production level
            "antimicrobial": 0.0  # Antimicrobial peptide production
        }
        
        # Epithelial cells have higher resistance to infection
        self.infection_resistance = 0.3
        self.regeneration_rate = 0.15  # Faster healing
        
        # Variable properties based on DNA
        trait_vals = self._decode_dna()
        self.barrier_strength += trait_vals[0] * 0.3  # Variation in barrier function
        self.secretions["mucus"] = trait_vals[1] * 0.5  # Variable mucus production
        self.secretions["antimicrobial"] = trait_vals[2] * 0.4  # Variable antimicrobial production
        
    def _apply_environmental_effects(self, environment):
        """Apply environmental effects to the epithelial cell"""
        super()._apply_environmental_effects(environment)
        
        # Epithelial cells are less affected by flow
        conditions = environment.get_conditions_at(self.x, self.y)
        
        # Temperature affects health
        temperature = conditions["temperature"]
        
        # Too high or too low temperature is damaging
        if temperature > 41 or temperature < 33:
            self.take_damage(0.1)
            
        # Epithelial cells regenerate barrier
        if self.barrier_strength < 100 and self.health > 60:
            self.barrier_strength += 0.2
            self.barrier_strength = min(100, self.barrier_strength)
    
    def render(self, screen, camera_x, camera_y, zoom):
        """
        Render the epithelial cell as a polygon
        
        Args:
            screen: Pygame screen to render on
            camera_x, camera_y: Camera position
            zoom: Zoom level
        """
        # Get screen dimensions
        screen_width, screen_height = screen.get_size()
        
        # Calculate screen position with proper centering
        screen_x = int((self.x - camera_x) * zoom + screen_width / 2)
        screen_y = int((self.y - camera_y) * zoom + screen_height / 2)
        
        # Skip rendering if off screen
        if (screen_x + self.size * zoom < 0 or screen_x - self.size * zoom > screen_width or
            screen_y + self.size * zoom < 0 or screen_y - self.size * zoom > screen_height):
            return
        
        # Calculate radius for screen
        radius = int(self.size * zoom)
        
        # Cell color varies with health
        health_factor = self.health / 100
        barrier_factor = self.barrier_strength / 100
        
        red_value = int(230)
        green_value = int(160 + 40 * health_factor)
        blue_value = int(160 + 40 * barrier_factor)
        
        cell_color = (red_value, green_value, blue_value)
        
        # Calculate polygon points
        points = []
        for i in range(self.sides):
            angle = self.rotation + (2 * np.pi * i / self.sides)
            x = screen_x + int(radius * np.cos(angle))
            y = screen_y + int(radius * np.sin(angle))
            points.append((x, y))
        
        # Draw the cell
        pygame.draw.polygon(screen, cell_color, points)
        
        # Draw outline
        pygame.draw.polygon(screen, (180, 130, 130), points, 1)
        
        # Draw nucleus (slightly offset from center)
        nucleus_x = screen_x + int(radius * 0.2)
        nucleus_y = screen_y - int(radius * 0.1)
        nucleus_radius = int(radius * 0.3)
        pygame.draw.circle(screen, (210, 150, 150), (nucleus_x, nucleus_y), nucleus_radius)
        
        # If infected, show visual indication
        if self.infected_by:
            infect_color = (200, 100, 100)
            pygame.draw.circle(screen, infect_color, (screen_x, screen_y), int(radius * 0.4))
        
        # If damaged, show visual indication
        if self.damaged:
            damage_factor = self.damage_level / 100
            damage_points = []
            for i in range(self.sides):
                angle = self.rotation + (2 * np.pi * i / self.sides)
                # Damaged cells have irregular shapes
                damage_radius = radius * (1 - damage_factor * 0.3 * (0.5 + 0.5 * np.sin(angle * 3)))
                x = screen_x + int(damage_radius * np.cos(angle))
                y = screen_y + int(damage_radius * np.sin(angle))
                damage_points.append((x, y))
                
            pygame.draw.polygon(screen, (230, 150, 150), damage_points, 1)
    
    def get_type(self):
        """Return the type of organism"""
        return "EpithelialCell"
        
    def get_name(self):
        """Return the display name of the organism"""
        return "Epithelial Cell"

    def reproduce(self, environment):
        """Epithelial cells should not reproduce in the simulation"""
        print(f"WARNING: EpithelialCell.reproduce() was called - these cells should not reproduce!")
        # Return None to indicate reproduction failed
        return None


class Platelet(BodyCell):
    """
    Platelet - Small cell fragments involved in blood clotting
    Respond to damage by aggregating
    """
    
    def __init__(self, x, y, size, color, speed):
        """Initialize a new platelet"""
        # Platelets are light purple
        color = (200, 180, 220)
        
        # Platelets are smaller than other cells
        size = size * 0.6
        
        super().__init__(x, y, size, color, speed)
        self.activated = False
        self.activation_time = 0
        self.aggregation_count = 0  # Number of other platelets it's connected to
        self.nearby_platelets = []  # References to nearby platelets
        
    def _apply_environmental_effects(self, environment):
        """Apply environmental effects to the platelet"""
        super()._apply_environmental_effects(environment)
        
        # Platelets move more with the flow than most cells
        conditions = environment.get_conditions_at(self.x, self.y)
        flow_rate = conditions["flow_rate"]
        
        # Additional flow effect
        self.x += flow_rate * 0.7
        self.y += flow_rate * 0.25
        
        # Ensure within bounds
        self.x = max(0, min(environment.width, self.x))
        self.y = max(0, min(environment.height, self.y))
        
        # If activated, track activation time
        if self.activated:
            self.activation_time += 1
            
            # If activated for too long, it's consumed
            if self.activation_time > 500:
                self.energy -= 0.5
                
            # Activated platelets aggregate and slow down
            if self.aggregation_count > 0:
                speed_reduction = min(0.9, self.aggregation_count * 0.2)
                self.velocity[0] *= (1 - speed_reduction)
                self.velocity[1] *= (1 - speed_reduction)
    
    def activate(self):
        """Activate the platelet (for clotting)"""
        if not self.activated:
            self.activated = True
            self.color = (220, 180, 220)  # Slightly brighter when activated
            
            # Activated platelets change shape and slow down
            self.base_speed *= 0.7
    
    def scan_for_platelets(self, organisms):
        """
        Scan for nearby platelets to potentially form aggregates
        
        Args:
            organisms (list): List of nearby organisms
        """
        if not self.activated:
            return
            
        self.nearby_platelets = []
        
        for org in organisms:
            if org.id == self.id:
                continue
                
            # Only care about other platelets
            if org.get_type() == "Platelet":
                # Calculate distance
                dx = self.x - org.x
                dy = self.y - org.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # If close enough and both activated, they can aggregate
                if distance < self.size * 4 and org.activated:
                    self.nearby_platelets.append(org)
                    
                    # Increment aggregation count if not already counting this platelet
                    if org.id not in [p.id for p in self.nearby_platelets]:
                        self.aggregation_count += 1
                        
                        # Aggregate platelets move toward each other
                        if len(self.nearby_platelets) < 5:  # Limit cluster size
                            # Move slightly toward each other
                            attraction = 0.2
                            self.x -= dx * attraction
                            self.y -= dy * attraction
    
    def render(self, screen, camera_x, camera_y, zoom):
        """
        Render the platelet
        
        Args:
            screen: Pygame screen to render on
            camera_x, camera_y: Camera position
            zoom: Zoom level
        """
        # Get screen dimensions
        screen_width, screen_height = screen.get_size()
        
        # Calculate screen position with proper centering
        screen_x = int((self.x - camera_x) * zoom + screen_width / 2)
        screen_y = int((self.y - camera_y) * zoom + screen_height / 2)
        
        # Skip rendering if off screen
        if (screen_x + self.size * zoom < 0 or screen_x - self.size * zoom > screen_width or
            screen_y + self.size * zoom < 0 or screen_y - self.size * zoom > screen_height):
            return
        
        # Calculate radius for screen
        radius = int(self.size * zoom)
        
        # Color depends on activation state
        if self.activated:
            # More purple when activated
            color = (220, 180, 220)
            if self.aggregation_count > 0:
                # More intense when aggregating
                color = (230, 170, 230)
        else:
            # Regular color when inactive
            color = self.color
        
        # Platelets are small and irregularly shaped
        if not self.activated:
            # Inactive platelets are more disc-shaped
            pygame.draw.circle(screen, color, (screen_x, screen_y), radius)
            pygame.draw.circle(screen, (180, 160, 200), (screen_x, screen_y), radius, 1)
        else:
            # Activated platelets extend pseudopodia (spiky)
            points = []
            num_points = 8
            for i in range(num_points):
                angle = 2 * np.pi * i / num_points
                # Vary radius to create spiky shape
                point_radius = radius * (1 + 0.4 * math.sin(angle * 4 + self.activation_time * 0.1))
                x = screen_x + int(point_radius * np.cos(angle))
                y = screen_y + int(point_radius * np.sin(angle))
                points.append((x, y))
            
            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, (180, 160, 200), points, 1)
        
        # If part of an aggregate, draw connections to nearby platelets
        if self.activated and self.aggregation_count > 0:
            for platelet in self.nearby_platelets:
                # Calculate other platelet's screen position with proper centering
                other_x = int((platelet.x - camera_x) * zoom + screen_width / 2)
                other_y = int((platelet.y - camera_y) * zoom + screen_height / 2)
                pygame.draw.line(screen, (210, 170, 210), (screen_x, screen_y), (other_x, other_y), 1)
    
    def get_type(self):
        """Return the type of organism"""
        return "Platelet"
        
    def get_name(self):
        """Return the display name of the organism"""
        return "Platelet" 