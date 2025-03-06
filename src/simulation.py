"""
Bio-Sim: Human Microbiome Simulation
Main simulation module containing the BioSimulation class
"""

import os
import pygame
import numpy as np
from pygame.locals import *

# Import custom modules
from src.organisms import create_organism
from src.environment import Environment
from src.visualization import Renderer, TreatmentPanel
from src.utils import save_simulation, load_simulation, list_saved_simulations

class BioSimulation:
    """Main simulation class for the Bio-Sim project"""
    
    def __init__(self, config=None):
        """Initialize the simulation with given configuration"""
        self.config = config or {}
        self.running = True
        self.paused = False
        self.organisms = []
        self.save_path = None
        self.update_count = 0
        
        # Initialize pygame
        pygame.init()
        pygame.display.set_caption("Bio-Sim: Human Microbiome Simulation")
        
        # Set up the display
        sim_config = self.config.get("simulation", {})
        self.width = sim_config.get("width", 800)
        self.height = sim_config.get("height", 600)
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        
        # Create renderer and treatment panel
        self.renderer = Renderer(self.screen, self.config)
        self.treatment_panel = TreatmentPanel(self.screen, self.config)
        
        # Initialize environment
        self.environment = Environment(self.width, self.height, self.config)
        
        # Create any needed directories
        os.makedirs("data", exist_ok=True)
        
        # Initialize simulation state
        self.initialize_simulation()
        
    def initialize_simulation(self):
        """Set up the initial simulation state"""
        print("Initializing simulation...")
        
        # Clear existing organisms
        self.organisms = []
        
        # Set reference to simulation in environment
        self.environment.simulation = self
        
        # Get max organisms limit
        max_organisms = self.config.get("simulation_settings", {}).get("max_organisms", 200)
        print(f"Max organisms: {max_organisms}")
        
        # Create organisms from configuration
        for organism_type, org_config in self.config.get("organism_types", {}).items():
            count = org_config.get("count", 0)
            
            print(f"Creating {count} {organism_type} organisms...")
            
            for _ in range(count):
                # Random position within the full world dimensions, not just the visible window
                x = self.environment.random.uniform(0, self.environment.width)
                y = self.environment.random.uniform(0, self.environment.height)
                
                try:
                    # Create organism using factory function
                    organism = create_organism(organism_type, x, y, self.environment)
                    
                    if organism:
                        self.organisms.append(organism)
                except Exception as e:
                    print(f"Error creating {organism_type}: {e}")
        
        print(f"Created {len(self.organisms)} organisms.")
        
    def handle_events(self):
        """Process events and user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            
            # If treatment panel is visible, let it handle the event first
            if self.treatment_panel.visible and event.type == pygame.MOUSEBUTTONDOWN:
                # If the mouse is in the treatment panel area, let it handle the event
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if mouse_x >= self.treatment_panel.x:  # If mouse is in panel x range
                    if self.treatment_panel.handle_event(event):
                        continue  # Event was handled by treatment panel
            
            # Let the renderer try to handle the event
            if self.renderer.handle_input(event):
                continue
                
            # Then handle events specifically meant for the simulation
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    print(f"Simulation {'paused' if self.paused else 'resumed'}")
                elif event.key == pygame.K_t:
                    self.treatment_panel.toggle_visibility()
                elif event.key == pygame.K_e:
                    self.cycle_environment()
                elif event.key == pygame.K_v:
                    self.renderer.toggle_environment_view()
                elif event.key == pygame.K_r:
                    self.reset()
                elif event.key == pygame.K_s:
                    # Add more details about the key event
                    print(f"S key event detected: {event}")
                    print(f"Event timestamp: {pygame.time.get_ticks()}")
                    # Use a timestamp-based debounce to prevent double saves
                    current_time = pygame.time.get_ticks()
                    if not hasattr(self, 'last_save_time') or current_time - self.last_save_time > 500:  # 500ms debounce
                        self.last_save_time = current_time
                        self.save_simulation_dialog()
                    else:
                        print(f"Ignoring duplicate save command (debounce: {current_time - self.last_save_time}ms)")
                elif event.key == pygame.K_l:
                    self.load_simulation_dialog()
                continue
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Convert screen coordinates to world coordinates
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    world_x, world_y = self.renderer.screen_to_world(mouse_x, mouse_y)
                    
                    # Find the clicked organism
                    self.handle_organism_click(world_x, world_y)
                    continue
            
            # Pass any remaining events to treatment panel
            self.treatment_panel.handle_event(event)
    
    def handle_organism_click(self, world_x, world_y):
        """
        Handle clicks on organisms
        
        Args:
            world_x (float): World x-coordinate of click
            world_y (float): World y-coordinate of click
        """
        clicked_organism = None
        closest_distance = float('inf')
        
        # Find the closest organism to the click
        for organism in self.organisms:
            distance = ((organism.x - world_x) ** 2 + (organism.y - world_y) ** 2) ** 0.5
            
            # Check if click is within the organism's size (with a little buffer for easier selection)
            selection_radius = max(organism.size * 1.5, 10)  # Use at least 10 pixels for small organisms
            
            if distance <= selection_radius and distance < closest_distance:
                closest_distance = distance
                clicked_organism = organism
        
        # Update selected organism
        if clicked_organism:
            self.renderer.selected_organism = clicked_organism
            self.renderer.show_organism_details = True
            print(f"Selected {clicked_organism.get_type()} (ID: {clicked_organism.id})")
        else:
            # If clicking on empty space, deselect current organism
            self.renderer.selected_organism = None
    
    def update(self):
        """Update the simulation state for a single time step"""
        if self.paused:
            return
            
        # Apply treatment effects if any are active
        self.treatment_panel.update(self.environment, self.organisms)
            
        # Update environment
        self.environment.update()
        
        # Update all organisms
        self.update_organisms()
        
        # Check for new organisms via reproduction
        self.process_reproduction()
        
        # Spawn new cells based on configuration
        self.spawn_cells()
        
        # Remove dead organisms
        self.remove_dead_organisms()
        
        # Enforce population cap to maintain performance
        self.enforce_population_cap()
        
        # Increment update counter
        self.update_count += 1
    
    def spawn_cells(self):
        """Spawn new cells periodically based on configuration settings"""
        # Get cell spawn settings from config
        sim_settings = self.config.get("simulation_settings", {})
        cell_spawn_interval = sim_settings.get("cell_spawn_interval", 0)
        cell_spawn_count = sim_settings.get("cell_spawn_count", 0)
        cell_types = sim_settings.get("cell_types_to_spawn", [])
        
        # Skip if spawn interval is 0 (disabled) or if no cell types are specified
        if cell_spawn_interval == 0 or not cell_types or not cell_spawn_count:
            return
            
        # Check if it's time to spawn new cells based on the interval
        if self.update_count % cell_spawn_interval != 0:
            return
            
        # Get flow rate to determine entry point (higher flow rate = more from edges)
        flow_rate = self.environment.env_settings.get("flow_rate", 0.5)
        
        # Spawn cells
        for _ in range(cell_spawn_count):
            # Choose a random cell type from the configured list
            cell_type = np.random.choice(cell_types)
            
            # Determine spawn position based on flow rate
            # Higher flow: more likely to spawn from edges
            # Lower flow: more random positioning throughout
            if np.random.random() < flow_rate:
                # Spawn from edge (simulating flow bringing in new cells)
                # Choose a random edge (top, right, bottom, left)
                edge = np.random.randint(0, 4)
                if edge == 0:  # Top
                    x = np.random.uniform(0, self.environment.width)
                    y = 0
                elif edge == 1:  # Right
                    x = self.environment.width
                    y = np.random.uniform(0, self.environment.height)
                elif edge == 2:  # Bottom
                    x = np.random.uniform(0, self.environment.width)
                    y = self.environment.height
                else:  # Left
                    x = 0
                    y = np.random.uniform(0, self.environment.height)
            else:
                # Spawn at random position
                x = np.random.uniform(0, self.environment.width)
                y = np.random.uniform(0, self.environment.height)
            
            try:
                # Create new cell using factory function
                new_cell = create_organism(cell_type, x, y, self.environment)
                if new_cell:
                    self.organisms.append(new_cell)
            except Exception as e:
                print(f"Error creating {cell_type}: {e}")
    
    def update_organisms(self):
        """Update all organisms and handle their interactions"""
        # First update all organisms
        for organism in self.organisms:
            if organism.is_alive:
                organism.update(self.environment)
        
        # Spatial optimization - divide environment into grid cells
        cell_size = 50  # Size of each cell
        grid_width = (self.width // cell_size) + 1
        grid_height = (self.height // cell_size) + 1
        
        # Create empty grid
        spatial_grid = {}
        
        # Assign organisms to grid cells
        for organism in self.organisms:
            if not organism.is_alive:
                continue
                
            # Get cell coordinates
            cell_x = int(organism.x // cell_size)
            cell_y = int(organism.y // cell_size)
            cell_key = (cell_x, cell_y)
            
            # Add to grid
            if cell_key not in spatial_grid:
                spatial_grid[cell_key] = []
            spatial_grid[cell_key].append(organism)
        
        # Special handling for platelets - allow them to scan for other platelets
        platelet_activation_threshold = 3  # Number of damaged cells needed to activate platelets
        
        # Track damaged cells to activate nearby platelets
        damaged_cell_counts = {}  # Map of grid cell to count of damaged cells
        
        # Find damaged cells
        for cell_key, cell_organisms in spatial_grid.items():
            damaged_count = 0
            for organism in cell_organisms:
                if hasattr(organism, 'damaged') and organism.damaged:
                    damaged_count += 1
            if damaged_count > 0:
                damaged_cell_counts[cell_key] = damaged_count
                
        # Activate platelets near damaged cells
        for cell_key, damaged_count in damaged_cell_counts.items():
            if damaged_count >= platelet_activation_threshold:
                # Check this cell and adjacent cells for platelets
                cell_x, cell_y = cell_key
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        adj_key = (cell_x + dx, cell_y + dy)
                        if adj_key in spatial_grid:
                            for organism in spatial_grid[adj_key]:
                                if organism.get_type() == "Platelet" and hasattr(organism, 'activate'):
                                    # Activate the platelet
                                    organism.activate()
        
        # Allow platelets to scan for other platelets
        for organism in self.organisms:
            if organism.get_type() == "Platelet" and organism.is_alive and hasattr(organism, 'scan_for_platelets'):
                # Get nearby organisms from grid
                cell_x = int(organism.x // cell_size)
                cell_y = int(organism.y // cell_size)
                nearby_organisms = []
                
                # Check 3x3 grid of cells around the platelet
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        cell_key = (cell_x + dx, cell_y + dy)
                        if cell_key in spatial_grid:
                            nearby_organisms.extend(spatial_grid[cell_key])
                
                # Scan for nearby platelets
                organism.scan_for_platelets(nearby_organisms)
        
        # White blood cells scan for targets
        for organism in self.organisms:
            # Use organism.get_type() if defined, or fall back to class name
            org_type = getattr(organism, 'get_type', lambda: organism.__class__.__name__.lower())()
            if "neutrophil" in org_type.lower() and organism.is_alive:
                # Get nearby organisms from grid
                cell_x = int(organism.x // cell_size)
                cell_y = int(organism.y // cell_size)
                nearby_organisms = []
                
                # Check 3x3 grid of cells around the white blood cell
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        cell_key = (cell_x + dx, cell_y + dy)
                        if cell_key in spatial_grid:
                            nearby_organisms.extend(spatial_grid[cell_key])
                
                # Call scan_for_targets if method exists
                if hasattr(organism, 'scan_for_targets'):
                    organism.scan_for_targets(nearby_organisms, self.environment)
        
        # Handle interactions between organisms in same or adjacent cells
        for cell_key, cell_organisms in spatial_grid.items():
            # Process interactions within this cell
            for i, organism1 in enumerate(cell_organisms):
                if not organism1.is_alive:
                    continue
                    
                # Interact with other organisms in same cell
                for organism2 in cell_organisms[i+1:]:
                    if not organism2.is_alive:
                        continue
                        
                    # Calculate distance between organisms
                    dx = organism1.x - organism2.x
                    dy = organism1.y - organism2.y
                    distance = np.sqrt(dx**2 + dy**2)
                    
                    # If close enough, they can interact
                    interaction_radius = self.config.get("simulation_settings", {}).get("interaction_radius", 10)
                    if distance <= organism1.size + organism2.size + interaction_radius:
                        # Try interaction in both directions
                        if hasattr(organism1, 'interact'):
                            organism1.interact(organism2, self.environment)
                        if hasattr(organism2, 'interact'):
                            organism2.interact(organism1, self.environment)
    
    def process_reproduction(self):
        """Process reproduction for all organisms"""
        # Early return if no new organism slots available
        population_limit = self.config.get("simulation", {}).get("max_organisms", 1000)
        
        if len(self.organisms) >= population_limit:
            if not hasattr(self, '_last_reproduction_warning') or self._last_reproduction_warning + 500 < pygame.time.get_ticks():
                print(f"Population limit reached: {len(self.organisms)}/{population_limit}")
                self._last_reproduction_warning = pygame.time.get_ticks()
            return
        
        # Only allow reproduction if under the population cap
        available_slots = population_limit - len(self.organisms)
        
        # Track organisms that may reproduce
        bacteria_candidates = []
        virus_candidates = []
        white_blood_cell_candidates = []
        body_cell_candidates = []
        
        # Sort organisms by type
        for organism in self.organisms:
            if not organism.is_alive:
                continue
                
            # Safety check - get_type() should never be None
            org_type = organism.get_type()
            if not org_type:
                continue
                
            # Log what types are being processed for reproduction
            if "EpithelialCell" in str(type(organism)):
                # print(f"Found EpithelialCell in reproduction candidates: {organism}, can_reproduce={getattr(organism, 'can_reproduce', 'unknown')}")
                pass
            # Add to appropriate list
            if "bacteria" in org_type.lower() or org_type in ["Salmonella", "Staphylococcus", "EColi", "Streptococcus"]:
                bacteria_candidates.append(organism)
            elif "virus" in org_type.lower():
                virus_candidates.append(organism)
            elif "white_blood_cell" in org_type.lower():
                white_blood_cell_candidates.append(organism)
            elif "body_cell" in org_type.lower() and hasattr(organism, "can_reproduce") and organism.can_reproduce:
                # Only add body cells that specifically have can_reproduce=True
                body_cell_candidates.append(organism)
        
        new_organisms = []
        
        # First handle bacteria
        for organism in bacteria_candidates:
            # Stop if we've reached the limit
            if len(new_organisms) >= available_slots:
                break
                
            try:
                offspring = organism.reproduce(self.environment)
                if offspring:
                    if isinstance(offspring, list):
                        # Add multiple offspring and check slot limit
                        for child in offspring:
                            if len(new_organisms) < available_slots:
                                new_organisms.append(child)
                            else:
                                break
                    else:
                        # Single offspring
                        new_organisms.append(offspring)
            except Exception as e:
                print(f"Error during reproduction of {organism.get_type()}: {e}")
        
        # Handle white blood cells
        for organism in white_blood_cell_candidates:
            # Stop if we've reached the limit
            if len(new_organisms) >= available_slots:
                break
                
            try:
                offspring = organism.reproduce(self.environment)
                if offspring:
                    new_organisms.append(offspring)
            except Exception as e:
                print(f"Error during reproduction of {organism.get_type()}: {e}")
        
        # Handle body cells (only those with can_reproduce=True)
        for organism in body_cell_candidates:
            # Stop if we've reached the limit
            if len(new_organisms) >= available_slots:
                break
                
            try:
                offspring = organism.reproduce(self.environment)
                if offspring:
                    new_organisms.append(offspring)
            except Exception as e:
                print(f"Error during reproduction of {organism.get_type()}: {e}")
        
        # Now handle virus reproduction - give them priority to ensure they can replicate properly
        remaining_slots = available_slots - len(new_organisms)
        
        # If we still have slots, process virus reproduction
        if remaining_slots > 0:
            # Keep track of how many viruses we're adding from this reproduction
            viruses_added = 0
            max_virus_reproductions = 10  # Limit to avoid overwhelming the simulation
            
            for organism in virus_candidates:
                # Stop if we've added too many viruses in one update
                if viruses_added >= max_virus_reproductions:
                    break
                    
                # Extra safety check: ensure host references are valid
                if hasattr(organism, 'host'):
                    if organism.host is not None and not organism.host.is_alive:
                        # Host is dead, clear reference
                        # print(f"Safety: clearing dead host reference for {organism.get_name()} in reproduction processing")
                        organism.host = None
                        organism.dormant_counter = 0
                        continue
                    
                try:
                    offspring = organism.reproduce(self.environment)
                    if offspring:
                        if isinstance(offspring, list):
                            # Try to add all virus particles
                            for child in offspring:
                                if len(new_organisms) < available_slots:
                                    new_organisms.append(child)
                                    viruses_added += 1
                                else:
                                    break
                        else:
                            # Single offspring
                            new_organisms.append(offspring)
                            viruses_added += 1
                except Exception as e:
                    print(f"Error during reproduction of {organism.get_type()}: {e}")
                
                # Only process a few virus reproductions per update to avoid overloading
                if viruses_added >= max_virus_reproductions:
                    break
        
        # Add all new organisms to the simulation
        self.organisms.extend(new_organisms)
    
    def enforce_population_cap(self):
        """Enforce the maximum population limit if needed"""
        max_organisms = self.config.get("simulation_settings", {}).get("max_organisms", 0)
        
        # Skip if no limit or already under limit
        if max_organisms <= 0 or len(self.organisms) <= max_organisms:
            return
            
        # We need to remove some organisms to get under the cap
        excess = len(self.organisms) - max_organisms
        
        if excess > 0:
            # Count viruses and non-viruses separately
            viruses = []
            non_viruses = []
            
            # Separate viruses from other organisms
            for org in self.organisms:
                is_virus = hasattr(org, 'get_type') and "virus" in org.get_type().lower()
                if is_virus:
                    viruses.append(org)
                else:
                    non_viruses.append(org)
            
            #print(f"Population control: {len(viruses)} viruses, {len(non_viruses)} non-viruses")
            
            # Prioritization function
            def organism_priority(org):
                # Priority formula: age/energy ratio (higher is more likely to be culled)
                energy = getattr(org, 'energy', 100)
                age = getattr(org, 'age', 1)
                
                # Base priority is age/energy
                priority = age / max(1, energy)
                
                # Reduce priority (make less likely to cull) if virus
                if hasattr(org, 'get_type') and "virus" in org.get_type().lower():
                    priority *= 0.5  # Give viruses half the priority for culling
                    
                # Extra protection for young viruses (age < 10)
                if hasattr(org, 'get_type') and "virus" in org.get_type().lower() and age < 10:
                    priority *= 0.2  # Even less priority for newly created viruses
                
                return priority
            
            # If we have more non-viruses than excess, preferentially remove non-viruses first
            if len(non_viruses) >= excess:
                # Sort non-viruses by priority
                sorted_non_viruses = sorted(non_viruses, key=organism_priority, reverse=True)
                
                # Remove excess from non-viruses and keep all viruses
                self.organisms = sorted_non_viruses[excess:] + viruses
                print(f"Population cap enforced: removed {excess} non-virus organisms")
            else:
                # We need to remove some viruses too
                # Sort all organisms by priority
                sorted_organisms = sorted(self.organisms, key=organism_priority, reverse=True)
                
                # Remove excess organisms
                self.organisms = sorted_organisms[excess:]
                print(f"Population cap enforced: removed {excess} organisms (including some viruses)")
                
                # Count how many viruses were removed
                remaining_viruses = sum(1 for org in self.organisms if hasattr(org, 'get_type') and "virus" in org.get_type().lower())
                viruses_removed = len(viruses) - remaining_viruses
                if viruses_removed > 0:
                    print(f"WARNING: {viruses_removed} viruses were removed due to population cap")
    
    def remove_dead_organisms(self):
        """Remove dead organisms from the simulation"""
        # Filter out dead organisms
        self.organisms = [org for org in self.organisms if getattr(org, 'is_alive', True)]
    
    def render(self):
        """Render the current simulation state"""
        self.renderer.clear()
        fps = self.clock.get_fps()
        self.renderer.render_all(self.environment, self.organisms, fps)
        
        # Render treatment panel on top
        self.treatment_panel.render()
        
        pygame.display.flip()
    
    def run(self):
        """Main simulation loop"""
        print("Starting simulation. Press ESCAPE to exit.")
        print("Press SPACE to pause/resume the simulation.")
        print("Press T to toggle treatment panel.")
        print("Press E to cycle between environments (intestine, skin, mouth).")
        print("Press V to toggle environment visualization.")
        print("Press TAB to cycle between visualization modes (temperature, pH, nutrients, flow).")
        print("Press G to toggle grid display.")
        print("Press H to toggle statistics display.")
        print("Press I to toggle organism details display.")
        print("Press R to reset simulation.")
        print("Press S to save simulation state.")
        print("Press L to load simulation state.")
        print("Press C to toggle auto-camera tracking (follows organisms).")
        print("Use arrow keys to manually move camera when auto-tracking is off.")
        print("Click on an organism to view its detailed information.")
        
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.config.get("simulation", {}).get("fps", 60))
        
        pygame.quit()
        return 0
    
    def save_simulation_dialog(self):
        """Open dialog to save simulation state"""
        print("save_simulation_dialog called!")  # Debug log
        save_path = save_simulation(self.environment, self.organisms)
        print(f"Simulation saved to {save_path}")
    
    def load_simulation_dialog(self):
        """Open dialog to load simulation state"""
        saved_sims = list_saved_simulations()
        if saved_sims:
            # Load the most recent save
            self.environment, self.organisms = load_simulation(saved_sims[0])
            print(f"Loaded simulation from {saved_sims[0]}")
            
    def cycle_environment(self):
        """Cycle through available environment types"""
        # Get available environment types from config
        env_settings = self.config.get("environment_settings", {})
        available_envs = list(env_settings.keys())
        
        if not available_envs:
            print("No environment types defined in config")
            return
            
        # Get current environment
        current_env = self.environment.config["simulation"]["environment"]
        
        # Find the index of the current environment
        try:
            current_index = available_envs.index(current_env)
        except ValueError:
            # If current not in list, default to first
            current_index = -1
            
        # Calculate next environment index
        next_index = (current_index + 1) % len(available_envs)
        next_env = available_envs[next_index]
        
        # Update environment
        print(f"Changing environment: {current_env} -> {next_env}")
        self.environment.update_environment_type(next_env)
    
    def reset(self):
        """Reset the simulation to initial state"""
        print("Resetting simulation...")
        self.initialize_simulation() 