"""
White Blood Cell Module for Bio-Sim
Implements the Neutrophil class, representing immune system cells
"""

import numpy as np
from src.organisms.organism import Organism
import math
import time
import random
import pygame

class Neutrophil(Organism):
    """
    Neutrophil class representing immune system cells in the simulation.
    Neutrophils hunt and destroy foreign organisms like viruses and bacteria.
    """
    
    def __init__(self, x, y, size, color, speed, dna_length=120):
        """
        Initialize a neutrophil
        
        Args:
            x (float): Initial x position
            y (float): Initial y position
            size (float): Cell radius
            color (tuple): RGB color tuple
            speed (float): Base movement speed
            dna_length (int): Length of DNA sequence
        """
        super().__init__(x, y, size, color, speed, dna_length)
        
        # Initialize velocity components
        self.vx = 0.0
        self.vy = 0.0
        
        # Targeting properties
        self.target = None
        self.target_x = None
        self.target_y = None
        self.has_target = False
        self.target_memory = []
        self.detection_radius = 200  # Increased from 100 to allow detecting pathogens from further away
        self.chase_speed_multiplier = 1.5  # Increased from 1.2 to make pursuit faster
        self.attack_strength = 5.0  # Increased from 3.0 to make attacks more effective
        
        # Specialized flags
        self.base_speed = speed
        self.interaction_cooldown = 0
        
        # Neutrophil specific properties
        self.memory_capacity = 3  # Number of pathogen types it can recognize
        self.pathogen_memory = []  # List of pathogen types it recognizes
        self.target_organism = None  # Current target organism (new attribute used in updated methods)
        self.base_metabolism = 0.05  # Base metabolic rate
        self.target_lock_time = 0  # Time counter for maintaining focus on the current target
        self.target_lock_duration = 50  # How long to maintain focus on a target before considering switching
        
        # Modify properties based on DNA
        self._apply_dna_effects()
    
    def _apply_dna_effects(self):
        """Apply effects of the DNA sequence to the neutrophil's properties"""
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
        # More A: Better detection radius
        # More T: Stronger attack
        # More G: Better memory capacity
        # More C: More energy efficient
        
        self.detection_radius += base_counts['A'] * 50
        self.attack_strength += base_counts['T'] * 3
        self.memory_capacity += int(base_counts['G'] * 5)
        self.energy += base_counts['C'] * 30
    
    def _apply_environmental_effects(self, environment):
        """
        Apply environmental effects to the neutrophil
        
        Args:
            environment: The environment object
        """
        # Get environment variables for current position
        env_data = environment.get_conditions_at(self.x, self.y)
        
        # Neutrophils are optimized for body environment
        # and are less affected by environmental conditions
        
        # Temperature effect
        temp = env_data['temperature']
        if abs(temp - 37.0) > 5.0:  # Outside normal body temperature range
            self.health -= 0.2
        
        # Energy metabolism
        # Neutrophils naturally consume energy over time
        self.energy -= 0.05
    
    def _get_neural_network_inputs(self, environment):
        """
        Prepare inputs for the neural network with target information
        
        Args:
            environment: The environment object
            
        Returns:
            list: Input values for neural network (exactly 5 inputs)
        """
        # Initialize all inputs with defaults
        inputs = [
            self.x / environment.width,              # Normalized x position
            self.y / environment.height,             # Normalized y position
            self.energy / 100.0,                     # Normalized energy
            0.0,                                     # Default x direction to target (if no target)
            0.0                                      # Default y direction to target (if no target)
        ]
        
        # Add target information if we have a target
        if self.target:
            # Check if target is a dictionary (new structure)
            if isinstance(self.target, dict) and 'organism' in self.target:
                target_organism = self.target['organism']
                if hasattr(target_organism, 'is_alive') and target_organism.is_alive:
                    # Direction to target
                    dx = target_organism.x - self.x
                    dy = target_organism.y - self.y
                    distance = max(0.1, np.sqrt(dx**2 + dy**2))
                    
                    # Normalized direction (replace the default values)
                    inputs[3] = dx / distance
                    inputs[4] = dy / distance
            
            # Legacy support for direct organism reference    
            elif hasattr(self.target, 'is_alive') and self.target.is_alive:
                # Direction to target
                dx = self.target.x - self.x
                dy = self.target.y - self.y
                distance = max(0.1, np.sqrt(dx**2 + dy**2))
                
                # Normalized direction (replace the default values)
                inputs[3] = dx / distance
                inputs[4] = dy / distance
        
        return inputs
    
    def _apply_decision(self, decision, environment):
        """
        Apply the neural network decision to the organism's state
        
        Args:
            decision (list): Output from neural network
            environment: The environment object
        """
        # Extract movement direction from decision
        dx = decision[0]
        dy = decision[1]
        
        # If we have a target, adjust movement direction
        if self.target is not None:
            # Initialize target organism and distance
            target_organism = None
            target_distance = 0
            
            # Handle target based on its type
            if isinstance(self.target, dict) and 'organism' in self.target:
                # New dictionary format
                target_organism = self.target['organism']
                target_distance = self.target['distance']
            elif hasattr(self.target, 'x') and hasattr(self.target, 'y'):
                # Legacy direct organism reference
                target_organism = self.target
                target_distance = np.sqrt((target_organism.x - self.x)**2 + (target_organism.y - self.y)**2)
            
            # Only proceed if we have a valid target organism
            if target_organism is not None and hasattr(target_organism, 'is_alive') and target_organism.is_alive:
                # Calculate direction to target
                target_dx = target_organism.x - self.x
                target_dy = target_organism.y - self.y
                
                # Normalize direction
                target_dist = np.sqrt(target_dx**2 + target_dy**2)
                
                if target_dist > 0:
                    target_dx /= target_dist
                    target_dy /= target_dist
                    
                    # Blend neural network decision with target direction
                    # The closer to the target, the more we follow neural network decision
                    blend_factor = min(1.0, target_dist / 100)
                    dx = dx * blend_factor + target_dx * (1 - blend_factor)
                    dy = dy * blend_factor + target_dy * (1 - blend_factor)
                    
                    # Normalize again
                    move_dist = np.sqrt(dx**2 + dy**2)
                    if move_dist > 0:
                        dx /= move_dist
                        dy /= move_dist
        
        # Apply movement
        self.x += dx * self.base_speed
        self.y += dy * self.base_speed
        
        # Boundary checking
        if self.x < 0 or self.x > environment.width:
            dx *= -1
        if self.y < 0 or self.y > environment.height:
            dy *= -1
            
        # Ensure within bounds
        self.x = max(0, min(environment.width, self.x))
        self.y = max(0, min(environment.height, self.y))
        
        # Consume energy for movement
        movement_cost = (abs(dx) + abs(dy)) * 0.05
        self.energy -= movement_cost
    
    def scan_for_targets(self, organisms, environment):
        """
        Scan for potential threat organisms within detection radius
        
        Args:
            organisms: List of organisms in the simulation
            environment: The environment object containing environmental data
        """
        if not self.is_alive:
            return
            
        # Get all organisms within detection radius
        max_scan_distance = self.detection_radius  # Use the instance's detection radius
        nearby_organisms = []
        
        for organism in organisms:
            # Skip self
            if organism.id == self.id:
                continue
                
            # Calculate distance
            dx = self.x - organism.x
            dy = self.y - organism.y
            
            # Account for world wrapping when calculating distance
            world_width = environment.width
            world_height = environment.height
            
            # Check for shorter path across world boundaries
            if abs(dx) > world_width / 2:
                dx = -1 * np.sign(dx) * (world_width - abs(dx))
            if abs(dy) > world_height / 2:
                dy = -1 * np.sign(dy) * (world_height - abs(dy))
                
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Only include organisms within detection radius
            if distance <= max_scan_distance:
                nearby_organisms.append(organism)
        
        # If we currently have a target, increment lock time
        if self.target:
            self.target_lock_time += 1
            
            # If we've maintained focus on this target for long enough, allow switching targets
            if self.target_lock_time >= self.target_lock_duration:
                self.target_lock_time = 0
                self.target = None  # Clear current target to allow finding a new one
                
            # Otherwise, check if current target is still in range
            else:
                current_target_in_range = False
                for organism in nearby_organisms:
                    if self.target.get('organism') == organism:
                        current_target_in_range = True
                        break
                
                # If current target not in range, allow finding a new one
                if not current_target_in_range:
                    self.target = None
                    self.target_lock_time = 0
                else:
                    # Current target still valid, keep it
                    return
        
        # Find the highest threat target
        self.target = self._select_target(nearby_organisms, environment)
        
        # If we found a new target, reset lock time
        if self.target:
            self.target_lock_time = 0
    
    def _sense_environment(self, environment):
        """
        Find nearby organisms that could be potential targets.
        This method doesn't actually scan the environment itself (as it doesn't have 
        direct access to all organisms) but will return any organisms passed to it
        through other methods like scan_for_targets.
        
        Args:
            environment: The environment object containing environmental data
            
        Returns:
            list: An empty list as this method can't directly access organisms
        """
        # We can't directly access organisms from the environment
        # This method is meant to be used with organisms provided by the Simulation class
        # For now, return an empty list
        return []
        
    def update(self, environment):
        """
        Update the neutrophil's state based on its environment and internal state
        
        Args:
            environment: The environment object containing state information
        """
        if not self.is_alive:
            return
            
        old_x, old_y = self.x, self.y
        
        # Since we can't directly sense the environment for other organisms,
        # we have to rely on neural network for movement
        inputs = self._get_neural_network_inputs(environment)
        decision = self.neural_network_decision(inputs)
        self._apply_decision(decision, environment)
        
        # If we have a target, move towards it with increased urgency
        if self.target is not None:
            # Get target organism - handle both dictionary and direct organism cases
            target_organism = None
            if isinstance(self.target, dict) and 'organism' in self.target:
                target_organism = self.target.get('organism')
            else:
                # If target is already the organism itself
                target_organism = self.target
                
            if target_organism and hasattr(target_organism, 'is_alive') and target_organism.is_alive:
                dx = target_organism.x - self.x
                dy = target_organism.y - self.y
            
            # Account for world wrapping when calculating distance
            world_width = environment.width
            world_height = environment.height
            
            # Check for shorter path across world boundaries
            if abs(dx) > world_width / 2:
                dx = -1 * np.sign(dx) * (world_width - abs(dx))
            if abs(dy) > world_height / 2:
                dy = -1 * np.sign(dy) * (world_height - abs(dy))
            
            # Calculate distance to target
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 0:
                # Normalize direction
                dx /= distance
                dy /= distance
                
                # Set velocity based on direction and speed with chase multiplier
                chase_speed = self.base_speed * self.chase_speed_multiplier
                
                # More aggressive pursuit when close to target
                if distance < 50:
                    chase_speed *= 1.2  # Extra speed boost when close
                
                self.vx = dx * chase_speed
                self.vy = dy * chase_speed
                
                # Add small random movement component (reduced for more direct pursuit)
                self.vx += np.random.normal(0, 0.1)
                self.vy += np.random.normal(0, 0.1)
            else:
                # Target is no longer valid, clear it
                self.target = None
        else:
            # Random movement with inertia when no target is present
            self.vx += np.random.normal(0, 0.3)
            self.vy += np.random.normal(0, 0.3)
            
            # Dampen velocity for stability
            self.vx *= 0.95
            self.vy *= 0.95
            
        # Apply maximum speed constraint
        speed = math.sqrt(self.vx*self.vx + self.vy*self.vy)
        if speed > self.base_speed:
            self.vx = (self.vx / speed) * self.base_speed
            self.vy = (self.vy / speed) * self.base_speed
            
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Boundary wrapping
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
        
        # Consume nutrients from environment based on distance moved
        distance_moved = math.sqrt((self.x - old_x)**2 + (self.y - old_y)**2)
        energy_consumed = distance_moved * 0.05
        self.energy = max(0, self.energy - energy_consumed)
        
        # Get nutrients from environment
        nutrients = environment.consume_nutrients(self.x, self.y, self.size * 0.1)
        self.energy = min(100, self.energy + nutrients * 0.5)
        
        # Check if organism should die
        self._check_vitals()
    
    def reproduce(self, environment):
        """
        Attempt to reproduce based on energy level
        
        Args:
            environment: The environment object
            
        Returns:
            Neutrophil: A new neutrophil instance or None if reproduction fails
        """
        # Check population cap from environment config
        max_organisms = environment.config.get("simulation_settings", {}).get("max_organisms", 0)
        if max_organisms > 0:
            # Estimate organism density to prevent overpopulation
            organism_density = max_organisms / (environment.width * environment.height)
            local_area = np.pi * 150 * 150  # Circular area of radius 150
            estimated_local_count = organism_density * local_area
            
            # If estimated local population is high, reduce reproduction chance
            if estimated_local_count > 30:  # Arbitrary threshold for WBCs
                if np.random.random() < 0.9:  # 90% chance to skip reproduction in dense areas
                    return None
        
        # Neutrophils reproduce less frequently
        if (self.energy > 140 and  # Increased energy threshold
            self.is_alive and 
            np.random.random() < 0.0005):  # Even lower reproduction rate
            
            # Create child with mutation in DNA
            child_dna = self.dna.copy()
            if np.random.random() < environment.config['simulation_settings']['mutation_rate']:
                mutation_idx = np.random.randint(0, len(child_dna))
                bases = ['A', 'T', 'G', 'C']
                child_dna[mutation_idx] = bases[np.random.randint(0, 4)]
            
            # Slightly mutate color
            r, g, b = self.color
            color_mutation = 5  # Less variation than bacteria
            new_color = (
                max(0, min(255, r + np.random.randint(-color_mutation, color_mutation))),
                max(0, min(255, g + np.random.randint(-color_mutation, color_mutation))),
                max(0, min(255, b + np.random.randint(-color_mutation, color_mutation)))
            )
            
            # Create child with random position deviation
            offset = 20
            new_x = max(0, min(environment.width, self.x + np.random.randint(-offset, offset)))
            new_y = max(0, min(environment.height, self.y + np.random.randint(-offset, offset)))
            
            # Pass memory to child
            child = Neutrophil(
                new_x, 
                new_y,
                self.size * np.random.uniform(0.95, 1.05),  # Less size variation
                new_color,
                self.base_speed * np.random.uniform(0.95, 1.05)  # Less speed variation
            )
            
            # Copy DNA to child
            child.dna = child_dna
            
            # Transfer pathogen memory to child (immune memory)
            child.pathogen_memory = self.pathogen_memory.copy()
            
            # Consume energy for reproduction
            self.energy -= 80  # Higher energy cost
            
            return child
        
        return None
    
    def interact(self, other_organism, environment):
        """
        Interact with another organism, potentially attacking it
        
        Args:
            other_organism: Another organism instance
            environment: The environment object
            
        Returns:
            bool: True if interaction occurred, False otherwise
        """
        # Only interact with pathogens
        if (other_organism.get_type() in ["virus", "bacteria"] and 
            other_organism.is_alive):
            
            # Check if close enough to attack
            dx = other_organism.x - self.x
            dy = other_organism.y - self.y
            distance = np.sqrt(dx**2 + dy**2)
            
            if distance <= self.size + other_organism.size + 2:
                # Attack the pathogen
                other_organism.health -= self.attack_strength
                
                # Use energy for attack
                self.energy -= 1.0
                
                # Remember this pathogen type
                if len(self.pathogen_memory) < self.memory_capacity:
                    if other_organism.id not in self.pathogen_memory:
                        self.pathogen_memory.append(other_organism.id)
                
                # NEW: Immune cells can be damaged during phagocytosis/attack
                # This models the biological reality that immune cells can be damaged 
                # by toxins, enzymes, or molecular mechanisms from pathogens
                damage_chance = 0.25  # 25% chance of taking damage
                
                # Viruses have higher chance of damaging immune cells
                if other_organism.get_type() == "virus":
                    damage_chance = 0.35
                
                # Some bacteria are more dangerous to immune cells
                if hasattr(other_organism, 'get_name'):
                    pathogen_name = other_organism.get_name()
                    if pathogen_name in ["Staphylococcus", "Salmonella"]:
                        damage_chance = 0.4
                
                # Apply damage if the random check passes
                if environment.random.random() < damage_chance:
                    damage_amount = environment.random.uniform(0.5, 2.0)
                    self.health -= damage_amount
                    
                    # Visual indication of damage could be added here
                    
                return True
                
        return False
    
    def get_type(self):
        """Return the type of organism"""
        return "neutrophil"

    def _select_target(self, organisms, environment):
        """
        Select the highest threat target from a list of potential target organisms
        
        Args:
            organisms (list): List of nearby organisms
            environment: The environment object
            
        Returns:
            dict: Dictionary containing the selected target organism and threat level, or None if no suitable target found
        """
        threat_scores = []
        
        for organism in organisms:
            # Skip other neutrophils, body cells, and dead organisms
            org_type = organism.get_type().lower()
            if "blood_cell" in org_type or "body" in org_type or not organism.is_alive:
                continue
                
            # Calculate base threat level
            threat_level = 0
            
            # Viruses are high threats
            if "virus" in org_type:
                threat_level += 8  # Increased from 5
                
                # Specific virus types may have different threat levels
                if "influenza" in org_type:
                    threat_level += 4  # Increased from 3
                elif "rhino" in org_type:  # Rhinovirus
                    threat_level += 3  # Increased from 2
            
            # Bacteria vary in threat level
            elif "bacteria" in org_type:
                # Beneficial bacteria are not threats
                if "beneficial" in org_type:
                    continue
                    
                # Basic bacteria threat
                threat_level += 5  # Increased from 3
                
                # Specific bacteria types may have different threat levels
                if "streptococcus" in org_type:
                    threat_level += 3  # Increased from 2
                if "ecoli" in org_type:
                    threat_level += 4  # Added specific threat for EColi
                if "staphylococcus" in org_type:
                    threat_level += 5  # Added specific threat for Staphylococcus
                if "salmonella" in org_type:
                    threat_level += 5  # Added specific threat for Salmonella
            
            # Skip if not a threat
            if threat_level == 0:
                continue
                
            # Calculate distance
            dx = self.x - organism.x
            dy = self.y - organism.y
            
            # Account for world wrapping
            world_width = environment.width
            world_height = environment.height
            
            # Check for shorter path across world boundaries
            if abs(dx) > world_width / 2:
                dx = -1 * np.sign(dx) * (world_width - abs(dx))
            if abs(dy) > world_height / 2:
                dy = -1 * np.sign(dy) * (world_height - abs(dy))
                
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Calculate final threat score - prefer closer threats
            # Modified to give more weight to proximity for faster response
            proximity_factor = max(0, 1 - distance / self.detection_radius)
            threat_score = threat_level * (proximity_factor ** 1.5)  # Increased proximity weight
            
            # Add health factor - prioritize weaker pathogens that can be eliminated quickly
            if hasattr(organism, 'health'):
                health_factor = 1.0
                if organism.health < 50:
                    health_factor = 1.3  # Prefer targeting already weakened organisms
                threat_score *= health_factor
            
            # Add to threat scores
            threat_scores.append({
                'organism': organism,
                'threat': threat_score,
                'distance': distance,
                'type': organism.get_type()
            })
            
        # Sort threats by score (highest first)
        if threat_scores:
            threat_scores.sort(key=lambda x: x['threat'], reverse=True)
            
            # Return the highest threat organism
            return threat_scores[0]
        
        return None

