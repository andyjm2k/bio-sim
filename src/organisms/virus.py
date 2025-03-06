"""
Virus Module for Bio-Sim
Implements the Virus class, representing viral microorganisms
"""

import numpy as np
import pygame
from pygame import gfxdraw
import random
import math
from src.organisms.organism import Organism

class Virus(Organism):
    """
    Virus class representing viral microorganisms in the simulation.
    Viruses cannot reproduce on their own and must infect host cells.
    """
    
    def __init__(self, x, y, size, color, speed, dna_length=80):
        """
        Initialize a virus microorganism
        
        Args:
            x (float): Initial x position
            y (float): Initial y position
            size (float): Size of the virus
            color (tuple): RGB color tuple
            speed (float): Base movement speed
            dna_length (int): Length of the DNA sequence
        """
        super().__init__(x, y, size, color, speed, dna_length)
        
        # Virus-specific properties
        self.structure = {
            "has_envelope": True,  # Some viruses have lipid envelope
            "has_capsid": True,    # Protein shell
            "nucleic_acid": "RNA"  # or "DNA"
        }
        
        # Host interaction properties
        self.host = None           # Current host cell (if any)
        self.dormant_counter = 0   # Counter for dormancy in host
        self.dormant_threshold = 70  # Threshold to trigger reproduction (reduced from 100)
        self.infection_chance = 0.4  # Chance to infect a suitable cell
        self.virulence = 0.8       # Damage caused to host per update
        self.replication_rate = 0.5  # Chance to replicate when conditions are right (increased from 0.3)
        self.replication_cooldown = 0  # Cooldown between replication attempts
        
        # Virus type - can be overridden by subclasses
        self.type = "generic"
        
        # Antibody marking system
        self.antibody_marked = False  # Whether virus is marked by antibodies
        self.antibody_level = 0.0     # Level of antibody coverage (0-1)
        self.antibody_marker = None   # Reference to the TCell type that marked this virus
        self.antibody_duration = 0    # Duration of antibody marking in simulation ticks
        self.antibody_max_duration = 300  # How long antibodies remain active
        
        # Modify properties based on DNA
        self._apply_dna_effects()
    
    def _decode_dna(self):
        """
        Decode DNA sequence to derive trait values.
        Returns a list of normalized values between 0 and 1 that can be used
        for various traits in derived virus classes.
        
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
    
    def _apply_dna_effects(self):
        """Apply effects of the DNA sequence to the virus's properties"""
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
        # More A: Better infection chance
        # More T: Higher virulence
        # More G: Better resilience
        # More C: Higher replication rate
        
        self.infection_chance += base_counts['A'] * 0.2
        self.virulence += base_counts['T'] * 0.15
        self.health += base_counts['G'] * 20
        self.replication_rate += base_counts['C'] * 0.01
    
    def _apply_environmental_effects(self, environment):
        """
        Apply environmental effects to the virus
        
        Args:
            environment: The environment object
        """
        # Get environment variables for current position
        env_data = environment.get_conditions_at(self.x, self.y)
        
        # Viruses are less affected by environmental conditions
        # but are still impacted by extreme conditions
        
        # Temperature effect
        temp = env_data['temperature']
        if temp < 10 or temp > 50:
            self.health -= 0.5
        
        # Energy decay
        # Viruses lose energy over time when not inside a host
        if self.host is None:
            self.energy -= 0.1
    
    def _apply_decision(self, decision, environment):
        """
        Apply the neural network decision to the virus's state
        
        Args:
            decision (list): Output from neural network
            environment: The environment object
        """
        # If virus has a host, it moves with the host
        if self.host is not None:
            self.x = self.host.x
            self.y = self.host.y
            return
            
        # Otherwise, use standard movement
        super()._apply_decision(decision, environment)
    
    def update(self, environment):
        """
        Update the virus's state
        
        Args:
            environment: The environment object
        """
        # If virus has infected a host
        if self.host is not None:
            # Check if host is still alive
            if not self.host.is_alive:
                # Host cell died - trigger viral burst
                # print(f"Host cell died - checking for viral burst condition for {self.get_name()}")
                # Store host position before clearing it
                host_x, host_y = self.host.x, self.host.y
                host_health_before_death = getattr(self.host, 'health', 0)
                
                # Store dormant counter before resetting
                dormant_counter_before_death = self.dormant_counter
                
                # Clear host reference
                self.host = None
                self.dormant_counter = 0
                
                # Much more lenient viral burst conditions:
                # 1. Virus only needs to have been inside the host for a minimal time
                # 2. Cell health threshold is much easier to reach
                # 3. Energy requirement is significantly lower
                if (dormant_counter_before_death > 10 and  # Reduced from dormant_threshold * 0.5
                    host_health_before_death <= -10 and     # Reduced from -15
                    self.energy > 40):                     # Reduced from 40
                    
                    # Create a list to hold new viruses
                    new_viruses = []
                    
                    # Get viral burst count from config, defaulting to 5 if not specified
                    num_viruses = environment.config.get("simulation_settings", {}).get("viral_burst_count", 5)
                    
                    # Output viral burst message for debug
                    # print(f"Viral Burst: Creating {num_viruses} new {self.get_name()} particles from dead cell")
                    
                    # Create virus particles
                    for i in range(num_viruses):
                        # Add larger variation to position for wider spread
                        offset_x = np.random.uniform(-15, 15)
                        offset_y = np.random.uniform(-15, 15)
                        
                        # Slightly mutate color
                        r, g, b = self.color
                        color_mutation = 10
                        new_color = (
                            max(0, min(255, r + np.random.randint(-color_mutation, color_mutation))),
                            max(0, min(255, g + np.random.randint(-color_mutation, color_mutation))),
                            max(0, min(255, b + np.random.randint(-color_mutation, color_mutation)))
                        )
                        
                        # Get size range from config instead of using parent's size
                        virus_type = self.get_name()
                        org_config = environment.config.get("organism_types", {}).get(virus_type, {})
                        min_size, max_size = org_config.get("size_range", [2, 4])  # Default to [2, 4] if not found
                        new_size = np.random.uniform(min_size, max_size)
                        
                        # Get speed range from config
                        min_speed, max_speed = org_config.get("speed_range", [1.0, 2.0])  # Default to [1.0, 2.0] if not found
                        new_speed = np.random.uniform(min_speed, max_speed)
                        
                        # New virus starts at host location with offset
                        child = type(self)(
                            host_x + offset_x, 
                            host_y + offset_y,
                            new_size,  # Use size from config range
                            new_color,
                            new_speed  # Use speed from config range
                        )
                        
                        # Copy DNA to child
                        child.dna = self.dna.copy()
                        
                        # Give child a moderate initial energy
                        child.energy = 100  # Reduced from 150
                        
                        # Add to environment
                        if environment.simulation:
                            environment.simulation.organisms.append(child)
                    
                    # Use energy for viral burst - scale with number of viruses but with lower cost
                    self.energy -= min(self.energy * 0.5, num_viruses * 4)  # Reduced energy cost
                    
                    # Set cooldown to prevent immediate reproduction
                    self.replication_cooldown = 40  # Reduced from 30
            else:
                # Damage host
                self.host.health -= self.virulence
                
                # Gain energy from host
                self.energy += self.virulence * 5
                
                # Cap energy
                self.energy = min(150, self.energy)
                
                # Increment dormant counter
                self.dormant_counter += 1
                
                # If enough time passes, try to replicate
                if self.dormant_counter > self.dormant_threshold:  # Using the new threshold
                    self.dormant_counter = 0
                    return  # Skip normal update to proceed to reproduction
        
        # Decrement replication cooldown if active
        if self.replication_cooldown > 0:
            self.replication_cooldown -= 1
            
        # Update antibody duration if marked
        if self.antibody_marked:
            self.antibody_duration += 1
            
            # If antibodies have expired, clear them
            if self.antibody_duration >= self.antibody_max_duration:
                self.antibody_marked = False
                self.antibody_level = 0.0
                self.antibody_marker = None
                self.antibody_duration = 0
        
        # Special case for young viruses - reduce energy consumption rate
        if self.age < 20:  # For very young viruses
            # Reduce energy consumption by 80%
            old_energy = self.energy
            super().update(environment)
            energy_used = old_energy - self.energy
            # Restore 80% of used energy to reduce consumption rate
            self.energy += energy_used * 0.8
        else:
            # Normal update if not actively replicating inside host
            super().update(environment)
    
    def reproduce(self, environment):
        """
        Attempt to replicate inside a host
        
        Args:
            environment: The environment object
            
        Returns:
            list: A list of new virus instances or None if replication fails
        """
        # Check if on cooldown
        if self.replication_cooldown > 0:
            return None
            
        # Safety check: ensure host reference is cleared if host is dead
        if self.host is not None and not self.host.is_alive:
            # print(f"Safety check: {self.get_name()} has reference to dead host - clearing it")
            self.host = None
            return None
            
        # Check population cap from environment config
        max_organisms = environment.config.get("simulation_settings", {}).get("max_organisms", 0)
        if max_organisms > 0:
            # Get approximate count of organisms (we don't have direct access to the full list)
            # This is a heuristic to help prevent overpopulation
            organism_density = max_organisms / (environment.width * environment.height)
            local_area = np.pi * 100 * 100  # Circular area of radius 100
            estimated_local_count = organism_density * local_area
            
            # If estimated local population is high, reduce replication chance
            if estimated_local_count > 20:  # Arbitrary threshold
                if np.random.random() < 0.3:  # Reduced from 0.5 to allow more reproduction in dense areas
                    return None
        
        # Viruses can only reproduce when they have a host
        if (self.host is not None and 
            self.host.is_alive and 
            self.energy > 30 and  # Reduced from 40
            np.random.random() < self.replication_rate):
            
            # Create mutation in DNA
            child_dna = self.dna.copy()
            if np.random.random() < environment.config['simulation_settings']['mutation_rate'] * 2:  # Viruses mutate more
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
            
            # Consume energy for replication
            self.energy -= 35
            
            # Set cooldown to prevent immediate reproduction
            self.replication_cooldown = 30
            
            # Create a list to hold new viruses
            new_viruses = []
            
            # Get viral burst count from config, defaulting to 5 if not specified
            num_viruses = environment.config.get("simulation_settings", {}).get("viral_burst_count", 5)
            
            # Output viral burst message for debug
            # print(f"Virus replication: Creating {num_viruses} new {self.get_name()} particles")

            # Create virus particles
            for i in range(num_viruses):
                # Add larger variation to position for wider spread
                offset_x = np.random.uniform(-15, 15)  # Increased spread radius
                offset_y = np.random.uniform(-15, 15)
                
                # Get size range from config instead of multiplying parent size
                org_config = environment.config.get("organism_types", {}).get("Influenza", {})
                min_size, max_size = org_config.get("size_range", [2, 4])  # Default to [2, 4] if not found
                new_size = np.random.uniform(min_size, max_size)
                
                # Get speed range from config
                min_speed, max_speed = org_config.get("speed_range", [1.2, 2.8])  # Default to [1.2, 2.8] if not found
                new_speed = np.random.uniform(min_speed, max_speed)
                
                # New virus starts at host location with offset
                child = type(self)(
                    self.host.x + offset_x, 
                    self.host.y + offset_y,
                    new_size,  # Use size from config range instead of parent size multiplier
                    new_color,
                    new_speed  # Use speed from config range instead of parent speed multiplier
                )
                
                # Copy DNA to child
                child.dna = child_dna.copy()
                
                # Give child a moderate initial energy
                child.energy = 100
                
                # Damage the host for each new virus
                if hasattr(self.host, 'health'):
                    damage = 0.5  # Small damage per virus particle
                    self.host.health = max(0, self.host.health - damage)
                
                # Add to list of new viruses
                new_viruses.append(child)
            
            return new_viruses
        
        return None
    
    def interact(self, other_organism, environment):
        """
        Interact with another organism
        
        Args:
            other_organism: Another organism instance
            environment: The environment object
        """
        # Viruses target cells to infect
        # Check if target is a cell type that can be infected
        other_type = getattr(other_organism, 'get_type', lambda: None)()
        
        # Expand types of cells that can be infected by viruses
        if (other_type in ["EpithelialCell", "RedBloodCell"] and hasattr(other_organism, 'infect')):
            # Attempt to infect the cell
            if np.random.random() < self.infection_chance:  # Use infection_chance probability
                if other_organism.infect(self):
                    # Successful infection
                    self.energy += 20  # Increased from 15
                    self.host = other_organism  # Set the cell as host
                    
                    # Viruses sometimes reproduce inside infected cells
                    if environment.random.random() < 0.25:  # Increased from 0.15
                        self.reproduction_ready = True
                    
        # Viruses can be destroyed by immune cells
        if "whiteb" in other_type.lower() or "tcell" in other_type.lower() or "macro" in other_type.lower():
            # Immune cells attack viruses
            attack_chance = 0.1  # Base chance
            
            # T-Cells are more effective against viruses
            if "tcell" in other_type.lower():
                attack_chance = 0.3
                
            # Macrophages are better at engulfing viruses
            if "macro" in other_type.lower():
                attack_chance = 0.3
                
            # Evasion reduces attack chance
            if hasattr(self, 'evasion'):
                attack_chance *= (1 - self.evasion)
                
            # Check if attack succeeds
            if environment.random.random() < attack_chance:
                self.health -= 20
                
                # If killed, give energy to the immune cell
                if self.health <= 0 and hasattr(other_organism, 'energy'):
                    other_organism.energy += 15
    
    def get_type(self):
        """Return the type of organism"""
        return "virus"

    def mark_with_antibodies(self, t_cell_type, initial_level=0.5):
        """
        Mark this virus with antibodies from a T-Cell
        
        Args:
            t_cell_type (str): The type of T-Cell that produced the antibodies
            initial_level (float): Initial level of antibody coverage (0-1)
            
        Returns:
            bool: Whether marking was successful
        """
        # If already marked by the same T-Cell type, just increase the level
        if self.antibody_marked and self.antibody_marker == t_cell_type:
            self.antibody_level = min(1.0, self.antibody_level + initial_level)
            self.antibody_duration = 0  # Reset duration
            return True
            
        # New marking
        self.antibody_marked = True
        self.antibody_level = initial_level
        self.antibody_marker = t_cell_type
        self.antibody_duration = 0
        
        return True
        
    def render(self, screen, camera_x, camera_y, zoom):
        """
        Render the virus on the screen with antibody markers if present
        
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
        
        # Draw the main virus body
        radius = max(2, int(self.size * zoom))
        
        # Base virus rendering
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), radius)
        
        # Draw a darker outline
        pygame.draw.circle(
            screen, 
            (max(0, self.color[0] - 30), max(0, self.color[1] - 30), max(0, self.color[2] - 30)),
            (screen_x, screen_y),
            radius,
            1
        )
        
        # Draw antibody markers if present
        if self.antibody_marked and self.antibody_level > 0:
            # Create a pulsating effect for antibodies
            pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.25 + 0.5
            
            # Antibody color (yellowish glow that pulses)
            antibody_color = (
                min(255, int(230 * pulse)),
                min(255, int(230 * pulse)), 
                min(255, int(100 * pulse))
            )
            
            # Draw outer glow to represent antibodies
            antibody_radius = radius + max(1, int(radius * 0.4 * self.antibody_level))
            
            # Draw dashed circle for antibodies
            num_segments = 12
            for i in range(num_segments):
                # Draw only every other segment for dashed effect
                if i % 2 == 0:
                    start_angle = i * (2 * math.pi / num_segments)
                    end_angle = (i + 1) * (2 * math.pi / num_segments)
                    
                    # Calculate points for arc
                    start_x = screen_x + int(antibody_radius * math.cos(start_angle))
                    start_y = screen_y + int(antibody_radius * math.sin(start_angle))
                    end_x = screen_x + int(antibody_radius * math.cos(end_angle))
                    end_y = screen_y + int(antibody_radius * math.sin(end_angle))
                    
                    # Draw arc segment
                    pygame.draw.arc(
                        screen,
                        antibody_color,
                        pygame.Rect(
                            screen_x - antibody_radius,
                            screen_y - antibody_radius,
                            antibody_radius * 2,
                            antibody_radius * 2
                        ),
                        start_angle,
                        end_angle,
                        max(1, int(radius * 0.2))
                    )

    def get_name(self):
        """
        Get the name of the virus
        
        Returns:
            str: The virus type name
        """
        return self.__class__.__name__

class Influenza(Virus):
    """Influenza virus that infects respiratory cells"""
    
    def __init__(self, x, y, size, color, speed):
        """Initialize Influenza virus"""
        # Influenza is reddish
        color = (255, 50, 50)
        super().__init__(x, y, size, color, speed)
        
        # Influenza properties - more moderate than before
        self.infectivity = 0.6  # Reduced from 0.9
        self.infection_chance = 0.4  # Reduced from 0.8
        self.targets = ["EpithelialCell", "RedBloodCell"]
        self.replication_rate = 0.4  # Reduced from 0.85
        self.dormant_threshold = 70  # Increased from 40 for slower replication cycle
        
        # Influenza immune evasion properties
        trait_vals = self._decode_dna()
        self.evasion = trait_vals[0] * 0.5 + 0.2  # Reduced from 0.7
        self.surface_mutation_rate = trait_vals[1] * 0.15 + 0.1  # Reduced from 0.2
        self.activation_threshold = 50 + trait_vals[2] * 30  # Increased from 30+20
    
    def get_type(self):
        return "virus"
        
    def get_name(self):
        return "Influenza"
        
    def render(self, screen, camera_x, camera_y, zoom):
        """Render influenza virus with its distinctive spherical shape and surface proteins"""
        if not self.is_alive:
            return
            
        # Calculate screen position
        screen_x = int((self.x - camera_x) * zoom + screen.get_width() / 2)
        screen_y = int((self.y - camera_y) * zoom + screen.get_height() / 2)
        
        # Skip if off screen
        if (screen_x < -50 or screen_x > screen.get_width() + 50 or
            screen_y < -50 or screen_y > screen.get_height() + 50):
            return
        
        # Draw the main virus body
        radius = max(2, int(self.size * zoom))
        
        # Ensure we use the correct color - fixed color assignment
        # Make sure this doesn't get overridden elsewhere
        pygame.draw.circle(screen, (255, 50, 50), (screen_x, screen_y), radius)
        
        # Draw a darker outline
        pygame.draw.circle(
            screen,
            (200, 30, 30),  # Darker red outline
            (screen_x, screen_y),
            radius,
            1
        )
        
        # Draw the characteristic surface proteins (hemagglutinin and neuraminidase)
        # that give influenza its distinctive appearance and name
        num_spikes = 12  # Number of protein spikes on the surface
        spike_length = max(1, int(radius * 0.5))  # Length of each spike
        
        for i in range(num_spikes):
            angle = i * (2 * math.pi / num_spikes)
            
            # Calculate spike start (on the virus surface)
            spike_start_x = screen_x + int(radius * math.cos(angle))
            spike_start_y = screen_y + int(radius * math.sin(angle))
            
            # Calculate spike end (extending outward)
            spike_end_x = screen_x + int((radius + spike_length) * math.cos(angle))
            spike_end_y = screen_y + int((radius + spike_length) * math.sin(angle))
            
            # Alternate between spike types (hemagglutinin and neuraminidase)
            if i % 2 == 0:
                # Hemagglutinin (H) - ends in a small bulb
                pygame.draw.line(screen, (200, 30, 30), 
                                (spike_start_x, spike_start_y), 
                                (spike_end_x, spike_end_y), 
                                max(1, int(zoom)))  # Line thickness scales with zoom
                # Draw the bulb at the end
                pygame.draw.circle(screen, (220, 50, 50), 
                                  (spike_end_x, spike_end_y), 
                                  max(1, int(radius * 0.15)))
            else:
                # Neuraminidase (N) - more mushroom-shaped
                pygame.draw.line(screen, (180, 30, 30), 
                                (spike_start_x, spike_start_y), 
                                (spike_end_x, spike_end_y), 
                                max(1, int(zoom)))  # Line thickness scales with zoom
                # Draw the mushroom cap
                cap_radius = max(1, int(radius * 0.25))
                pygame.draw.circle(screen, (200, 40, 40), 
                                  (spike_end_x, spike_end_y), 
                                  cap_radius)
                                  
        # Draw antibody markers if present (copied from base class)
        if hasattr(self, 'antibody_marked') and self.antibody_marked and hasattr(self, 'antibody_level') and self.antibody_level > 0:
            # Create a pulsating effect for antibodies
            pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.25 + 0.5
            
            # Antibody color (yellowish glow that pulses)
            antibody_color = (
                min(255, int(230 * pulse)),
                min(255, int(230 * pulse)), 
                min(255, int(100 * pulse))
            )
            
            # Draw outer glow to represent antibodies
            antibody_radius = radius + max(1, int(radius * 0.4 * self.antibody_level))
            
            # Draw dashed circle for antibodies
            num_segments = 12
            for i in range(num_segments):
                # Draw only every other segment for dashed effect
                if i % 2 == 0:
                    start_angle = i * (2 * math.pi / num_segments)
                    end_angle = (i + 1) * (2 * math.pi / num_segments)
                    
                    # Calculate points for arc
                    start_x = screen_x + int(antibody_radius * math.cos(start_angle))
                    start_y = screen_y + int(antibody_radius * math.sin(start_angle))
                    end_x = screen_x + int(antibody_radius * math.cos(end_angle))
                    end_y = screen_y + int(antibody_radius * math.sin(end_angle))
                    
                    # Draw arc segment
                    pygame.draw.arc(
                        screen,
                        antibody_color,
                        pygame.Rect(
                            screen_x - antibody_radius,
                            screen_y - antibody_radius,
                            antibody_radius * 2,
                            antibody_radius * 2
                        ),
                        start_angle,
                        end_angle,
                        max(1, int(radius * 0.2))
                    )

    def interact(self, other_organism, environment):
        """Specialized interaction for Influenza virus"""
        other_type = getattr(other_organism, 'get_type', lambda: None)()
        other_name = getattr(other_organism, 'get_name', lambda: None)()
        
        # Influenza targets cells with more moderate infection rate
        if other_type in ["EpithelialCell", "RedBloodCell"] and hasattr(other_organism, 'infect'):
            # More balanced chance to infect cells
            if np.random.random() < self.infection_chance:
                if other_organism.infect(self):
                    self.energy += 25  # Reduced from 40
                    self.host = other_organism
                    
                    # Moderate chance to trigger reproduction
                    if environment.random.random() < 0.3:  # Reduced from 0.65
                        self.reproduction_ready = True
                        self.dormant_counter = max(self.dormant_counter, self.dormant_threshold - 15)
        
        # Handle immune responses
        if "whiteb" in other_type.lower() or "tcell" in other_type.lower() or "macro" in other_type.lower():
            attack_chance = 0.1  # Increased from 0.05
            
            if "tcell" in other_type.lower():
                attack_chance = 0.25  # Increased from 0.15
                
            if "macro" in other_type.lower():
                attack_chance = 0.2  # Increased from 0.1
            
            # Apply improved evasion modifier
            attack_chance *= (1 - self.evasion)
            
            # Surface mutation provides additional protection against immune cells
            attack_chance *= (1 - self.surface_mutation_rate)
            
            if environment.random.random() < attack_chance:
                self.health -= 18  # Increased from 12
                
                if self.health <= 0 and hasattr(other_organism, 'energy'):
                    other_organism.energy += 15
    
    def reproduce(self, environment):
        """
        Override reproduce method for Influenza to be more aggressive
        """
        # Check if on cooldown - shorter cooldown for Influenza
        if self.replication_cooldown > 0:
            self.replication_cooldown -= 2  # Faster cooldown reduction (2 per update)
            if self.replication_cooldown <= 0:
                # print("Influenza ready to replicate again!")
                pass
            return None
            
        # Relaxed population density check
        max_organisms = environment.config.get("simulation_settings", {}).get("max_organisms", 0)
        if max_organisms > 0:
            # Influenza ignores local density more than other viruses
            organism_density = max_organisms / (environment.width * environment.height)
            local_area = np.pi * 100 * 100  # Circular area of radius 100
            estimated_local_count = organism_density * local_area
            
            # Higher threshold before reducing replication chance
            if estimated_local_count > 40:  # Increased from 20
                if np.random.random() < 0.2:  # Reduced from 0.3 - even more aggressive in dense areas
                    return None
        
        # Influenza can replicate with lower energy requirements
        if (self.host is not None and 
            self.host.is_alive and 
            self.energy > 25 and  # Reduced from 30
            np.random.random() < self.replication_rate):
            
            # Create mutation in DNA - Influenza mutates rapidly
            child_dna = self.dna.copy()
            if np.random.random() < environment.config['simulation_settings']['mutation_rate'] * 3:  # Increased mutation chance
                mutation_idx = np.random.randint(0, len(child_dna))
                bases = ['A', 'T', 'G', 'C']
                child_dna[mutation_idx] = bases[np.random.randint(0, 4)]
            
            # Slightly mutate color
            r, g, b = self.color
            color_mutation = 15  # Increased color variation
            new_color = (
                max(0, min(255, r + np.random.randint(-color_mutation, color_mutation))),
                max(0, min(255, g + np.random.randint(-color_mutation, color_mutation))),
                max(0, min(255, b + np.random.randint(-color_mutation, color_mutation)))
            )
            
            # Consume energy for replication
            self.energy -= 30  # Replication energy cost
            
            # Set cooldown to prevent immediate reproduction
            self.replication_cooldown = 40  # Higher cooldown than normal viruses
            
            # Create a list for new viruses
            new_viruses = []
            
            # Get viral burst count from config, defaulting to 5 if not specified
            num_viruses = environment.config.get("simulation_settings", {}).get("viral_burst_count", 5)
            
            # Output viral burst message for debug
            # print(f"Influenza reproducing: Creating {num_viruses} new virus particles")
            
            # Create virus particles
            for i in range(num_viruses):
                # Add larger variation to position for wider spread
                offset_x = np.random.uniform(-15, 15)  # Increased spread radius
                offset_y = np.random.uniform(-15, 15)
                
                # Get size range from config instead of multiplying parent size
                org_config = environment.config.get("organism_types", {}).get("Influenza", {})
                min_size, max_size = org_config.get("size_range", [2, 4])  # Default to [2, 4] if not found
                new_size = np.random.uniform(min_size, max_size)
                
                # Get speed range from config
                min_speed, max_speed = org_config.get("speed_range", [1.2, 2.8])  # Default to [1.2, 2.8] if not found
                new_speed = np.random.uniform(min_speed, max_speed)
                
                # New virus starts at host location with offset
                child = type(self)(
                    self.host.x + offset_x, 
                    self.host.y + offset_y,
                    new_size,  # Use size from config range instead of parent size multiplier
                    new_color,
                    new_speed  # Use speed from config range instead of parent speed multiplier
                )
                
                # Copy DNA to child
                child.dna = child_dna.copy()
                
                # Give child higher initial energy
                child.energy = 100  # Moderate energy to balance survival
                
                # Damage the host more for each new virus
                if hasattr(self.host, 'health'):
                    damage = 0.5  # Reduced from 0.8 - less damage per virus
                    self.host.health = max(0, self.host.health - damage)
                
                # Add to list of new viruses
                new_viruses.append(child)
            
            return new_viruses
        
        return None

class Rhinovirus(Virus):
    """Rhinovirus that causes common cold"""
    
    def __init__(self, x, y, size, color, speed):
        """Initialize Rhinovirus"""
        color = (100, 180, 255)  # Bluish color
        super().__init__(x, y, size, color, speed)
        
        # Rhinovirus properties - more moderate
        self.infection_chance = 0.3  # Reduced from 0.55
        self.virulence = 0.2  # Reduced from 0.4
        self.replication_rate = 0.35  # Reduced from 0.7
        self.dormant_threshold = 80  # Increased from 55
        
        # Decode DNA for traits
        trait_vals = self._decode_dna()
        self.cold_resistance = trait_vals[0] * 0.5  # Reduced from 0.6
        self.infection_boost = trait_vals[1] * 0.15  # Reduced from 0.2
        self.targets = ["EpithelialCell"]
    
    def get_type(self):
        return "virus"
        
    def get_name(self):
        return "Rhinovirus"
    
    def _apply_environmental_effects(self, environment):
        """Apply environmental effects with cold resistance advantage"""
        conditions = environment.get_conditions_at(self.x, self.y)
        
        # Base environmental effects
        super()._apply_environmental_effects(environment)
        
        # Rhinoviruses thrive in cooler temperatures
        temperature = conditions["temperature"]
        if temperature < 37:  # Below body temperature
            # Less energy loss in cold environments
            energy_boost = (37 - temperature) * 0.02 * self.cold_resistance
            self.energy += energy_boost
            
            # Infection chance boost in cold
            self.infection_chance = 0.3 + self.infection_boost * (37 - temperature) * 0.01
            self.infection_chance = min(0.8, self.infection_chance)  # Cap at 80%
        else:
            # Reset to normal
            self.infection_chance = 0.3
    
    def reproduce(self, environment):
        """
        Override reproduce method for Rhinovirus to favor cold environments
        """
        # Check if on cooldown
        if self.replication_cooldown > 0:
            return None
            
        # Get environmental conditions for possible boost
        conditions = environment.get_conditions_at(self.x, self.y)
        temperature = conditions["temperature"]
        
        # Special boost in cold environments
        temp_boost = 0
        if temperature < 37:
            temp_boost = (37 - temperature) * 0.02  # Up to 0.2 boost in cold (27°C)
        
        # Check for host cell first - log message added for debugging
        if self.host is None:
            # Debug message - rhinovirus has no host but tried to reproduce
            # print(f"Warning: Rhinovirus at ({self.x:.1f}, {self.y:.1f}) attempted reproduction without a host")
            return None
            
        # Double-check host is still alive
        if not self.host.is_alive:
            # print(f"Warning: Rhinovirus attempted reproduction with dead host - clearing reference")
            self.host = None
            return None
            
        # Viruses can only reproduce when they have a host
        if (self.host.is_alive and 
            self.energy > 25 and  # Lower energy requirement
            np.random.random() < (self.replication_rate + temp_boost)):
            
            # Create mutation in DNA with possible cold adaptation
            child_dna = self.dna.copy()
            mutation_chance = environment.config['simulation_settings']['mutation_rate'] * 2
            
            # Higher mutation in cold environments
            if temperature < 37:
                mutation_chance *= 1.2
                
            if np.random.random() < mutation_chance:
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
            
            # Consume energy for replication
            self.energy -= 30
            
            # Set cooldown to prevent immediate reproduction
            self.replication_cooldown = 35
            
            # Create a list for new viruses
            new_viruses = []
            
            # Get viral burst count from config, defaulting to 5 if not specified
            num_viruses = environment.config.get("simulation_settings", {}).get("viral_burst_count", 5)
            
            # Output viral burst message for debug
            # print(f"Rhinovirus reproducing: Creating {num_viruses} new virus particles")
            
            # Create offspring 
            for i in range(num_viruses):
                # Random position offset
                offset_x = np.random.uniform(-15, 15)
                offset_y = np.random.uniform(-15, 15)
                
                # Get size range from config instead of multiplying parent size
                org_config = environment.config.get("organism_types", {}).get("Rhinovirus", {})
                min_size, max_size = org_config.get("size_range", [2, 3])  # Default to [2, 3] if not found
                new_size = np.random.uniform(min_size, max_size)
                
                # Get speed range from config
                min_speed, max_speed = org_config.get("speed_range", [1.0, 2.5])  # Default to [1.0, 2.5] if not found
                new_speed = np.random.uniform(min_speed, max_speed)
                
                # Slightly mutate color
                r, g, b = self.color
                color_mutation = 10
                new_color = (
                    max(0, min(255, r + np.random.randint(-color_mutation, color_mutation))),
                    max(0, min(255, g + np.random.randint(-color_mutation, color_mutation))),
                    max(0, min(255, b + np.random.randint(-color_mutation, color_mutation)))
                )
                
                # Create new virus with cold adaptation
                child = Rhinovirus(
                    self.x + offset_x,
                    self.y + offset_y,
                    new_size,
                    new_color,
                    new_speed
                )
                
                # Copy DNA to child
                child.dna = child_dna.copy()
                
                # Give child energy
                child.energy = 100
                
                # Damage the host, more in colder environments
                if hasattr(self.host, 'health'):
                    damage_factor = 1.0
                    if temperature < 37:
                        damage_factor = 1.0 + (37 - temperature) * 0.03  # Up to 30% more damage in cold
                    damage = 0.4 * damage_factor
                    self.host.health = max(0, self.host.health - damage)
                
                # Add to list of new viruses
                new_viruses.append(child)
            
            return new_viruses
        
        return None

class Coronavirus(Virus):
    """Coronavirus class"""
    
    def __init__(self, x, y, size, color, speed):
        """Initialize coronavirus with specific traits"""
        # Initialize the base virus class first
        super().__init__(x, y, size, color, speed)
        
        # Set specific Coronavirus attributes
        self.color = (180, 100, 180)  # Purple
        self.shape = "complex"
        self.structure["has_envelope"] = True
        self.structure["has_spikes"] = True
        self.spike_count = random.randint(15, 25)  # Spike proteins
        
        # Add standard virus parameters that may be missing
        self.infectivity = 0.7
        self.infection_chance = 0.5
        self.targets = ["EpithelialCell", "RedBloodCell"]
        self.replication_rate = 0.5
        self.dormant_threshold = 65
        
        # Coronavirus specific traits
        self.dna_traits = {
            "mutation_rate": 0.3,  # High mutation rate (RNA virus)
            "infectivity": 0.7,
            "environmental_resistance": 0.5
        }
        
        # Transmission traits
        self.transmission_routes = {
            "respiratory": 0.8,  # High respiratory transmission
            "contact": 0.5,
            "fecal-oral": 0.2
        }
        
        # Antiviral resistance profile
        self.antiviral_resistance = {
            "oseltamivir": 0.6,
            "acyclovir": 0.6,
            "ribavirin": 0.3,
            "interferon": 0.4
        }
    
    def get_type(self):
        return "virus"
        
    def get_name(self):
        return "Coronavirus"
        
    def render(self, screen, camera_x, camera_y, zoom):
        """Render coronavirus with its distinctive crown of spikes"""
        # Calculate screen position
        screen_x = int((self.x - camera_x) * zoom + screen.get_width() / 2)
        screen_y = int((self.y - camera_y) * zoom + screen.get_height() / 2)
        
        # Scale radius based on zoom
        radius = int(self.size * zoom)
        if radius < 1:
            radius = 1
            
        # Draw main virus body
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), radius)
        
        # Draw darker outline
        outline_color = (max(0, self.color[0] - 40), max(0, self.color[1] - 40), max(0, self.color[2] - 40))
        pygame.draw.circle(screen, outline_color, (screen_x, screen_y), radius, 1)
        
        # Draw distinctive crown-like spikes
        num_spikes = 12  # Number of spike proteins
        spike_length = radius * 0.8  # Length of each spike
        for i in range(num_spikes):
            angle = 2 * math.pi * i / num_spikes
            # Spike base point (on virus surface)
            base_x = screen_x + int(radius * math.cos(angle))
            base_y = screen_y + int(radius * math.sin(angle))
            # Spike tip (extending outward)
            tip_x = screen_x + int((radius + spike_length) * math.cos(angle))
            tip_y = screen_y + int((radius + spike_length) * math.sin(angle))
            
            # Draw spike
            spike_color = (min(255, self.color[0] + 20), min(255, self.color[1] + 20), min(255, self.color[2] + 20))
            pygame.draw.line(screen, spike_color, (base_x, base_y), (tip_x, tip_y), 2)
            
            # Draw spike protein "bulb" at the end
            bulb_radius = int(radius * 0.3)
            if bulb_radius < 1:
                bulb_radius = 1
            pygame.draw.circle(screen, spike_color, (tip_x, tip_y), bulb_radius)
        
        # Draw antibodies if present
        if self.antibody_level > 0:
            # Calculate antibody radius
            antibody_radius = radius + int(spike_length * 1.5)
            # Draw dashed circle for antibodies
            dash_length = 5
            antibody_color = (200, 200, 100)  # Yellow-ish
            
            # Make it pulsate slightly
            pulsate = 0.8 + 0.2 * math.sin(pygame.time.get_ticks() / 200)
            antibody_radius = int(antibody_radius * pulsate)
            
            for i in range(0, 360, dash_length * 2):
                angle_start = math.radians(i)
                angle_end = math.radians(i + dash_length)
                start_x = screen_x + int(antibody_radius * math.cos(angle_start))
                start_y = screen_y + int(antibody_radius * math.sin(angle_start))
                end_x = screen_x + int(antibody_radius * math.cos(angle_end))
                end_y = screen_y + int(antibody_radius * math.sin(angle_end))
                pygame.draw.line(screen, antibody_color, (start_x, start_y), (end_x, end_y), 1)
    
    def reproduce(self, environment):
        """
        Reproduce coronavirus - uses spike proteins to bind to cell receptors
        Uses viral_burst_count from configuration
        """
        # Check if enough energy to reproduce
        if self.energy < 30 or self.replication_cooldown > 0:
            return
        
        # Viruses can only reproduce when they have a host
        if self.host is None or not self.host.is_alive:
            return None
            
        # Get environmental factors
        conditions = environment.get_conditions_at(self.x, self.y)
        temperature = conditions["temperature"]
        
        # Check for optimal conditions (slightly lower temp preference)
        temp_factor = 1.0
        if temperature < 36.0:  # Prefers slightly cooler temperatures
            temp_factor = 1.2
        
        # Check nearby organisms for overcrowding
        nearby_organisms = environment.get_nearby_organisms(self.x, self.y, 30)
        if len(nearby_organisms) > 5:
            # Less chance to reproduce in crowded areas
            if random.random() > 0.3:
                return
                
        # Get viral burst count from config, defaulting to 5 if not specified
        num_viruses = environment.config.get("simulation_settings", {}).get("viral_burst_count", 5)
                
        # Create new viruses
        new_viruses = []
        for i in range(num_viruses):
            # Small position variation
            offset_x = random.uniform(-10, 10)
            offset_y = random.uniform(-10, 10)
            
            # Get size range from config instead of multiplying parent size
            org_config = environment.config.get("organism_types", {}).get("Coronavirus", {})
            min_size, max_size = org_config.get("size_range", [2, 4])  # Default to [2, 4] if not found
            new_size = np.random.uniform(min_size, max_size)
            
            # Get speed range from config
            min_speed, max_speed = org_config.get("speed_range", [1.3, 2.7])  # Default to [1.3, 2.7] if not found
            new_speed = np.random.uniform(min_speed, max_speed)
            
            # Slight color mutation
            r, g, b = self.color
            color_mutation = 10
            new_color = (
                max(0, min(255, r + random.randint(-color_mutation, color_mutation))),
                max(0, min(255, g + random.randint(-color_mutation, color_mutation))),
                max(0, min(255, b + random.randint(-color_mutation, color_mutation)))
            )
            
            # Create child virus
            child = Coronavirus(
                self.x + offset_x,
                self.y + offset_y,
                new_size,
                new_color,
                new_speed
            )
            
            # DNA inheritance with mutation chance
            child.dna = self.dna.copy()
            if random.random() < 0.3 * temp_factor:  # Higher mutation in cooler temps
                mutation_point = random.randint(0, len(child.dna) - 1)
                child.dna[mutation_point] = random.randint(0, 1)
            
            # Give child energy and apply DNA effects
            child.energy = 100
            child._apply_dna_effects()
            
            # Add to environment
            if environment.simulation:
                environment.simulation.organisms.append(child)
            new_viruses.append(child)
            
        # Consume energy for reproduction
        self.energy -= 30 + (num_viruses * 3)
        
        # Set cooldown to prevent immediate reproduction
        self.replication_cooldown = 35
        
        return new_viruses

class Adenovirus(Virus):
    """Adenovirus class"""
    
    def __init__(self, x, y, size, color, speed):
        """Initialize Adenovirus with specific traits"""
        # Initialize the base virus class first
        super().__init__(x, y, size, color, speed)
        
        # Set specific Adenovirus attributes
        self.color = (220, 100, 100)  # Red
        self.shape = "icosahedral"
        self.structure["has_envelope"] = False
        self.structure["has_spikes"] = True
        self.fiber_count = random.randint(8, 12)  # Distinctive fibers at vertices
        
        # Add standard virus parameters that may be missing
        self.infectivity = 0.6
        self.infection_chance = 0.45
        self.targets = ["EpithelialCell", "RedBloodCell"]
        self.replication_rate = 0.4
        self.dormant_threshold = 75
        
        # Adenovirus specific traits
        self.dna_traits = {
            "mutation_rate": 0.05,  # Low mutation rate (DNA virus)
            "infectivity": 0.6,
            "environmental_resistance": 0.7  # Very resistant
        }
        
        # Update resistance profile
        self.antiviral_resistance = {
            "oseltamivir": 0.8,  # Highly resistant to antivirals
            "acyclovir": 0.7,
            "ribavirin": 0.6,
            "interferon": 0.5
        }
    
    def get_type(self):
        return "virus"
        
    def get_name(self):
        return "Adenovirus"
        
    def render(self, screen, camera_x, camera_y, zoom):
        """Render adenovirus with its icosahedral shape and fibers"""
        # Calculate screen position
        screen_x = int((self.x - camera_x) * zoom + screen.get_width() / 2)
        screen_y = int((self.y - camera_y) * zoom + screen.get_height() / 2)
        
        # Scale radius based on zoom
        radius = int(self.size * zoom)
        if radius < 1:
            radius = 1
        
        # Draw main virus body (icosahedral approximation)
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), radius)
        
        # Draw icosahedral facets (simplified version)
        facet_color = (min(255, self.color[0] + 30), min(255, self.color[1] + 30), min(255, self.color[2] + 30))
        
        # Draw outline
        outline_color = (max(0, self.color[0] - 40), max(0, self.color[1] - 40), max(0, self.color[2] - 40))
        pygame.draw.circle(screen, outline_color, (screen_x, screen_y), radius, 1)
        
        # Draw facet lines to give icosahedral appearance
        for i in range(5):
            angle1 = 2 * math.pi * i / 5
            angle2 = 2 * math.pi * ((i + 2) % 5) / 5
            
            x1 = screen_x + int(radius * 0.8 * math.cos(angle1))
            y1 = screen_y + int(radius * 0.8 * math.sin(angle1))
            
            x2 = screen_x + int(radius * 0.8 * math.cos(angle2))
            y2 = screen_y + int(radius * 0.8 * math.sin(angle2))
            
            pygame.draw.line(screen, facet_color, (x1, y1), (x2, y2), 1)
        
        # Draw the fiber projections at vertices
        fiber_color = (min(255, self.color[0] + 50), min(255, self.color[1] + 50), min(255, self.color[2] + 50))
        
        for i in range(self.fiber_count):
            angle = 2 * math.pi * i / self.fiber_count
            
            # Fiber base (on virus surface)
            base_x = screen_x + int(radius * math.cos(angle))
            base_y = screen_y + int(radius * math.sin(angle))
            
            # Fiber length
            fiber_length = radius * 0.6
            
            # Fiber tip
            tip_x = screen_x + int((radius + fiber_length) * math.cos(angle))
            tip_y = screen_y + int((radius + fiber_length) * math.sin(angle))
            
            # Draw fiber
            pygame.draw.line(screen, fiber_color, (base_x, base_y), (tip_x, tip_y), 1)
            
            # Draw knob at the end of fiber
            knob_radius = max(1, int(radius * 0.15))
            pygame.draw.circle(screen, fiber_color, (tip_x, tip_y), knob_radius)
        
        # Draw antibodies if present
        if self.antibody_level > 0:
            # Calculate antibody radius
            antibody_radius = radius + int(fiber_length * 1.5)
            
            # Draw dashed circle for antibodies
            dash_length = 5
            antibody_color = (200, 200, 100)  # Yellow-ish
            
            # Make it pulsate slightly
            pulsate = 0.8 + 0.2 * math.sin(pygame.time.get_ticks() / 200)
            antibody_radius = int(antibody_radius * pulsate)
            
            for i in range(0, 360, dash_length * 2):
                angle_start = math.radians(i)
                angle_end = math.radians(i + dash_length)
                start_x = screen_x + int(antibody_radius * math.cos(angle_start))
                start_y = screen_y + int(antibody_radius * math.sin(angle_start))
                end_x = screen_x + int(antibody_radius * math.cos(angle_end))
                end_y = screen_y + int(antibody_radius * math.sin(angle_end))
                pygame.draw.line(screen, antibody_color, (start_x, start_y), (end_x, end_y), 1)
                
    def reproduce(self, environment):
        """
        Reproduce adenovirus - uses fibers to attach to cell receptors
        Very stable DNA virus with high environmental resistance
        Uses viral_burst_count from configuration
        """
        # Check if enough energy to reproduce
        if self.energy < 35 or self.replication_cooldown > 0:
            return
        
        # Viruses can only reproduce when they have a host
        if self.host is None or not self.host.is_alive:
            return None
        
        # Get environmental conditions
        conditions = environment.get_conditions_at(self.x, self.y)
        ph_level = conditions["ph_level"]
        
        # DNA viruses are more stable in environment
        environmental_bonus = 1.0
        if ph_level < 6.0 or ph_level > 8.0:
            # Can tolerate wider pH range
            environmental_bonus = 1.2
            
        # Check nearby organisms for overcrowding
        nearby_organisms = environment.get_nearby_organisms(self.x, self.y, 30)
        if len(nearby_organisms) > 8:  # Higher tolerance for crowding
            # Still decent chance to reproduce in crowded areas
            if random.random() > 0.4:
                return
                
        # Get viral burst count from config, defaulting to 5 if not specified
        num_viruses = environment.config.get("simulation_settings", {}).get("viral_burst_count", 5)
        
        # Initialize list to hold new viruses
        new_viruses = []
        
        # Create new viruses based on viral burst count
        for i in range(num_viruses):
            # Create position variation
            offset_x = np.random.uniform(-15, 15)
            offset_y = np.random.uniform(-15, 15)
            
            # Get size range from config instead of multiplying parent size
            org_config = environment.config.get("organism_types", {}).get("Adenovirus", {})
            min_size, max_size = org_config.get("size_range", [2, 3])  # Default to [2, 3] if not found
            new_size = np.random.uniform(min_size, max_size)
            
            # Get speed range from config
            min_speed, max_speed = org_config.get("speed_range", [1.1, 2.3])  # Default to [1.1, 2.3] if not found
            new_speed = np.random.uniform(min_speed, max_speed)
            
            # Create slight color variation
            r, g, b = self.color
            color_mutation = 15
            new_color = (
                max(0, min(255, r + np.random.randint(-color_mutation, color_mutation))),
                max(0, min(255, g + np.random.randint(-color_mutation, color_mutation))),
                max(0, min(255, b + np.random.randint(-color_mutation, color_mutation)))
            )
            
            # Create new virus
            child = Adenovirus(
                self.x + offset_x,
                self.y + offset_y,
                new_size,
                new_color,
                new_speed
            )
            
            # DNA inheritance with low mutation chance
            child.dna = self.dna.copy()
            if random.random() < 0.05 * environmental_bonus:  # Lower mutation rate for DNA virus
                mutation_point = random.randint(0, len(child.dna) - 1)
                child.dna[mutation_point] = random.randint(0, 1)
            
            # Give child energy
            child.energy = 110  # Slightly more initial energy
            child._apply_dna_effects()
            
            # Add to environment
            if environment.simulation:
                environment.simulation.organisms.append(child)
                
            # Add to list of new viruses
            new_viruses.append(child)
        
        # Consume energy for reproduction (DNA virus uses more energy per reproduction)
        self.energy -= 35 + (num_viruses * 3.5)
        
        # Set cooldown to prevent immediate reproduction (DNA virus takes longer to replicate)
        self.replication_cooldown = 40
        
        return new_viruses