class Macrophage(Neutrophil):
    """
    Macrophage - Advanced phagocyte that engulfs pathogens and debris
    Specialized in detecting and destroying antibody-marked viruses
    """
    
    def __init__(self, x, y, size=10, color=(150, 150, 220), speed=0.5):
        """Initialize macrophage with specialized properties"""
        super().__init__(x, y, size, color, speed)
        self.phagocytosis_radius = self.size * 2.0  # Radius for engulfing pathogens
        self.engulfed_pathogens = []  # List to store engulfed pathogens
        self.digesting = False  # Whether currently digesting pathogens
        self.max_digestion_time = 80  # How long it takes to digest engulfed pathogens
        self.digestion_time = 0  # Current digestion time
        self.max_engulf_capacity = 5  # Maximum number of pathogens that can be engulfed at once
        self.detection_radius = 250  # Enhanced detection range
        self.chase_speed_multiplier = 1.7  # Faster chase speed
        self.attack_range = self.size * 1.8  # Increased attack range
        self.structure = "cell"
        self.type = "Macrophage"
        self.color = color  # Use the passed color
        
        # Define potential targets
        self.potential_targets = ["Bacteria", "Virus", "DamagedCell", "DeadCell"]
        
        # Initialize memory for remembering encountered pathogens
        self.memory = []
        
        # Enhanced properties for antibody marked viruses
        self.antibody_detection_bonus = 1.5  # Bonus to detection radius for marked viruses
        self.marked_target_speed_multiplier = 2.0  # Extra speed when chasing marked targets
        self.marked_damage_multiplier = 2.0  # Extra damage to marked targets

    def update(self, environment):
        """
        Update the Macrophage's state
        
        Args:
            environment: The environment object
        """
        # Handle digestion process
        if self.digesting:
            self.digestion_time += 1
            
            # Slow down while digesting
            self.speed = self.base_speed * 0.8
            
            # If digestion complete
            if self.digestion_time >= self.max_digestion_time:
                # Gain energy from digested pathogens
                self.energy += len(self.engulfed_pathogens) * 30
                
                # Clear engulfed pathogens
                self.engulfed_pathogens.clear()
                self.digesting = False
                self.digestion_time = 0
                
                # Return to normal speed
                self.speed = self.base_speed
        
        # Speed up when chasing a marked target
        if self.target and hasattr(self.target, 'antibody_marked') and self.target.antibody_marked:
            self.speed = self.base_speed * self.marked_target_speed_multiplier
        elif self.target:
            self.speed = self.base_speed * self.chase_speed_multiplier
        else:
            self.speed = self.base_speed
            
        # Call parent update
        super().update(environment)
        
    def scan_for_targets(self, organisms, environment):
        """
        Scan for targets with strong preference for antibody-marked viruses
        
        Args:
            organisms: List of nearby organisms to scan
            environment: The environment object
            
        Returns:
            The target organism if found, None otherwise
        """
        # Use provided organisms instead of fetching from environment
        nearby_organisms = organisms
        
        if not nearby_organisms:
            return None
            
        # Calculate threat scores
        threats = []
        for organism in nearby_organisms:
            # Skip self, dead organisms, and non-threats
            if organism == self or not organism.is_alive:
                continue
                
            # Get the organism type, using methods or attributes as available
            organism_type = ""
            if hasattr(organism, 'get_type'):
                organism_type = organism.get_type().capitalize()
            elif hasattr(organism, 'get_name'):
                organism_type = organism.get_name()
            elif hasattr(organism, 'type'):
                organism_type = organism.type
                
            # Initialize is_potential_target to False
            is_potential_target = False
            
            for target_type in self.potential_targets:
                if target_type in organism_type:
                    is_potential_target = True
                    break
            
            if not is_potential_target:
                continue
            
            # Calculate distance
            dx = organism.x - self.x
            dy = organism.y - self.y
            distance = (dx**2 + dy**2)**0.5
            
            # Skip if beyond detection radius
            if distance > self.detection_radius:
                continue
            
            # Base threat score on proximity and type
            threat_score = self.detection_radius / max(1, distance)
            
            # Increase threat for recognized targets
            if "virus" in organism_type.lower():
                threat_score *= 2.5
                
                # Additional weighting for specific virus types
                if "influenza" in organism_type.lower():
                    threat_score *= 1.5
                if "rhinovirus" in organism_type.lower():
                    threat_score *= 1.5
                    
                # Antibody marked viruses are less of a priority (already handled)
                if hasattr(organism, 'antibody_marked') and organism.antibody_marked:
                    threat_score *= 0.3
                    
            # Increase threat for remembered targets
            if id(organism) in self.memory:
                threat_score *= 2.0
                
            # Increase threat if organism is damaged
            if hasattr(organism, 'health') and hasattr(organism, 'max_health') and organism.health < organism.max_health * 0.7:
                threat_score *= 1.3
                
            threats.append((organism, threat_score))
            
        # No threats found
        if not threats:
            return None
            
        # Sort by threat score (highest first)
        threats.sort(key=lambda x: x[1], reverse=True)
        
        # Select the highest threat
        target = threats[0][0]
        
        # Increase activation level if our target is a virus
        full_target_type = ""
        if hasattr(target, 'type'):
            full_target_type = target.type
        elif hasattr(target, 'get_type') and callable(getattr(target, 'get_type')):
            full_target_type = target.get_type()
            
        if "virus" in full_target_type.lower():
            self.activation_level += 2.0
            
        # Set target and return
        self.target = target
        self.target_visual_indicator = full_target_type
        
        return target
        
    def interact(self, organism, environment):
        """
        Interact with another organism, potentially engulfing it
        
        Args:
            organism: The organism to interact with
            environment: The environment object
            
        Returns:
            bool: Whether the interaction happened
        """
        # Skip if already at capacity
        if len(self.engulfed_pathogens) >= self.max_engulf_capacity:
            return False
            
        # Calculate distance
        dx = organism.x - self.x
        dy = organism.y - self.y
        distance = (dx**2 + dy**2)**0.5
        
        # Check if within engulfing range
        if distance <= self.phagocytosis_radius:
            # Higher success rate for antibody-marked viruses
            engulf_chance = 0.6  # Base chance
            damage_amount = self.attack_strength
            
            # Modify for different target types
            if hasattr(organism, 'antibody_marked') and organism.antibody_marked:
                engulf_chance = 0.95  # Almost certain success for marked viruses
                damage_amount *= self.marked_damage_multiplier
                
            elif hasattr(organism, 'type') and "Virus" in organism.type:
                engulf_chance = 0.4  # Harder to engulf unmarked viruses
                
            elif hasattr(organism, 'type') and "Bacteria" in organism.type:
                engulf_chance = 0.7  # Easier to engulf bacteria
                
            elif hasattr(organism, 'type') and "DamagedCell" in organism.type:
                engulf_chance = 0.8  # Easy to clean up damaged cells
            
            # Handle organisms that use get_type() instead of type attribute
            elif hasattr(organism, 'get_type'):
                organism_type = organism.get_type()
                if "virus" in organism_type.lower():
                    engulf_chance = 0.4
                elif "bacteria" in organism_type.lower():
                    engulf_chance = 0.7
                elif "damaged" in organism_type.lower():
                    engulf_chance = 0.8
            
            # Try to engulf
            if random.random() < engulf_chance:
                # Apply damage first
                if hasattr(organism, 'health'):
                    organism.health -= damage_amount
                    
                # If organism dies from this damage, engulf it
                if not organism.is_alive:
                    # Add to engulfed list
                    self.engulfed_pathogens.append({
                        "type": organism.type,
                        "size": organism.size
                    })
                    
                    # Start digestion if this is the first engulfed pathogen
                    if not self.digesting:
                        self.digesting = True
                        self.digestion_time = 0
                    
                    return True
            else:
                # Damage even if engulfing fails
                if hasattr(organism, 'health'):
                    organism.health -= damage_amount * 0.5
                    
        return False
        
    def render(self, screen, camera_x, camera_y, zoom):
        """
        Render the Macrophage on the screen
        
        Args:
            screen: pygame screen surface
            camera_x (float): Camera x position
            camera_y (float): Camera y position
            zoom (float): Zoom level
        """
        if not self.is_alive:
            return
        
        # Calculate screen position
        screen_x = int((self.x - camera_x) * zoom + screen.get_width() / 2)
        screen_y = int((self.y - camera_y) * zoom + screen.get_height() / 2)
        
        # Skip if off screen
        if (screen_x < -50 or screen_x > screen.get_width() + 50 or
            screen_y < -50 or screen_y > screen.get_height() + 50):
            return
        
        # Draw the main Macrophage body
        radius = max(2, int(self.size * zoom))
        
        # Base color varies by digestion state
        if self.digesting:
            # Darker and more purple when digesting
            fill_color = (130, 100, 220)
            digestion_progress = self.digestion_time / self.max_digestion_time
            # Pulse effect during digestion
            pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.25 + 0.5
            fill_color = (
                int(fill_color[0] * (0.8 + pulse * 0.2)),
                int(fill_color[1] * (0.8 + pulse * 0.2)),
                int(fill_color[2] * (0.8 + pulse * 0.2))
            )
        else:
            fill_color = self.color
            
        # Draw main cell body
        pygame.draw.circle(screen, fill_color, (screen_x, screen_y), radius)
        
        # Draw pseudopods (little arm-like extensions)
        num_pseudopods = 8
        pseudopod_length = int(radius * 0.3)
        for i in range(num_pseudopods):
            angle = i * (2 * math.pi / num_pseudopods)
            
            # Add some wiggle to the pseudopods
            wiggle = math.sin(pygame.time.get_ticks() * 0.01 + i) * 20
            
            # Pseudopod position
            pseudopod_x = screen_x + int((radius + pseudopod_length) * math.cos(angle + wiggle * 0.01))
            pseudopod_y = screen_y + int((radius + pseudopod_length) * math.sin(angle + wiggle * 0.01))
            
            # Draw pseudopod
            pygame.draw.line(
                screen,
                fill_color,
                (screen_x + int(radius * math.cos(angle)), screen_y + int(radius * math.sin(angle))),
                (pseudopod_x, pseudopod_y),
                max(1, int(radius * 0.2))
            )
            
        # Show engulfed pathogens as smaller circles inside
        if self.engulfed_pathogens:
            # Draw small circles inside to represent engulfed pathogens
            for i, pathogen in enumerate(self.engulfed_pathogens):
                # Position inside the cell
                angle = i * (2 * math.pi / len(self.engulfed_pathogens))
                offset = radius * 0.5
                
                pathogen_x = screen_x + int(offset * math.cos(angle))
                pathogen_y = screen_y + int(offset * math.sin(angle))
                
                # Determine color based on pathogen type
                if "Virus" in pathogen["type"]:
                    pathogen_color = (150, 50, 50)  # Red for viruses
                elif "Bacteria" in pathogen["type"]:
                    pathogen_color = (50, 150, 50)  # Green for bacteria
                else:
                    pathogen_color = (100, 100, 100)  # Gray for others
                    
                # Draw engulfed pathogen
                pygame.draw.circle(
                    screen,
                    pathogen_color,
                    (pathogen_x, pathogen_y),
                    max(1, int(pathogen["size"] * zoom * 0.3))
                )


class TCell(Neutrophil):
    """
    T-Cell that targets specific pathogens
    Fires antibodies to mark viruses for destruction by other immune cells
    """
    
    def __init__(self, x, y, size=8, color=(100, 180, 255), speed=0.8):
        """Initialize T-Cell with specialized properties"""
        super().__init__(x, y, size, color, speed)
        self.activation_level = 0
        self.activation_threshold = 50
        self.memory = {}  # remembers pathogens
        self.type = "TCell"
        self.structure = "cell"
        self.attack_range = self.size * 1.5
        self.attack_strength = 5.0
        self.max_attack_cooldown = 15
        self.detection_radius = 220
        self.chase_speed_multiplier = 1.8
        self.memory_duration = 300  # How long to remember a pathogen
        self.color = color  # Use the passed color
        self.attack_cooldown = 0
        self.potential_targets = ["Virus", "Influenza", "Rhinovirus", "Staphylococcus", "Salmonella"]
        self.active_color = (50, 150, 255)  # Color when activated
        self.target_visual_indicator = None
        
        # Antibody properties
        self.antibody_production_cooldown = 0
        self.max_antibody_cooldown = 25  # Time between antibody production
        self.antibody_energy_cost = 15
        self.antibody_range = self.detection_radius * 0.8  # Slightly less than detection range
        self.antibody_strength = 0.3  # Initial antibody level when marking

    def update(self, environment):
        """
        Update the T-Cell's state
        
        Args:
            environment: The environment object
        """
        # Decrease activation if activated
        if self.activation_level > 0:
            self.activation_level -= 0.1
            
        # Increase speed based on activation
        if self.activation_level > self.activation_threshold:
            self.color = self.active_color
            self.speed = self.base_speed * self.chase_speed_multiplier * 1.2
        else:
            self.color = (100, 180, 255)
            self.speed = self.base_speed
            
        # Decrease attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        # Decrease antibody production cooldown
        if self.antibody_production_cooldown > 0:
            self.antibody_production_cooldown -= 1
            
        # Update memory - remove expired entries
        expired_targets = []
        for target_id, memory_data in self.memory.items():
            memory_data["time"] -= 1
            if memory_data["time"] <= 0:
                expired_targets.append(target_id)
                
        for target_id in expired_targets:
            del self.memory[target_id]
            
        # If we have a target and it's a virus, try to create antibodies
        if (self.target and 
            self.target.is_alive and 
            "Virus" in self.target.type and
            self.antibody_production_cooldown <= 0 and
            self.energy >= self.antibody_energy_cost and
            self.activation_level >= self.activation_threshold):
            
            # Calculate distance to target
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            distance = (dx**2 + dy**2)**0.5
            
            # If within antibody range, fire antibodies
            if distance <= self.antibody_range:
                self._fire_antibodies(self.target)
                
        # Call parent update
        super().update(environment)
        
    def _fire_antibodies(self, target_organism):
        """
        Fire antibodies at the target organism
        
        Args:
            target_organism: The organism to mark with antibodies
        
        Returns:
            bool: Whether antibodies were successfully fired
        """
        # Check if the target is a virus and has the mark_with_antibodies method
        if not hasattr(target_organism, 'mark_with_antibodies'):
            return False
            
        # Mark the target with antibodies
        success = target_organism.mark_with_antibodies(self.type, self.antibody_strength)
        
        if success:
            # Apply cooldown and energy cost
            self.antibody_production_cooldown = self.max_antibody_cooldown
            self.energy -= self.antibody_energy_cost
            
            # Add the target to memory
            self.memory[id(target_organism)] = {
                "type": target_organism.type,
                "time": self.memory_duration,
                "last_x": target_organism.x,
                "last_y": target_organism.y
            }
            
            # Increase activation level - we've detected a threat
            self.activation_level += 10
            
            return True
        return False
    
    def scan_for_targets(self, organisms, environment):
        """
        Scan for targets in the environment and prioritize threats.
        
        Args:
            organisms: List of nearby organisms to scan
            environment: The environment object
            
        Returns:
            The target organism if found, None otherwise
        """
        # Use provided organisms instead of fetching from environment
        nearby_organisms = organisms
        
        if not nearby_organisms:
            return None
            
        # Calculate threat scores
        threats = []
        for organism in nearby_organisms:
            # Skip self, dead organisms, and non-threats
            if organism == self or not organism.is_alive:
                continue
                
            # Check if organism is a potential target
            is_potential_target = False
            
            # Get the organism type, using methods or attributes as available
            organism_type = ""
            if hasattr(organism, 'get_type'):
                organism_type = organism.get_type().capitalize()
            elif hasattr(organism, 'get_name'):
                organism_type = organism.get_name()
            elif hasattr(organism, 'type'):
                organism_type = organism.type
                
            for target_type in self.potential_targets:
                if target_type in organism_type:
                    is_potential_target = True
                    break
            
            if not is_potential_target:
                continue
                
            # Calculate distance
            dx = organism.x - self.x
            dy = organism.y - self.y
            distance = (dx**2 + dy**2)**0.5
            
            # Skip if beyond detection radius
            if distance > self.detection_radius:
                continue
            
            # Base threat score on proximity and type
            threat_score = self.detection_radius / max(1, distance)
            
            # Increase threat for recognized targets
            if "Virus" in organism_type:
                threat_score *= 2.5
                
                # Additional weighting for specific virus types
                if "Influenza" in organism_type:
                    threat_score *= 1.5
                if "Rhinovirus" in organism_type:
                    threat_score *= 1.5
                    
                # Antibody marked viruses are less of a priority (already handled)
                if hasattr(organism, 'antibody_marked') and organism.antibody_marked:
                    threat_score *= 0.3
                    
            # Increase threat for remembered targets
            if id(organism) in self.memory:
                threat_score *= 2.0
                
            # Increase threat if organism is damaged
            if hasattr(organism, 'health') and hasattr(organism, 'max_health') and organism.health < organism.max_health * 0.7:
                threat_score *= 1.3
                
            threats.append((organism, threat_score))
            
        # No threats found
        if not threats:
            return None
            
        # Sort by threat score (highest first)
        threats.sort(key=lambda x: x[1], reverse=True)
        
        # Select the highest threat
        target = threats[0][0]
        
        # Increase activation level if our target is a virus
        if "Virus" in target.type:
            self.activation_level += 2.0
            
        # Set target and return
        self.target = target
        self.target_visual_indicator = target.type
        
        return target
        
    def interact(self, organism, environment):
        """
        Interact with another organism
        
        Args:
            organism: The organism to interact with
            environment: The environment object
            
        Returns:
            bool: Whether the interaction happened
        """
        # Skip if cooling down from attack
        if self.attack_cooldown > 0:
            return False
            
        # Check if organism is a target type
        is_target = False
        for target_type in self.potential_targets:
            # Check if organism has type attribute or get_type method
            if hasattr(organism, 'type'):
                if target_type in organism.type:
                    is_target = True
                    break
            elif hasattr(organism, 'get_type'):
                if target_type in organism.get_type():
                    is_target = True
                    break
                
        if not is_target:
            return False
            
        # Calculate distance
        dx = organism.x - self.x
        dy = organism.y - self.y
        distance = (dx**2 + dy**2)**0.5
        
        # If within attack range, attack
        if distance <= self.attack_range:
            # Increase activation on successful attack
            self.activation_level += 5.0
            
            # Double damage for active T-Cells against targets
            damage_multiplier = 2.0 if self.activation_level >= self.activation_threshold else 1.0
            
            # Apply damage to target
            if hasattr(organism, 'health'):
                # Double damage to virus targets
                if "Virus" in organism.type:
                    organism.health -= self.attack_strength * damage_multiplier * 2.0
                else:
                    organism.health -= self.attack_strength * damage_multiplier
                    
            # Add to memory
            self.memory[id(organism)] = {
                "type": organism.type,
                "time": self.memory_duration,
                "last_x": organism.x,
                "last_y": organism.y
            }
            
            # Set cooldown
            self.attack_cooldown = max(5, self.max_attack_cooldown - int(self.activation_level / 10))
            
            # Try to fire antibodies if it's a virus
            if "Virus" in organism.type and self.antibody_production_cooldown <= 0:
                self._fire_antibodies(organism)
                
            return True
            
        return False
        
    def render(self, screen, camera_x, camera_y, zoom):
        """
        Render the T-Cell on the screen
        
        Args:
            screen: pygame screen surface
            camera_x (float): Camera x position
            camera_y (float): Camera y position
            zoom (float): Zoom level
        """
        if not self.is_alive:
            return
        
        # Calculate screen position
        screen_x = int((self.x - camera_x) * zoom + screen.get_width() / 2)
        screen_y = int((self.y - camera_y) * zoom + screen.get_height() / 2)
        
        # Skip if off screen
        if (screen_x < -50 or screen_x > screen.get_width() + 50 or
            screen_y < -50 or screen_y > screen.get_height() + 50):
            return
        
        # Set color based on activation
        if self.activation_level >= self.activation_threshold:
            cell_color = self.active_color
            
            # Draw activation aura when highly activated
            aura_radius = int(self.size * zoom * (1.2 + 0.4 * min(1.0, self.activation_level / 100)))
            aura_opacity = min(200, int(100 + self.activation_level))
            aura_surface = pygame.Surface((aura_radius * 2, aura_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                aura_surface, 
                (*self.active_color[:3], aura_opacity), 
                (aura_radius, aura_radius), 
                aura_radius
            )
            screen.blit(aura_surface, (screen_x - aura_radius, screen_y - aura_radius))
        else:
            cell_color = self.color
            
        # Draw the main T-Cell body
        radius = max(2, int(self.size * zoom))
        pygame.draw.circle(screen, cell_color, (screen_x, screen_y), radius)
        
        # Draw a dark blue nucleus
        nucleus_radius = max(1, int(radius * 0.5))
        pygame.draw.circle(screen, (20, 50, 120), (screen_x, screen_y), nucleus_radius)
        
        # Draw a line to target if we have one
        if self.target and self.target.is_alive:
            target_screen_x = int((self.target.x - camera_x) * zoom + screen.get_width() / 2)
            target_screen_y = int((self.target.y - camera_y) * zoom + screen.get_height() / 2)
            
            # Draw a line to show targeting
            if self.activation_level >= self.activation_threshold:
                # Animated targeting line for activated cells
                line_segments = 8
                for i in range(line_segments):
                    if i % 2 == 0:  # Draw every other segment
                        start_pct = i / line_segments
                        end_pct = (i + 1) / line_segments
                        
                        start_x = screen_x + int((target_screen_x - screen_x) * start_pct)
                        start_y = screen_y + int((target_screen_y - screen_y) * start_pct)
                        end_x = screen_x + int((target_screen_x - screen_x) * end_pct)
                        end_y = screen_y + int((target_screen_y - screen_y) * end_pct)
                        
            pygame.draw.line(
                screen,
                            (150, 210, 255), 
                            (start_x, start_y), 
                            (end_x, end_y), 
                            max(1, int(zoom))
                        )
            else:
                # Simple line for non-activated cells
                pygame.draw.line(
                    screen,
                    (150, 210, 255, 128), 
                    (screen_x, screen_y),
                    (target_screen_x, target_screen_y),
                    max(1, int(zoom * 0.5))
                ) 