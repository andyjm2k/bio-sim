"""
Environment Module for Bio-Sim
Handles environmental conditions and their effects on organisms
"""

import numpy as np

class Environment:
    """
    Class representing the environment in which organisms live.
    Manages environmental conditions like temperature, pH, nutrients, etc.
    """
    
    def __init__(self, width, height, config):
        """
        Initialize a new environment
        
        Args:
            width (int): Width of the environment
            height (int): Height of the environment
            config (dict): Configuration data
        """
        # Use world size from config if available, otherwise use window size
        self.width = config["simulation"].get("world_width", width)
        self.height = config["simulation"].get("world_height", height)
        self.config = config
        
        # Initialize random number generator
        self.random = np.random.RandomState()
        
        # Get environment type
        env_type = config["simulation"]["environment"]
        self.env_settings = config["environment_settings"].get(env_type, {})
        
        # Initialize environmental conditions
        self._initialize_conditions()
        
        # Track time
        self.tick_count = 0
        
        # Reference to the simulation (will be set by the simulation)
        self.simulation = None
    
    def _initialize_conditions(self):
        """Initialize the environmental conditions grids"""
        # Grid resolution (cells per dimension)
        self.grid_res = 20
        self.cell_width = self.width / self.grid_res
        self.cell_height = self.height / self.grid_res
        
        # Create grids for different environmental factors
        self.temperature_grid = np.ones((self.grid_res, self.grid_res)) * self.env_settings.get("temperature", 37.0)
        self.ph_grid = np.ones((self.grid_res, self.grid_res)) * self.env_settings.get("ph_level", 7.0)
        self.nutrient_grid = np.ones((self.grid_res, self.grid_res)) * self.env_settings.get("nutrients", 100)
        self.flow_rate_grid = np.ones((self.grid_res, self.grid_res)) * self.env_settings.get("flow_rate", 0.1)
        
        # Add some variation to make it more interesting
        self._add_environmental_variation()
    
    def _add_environmental_variation(self):
        """Add variation to environmental conditions"""
        # Temperature variation (±2°C)
        self.temperature_grid += np.random.normal(0, 0.5, (self.grid_res, self.grid_res))
        
        # pH variation (±0.5 pH)
        self.ph_grid += np.random.normal(0, 0.1, (self.grid_res, self.grid_res))
        
        # Nutrient variation (±20%)
        base_nutrients = self.env_settings.get("nutrients", 100)
        self.nutrient_grid += np.random.normal(0, base_nutrients * 0.05, (self.grid_res, self.grid_res))
        
        # Flow rate variation (±20%)
        base_flow = self.env_settings.get("flow_rate", 0.1)
        self.flow_rate_grid += np.random.normal(0, base_flow * 0.05, (self.grid_res, self.grid_res))
        
        # Ensure values are within reasonable ranges
        self.temperature_grid = np.clip(self.temperature_grid, 20, 50)
        self.ph_grid = np.clip(self.ph_grid, 3, 10)
        self.nutrient_grid = np.clip(self.nutrient_grid, 5, base_nutrients * 2)
        self.flow_rate_grid = np.clip(self.flow_rate_grid, 0, base_flow * 3)
        
        # Add "hotspots" and "coldspots" for more interesting dynamics
        for _ in range(3):
            # Temperature hotspot
            x, y = np.random.randint(0, self.grid_res, 2)
            self._create_hotspot(self.temperature_grid, x, y, 3, 5)
            
            # pH hotspot
            x, y = np.random.randint(0, self.grid_res, 2)
            self._create_hotspot(self.ph_grid, x, y, 1, 0.5)
            
            # Nutrient-rich area
            x, y = np.random.randint(0, self.grid_res, 2)
            self._create_hotspot(self.nutrient_grid, x, y, 5, base_nutrients)
    
    def _create_hotspot(self, grid, center_x, center_y, radius, intensity):
        """
        Create a hotspot (area of higher values) in a grid
        
        Args:
            grid (ndarray): The grid to modify
            center_x, center_y (int): Center coordinates of the hotspot
            radius (float): Radius of influence
            intensity (float): Maximum intensity at the center
        """
        for x in range(max(0, center_x - radius), min(self.grid_res, center_x + radius + 1)):
            for y in range(max(0, center_y - radius), min(self.grid_res, center_y + radius + 1)):
                # Calculate distance from center
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                # Apply if within radius
                if dist <= radius:
                    # Intensity falls off with distance
                    factor = (radius - dist) / radius
                    grid[x, y] += intensity * factor
    
    def update_environment_type(self, env_type):
        """
        Update the environment type and conditions
        
        Args:
            env_type (str): New environment type ('intestine', 'skin', 'mouth', etc.)
        """
        # Ensure the environment type exists in config
        if env_type not in self.config["environment_settings"]:
            print(f"Warning: Environment type '{env_type}' not found in config. Using defaults.")
            return
        
        # Update environment type
        self.config["simulation"]["environment"] = env_type
        self.env_settings = self.config["environment_settings"].get(env_type, {})
        
        # Store current conditions for smooth transition
        old_temp = np.mean(self.temperature_grid)
        old_ph = np.mean(self.ph_grid)
        old_nutrients = np.mean(self.nutrient_grid)
        old_flow = np.mean(self.flow_rate_grid)
        
        # Get new base values
        new_temp = self.env_settings.get("temperature", 37.0)
        new_ph = self.env_settings.get("ph_level", 7.0)
        new_nutrients = self.env_settings.get("nutrients", 100)
        new_flow = self.env_settings.get("flow_rate", 0.5)
        
        # Calculate differences for gradual transition
        temp_diff = new_temp - old_temp
        ph_diff = new_ph - old_ph
        nutrients_diff = new_nutrients - old_nutrients
        flow_diff = new_flow - old_flow
        
        # Apply 50% of the change immediately, rest will happen gradually
        self.temperature_grid += temp_diff * 0.5
        self.ph_grid += ph_diff * 0.5
        self.nutrient_grid += nutrients_diff * 0.5
        self.flow_rate_grid += flow_diff * 0.5
        
        # Flag for gradual transition over next several updates
        self.transitioning = True
        self.transition_target = {
            "temperature": new_temp,
            "ph": new_ph,
            "nutrients": new_nutrients,
            "flow": new_flow
        }
        self.transition_steps = 100  # Number of steps to complete transition
        self.transition_current = 0
        
        # Add some new variation and hotspots based on new environment
        self._add_environmental_variation()
        
        print(f"Environment transitioning to {env_type}: Temp={new_temp}°C, pH={new_ph}, Nutrients={new_nutrients}")
        
    def update(self):
        """Update the environment for the current simulation tick"""
        # Increment tick count
        self.tick_count += 1
        
        # Handle environment transition if in progress
        if hasattr(self, 'transitioning') and self.transitioning:
            self._update_transition()
        
        # Replenish nutrients slightly
        self.nutrient_grid += 0.01
        
        # Apply flow effects - nutrients move according to flow rate
        self._apply_flow()
        
        # Every 500 ticks, create a small environmental shift
        if self.tick_count % 500 == 0:
            self._create_environmental_shift()
            
    def _update_transition(self):
        """Update environmental transition"""
        self.transition_current += 1
        
        # Calculate transition progress (0 to 1)
        if self.transition_steps > 0:
            progress = self.transition_current / self.transition_steps
        else:
            progress = 1
            
        # If transition complete
        if progress >= 1:
            self.transitioning = False
            return
        
        # Get current averages
        current_temp = np.mean(self.temperature_grid)
        current_ph = np.mean(self.ph_grid)
        current_nutrients = np.mean(self.nutrient_grid)
        current_flow = np.mean(self.flow_rate_grid)
        
        # Calculate increments needed
        temp_increment = (self.transition_target["temperature"] - current_temp) * 0.05
        ph_increment = (self.transition_target["ph"] - current_ph) * 0.05
        nutrients_increment = (self.transition_target["nutrients"] - current_nutrients) * 0.05
        flow_increment = (self.transition_target["flow"] - current_flow) * 0.05
        
        # Apply increments
        self.temperature_grid += temp_increment
        self.ph_grid += ph_increment
        self.nutrient_grid += nutrients_increment
        self.flow_rate_grid += flow_increment
    
    def _apply_flow(self):
        """Apply flow effects to nutrients"""
        # Simple flow model - nutrients diffuse slightly in each direction
        # and are carried in the direction of flow
        
        # Create a copy of the current nutrient grid
        new_nutrients = self.nutrient_grid.copy()
        
        for x in range(self.grid_res):
            for y in range(self.grid_res):
                # Get flow rate and direction (simplified to be rightward for now)
                flow = self.flow_rate_grid[x, y]
                
                # Calculate diffusion and flow
                diffusion_rate = 0.01
                flow_rate = flow * 0.1
                
                # Apply to neighboring cells
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    
                    # Skip if outside grid
                    if nx < 0 or nx >= self.grid_res or ny < 0 or ny >= self.grid_res:
                        continue
                    
                    # Natural diffusion in all directions
                    transfer = self.nutrient_grid[x, y] * diffusion_rate
                    
                    # Additional flow in the flow direction (simplified to right/down)
                    if dx > 0 or dy > 0:  # Right or down
                        transfer += self.nutrient_grid[x, y] * flow_rate
                    
                    new_nutrients[x, y] -= transfer
                    new_nutrients[nx, ny] += transfer
        
        # Update nutrient grid
        self.nutrient_grid = new_nutrients
        
        # Ensure values are within reasonable ranges
        self.nutrient_grid = np.clip(self.nutrient_grid, 5, 200)
    
    def _create_environmental_shift(self):
        """Create a small environmental shift to simulate changing conditions"""
        # Random temperature shift
        temp_shift = np.random.normal(0, 1)
        self.temperature_grid += temp_shift
        
        # Random pH shift
        ph_shift = np.random.normal(0, 0.2)
        self.ph_grid += ph_shift
        
        # Ensure values are within reasonable ranges
        self.temperature_grid = np.clip(self.temperature_grid, 20, 50)
        self.ph_grid = np.clip(self.ph_grid, 3, 10)
    
    def get_grid_cell(self, x, y):
        """
        Convert world coordinates to grid cell coordinates
        
        Args:
            x, y (float): World coordinates
            
        Returns:
            tuple: Grid cell coordinates (cell_x, cell_y)
        """
        cell_x = int(min(self.grid_res - 1, max(0, x // self.cell_width)))
        cell_y = int(min(self.grid_res - 1, max(0, y // self.cell_height)))
        return cell_x, cell_y
    
    def get_conditions_at(self, x, y):
        """
        Get environmental conditions at the specified world coordinates
        
        Args:
            x, y (float): World coordinates
            
        Returns:
            dict: Dictionary of environmental conditions
        """
        cell_x, cell_y = self.get_grid_cell(x, y)
        
        return {
            "temperature": self.temperature_grid[cell_x, cell_y],
            "ph_level": self.ph_grid[cell_x, cell_y],
            "nutrients": self.nutrient_grid[cell_x, cell_y],
            "flow_rate": self.flow_rate_grid[cell_x, cell_y]
        }
    
    def consume_nutrients(self, x, y, amount):
        """
        Consume nutrients at the specified location
        
        Args:
            x, y (float): World coordinates
            amount (float): Amount of nutrients to consume
            
        Returns:
            float: Actual amount consumed
        """
        cell_x, cell_y = self.get_grid_cell(x, y)
        
        # Limit consumption to available nutrients
        actual_consumption = min(amount, self.nutrient_grid[cell_x, cell_y])
        
        # Update nutrient grid
        self.nutrient_grid[cell_x, cell_y] -= actual_consumption
        
        return actual_consumption

    def get_organisms_in_radius(self, x, y, radius):
        """
        Get organisms within a radius around a point.
        
        NOTE: This is a compatibility method for code that expects to get organisms from the
        environment. In this implementation, the environment doesn't have direct access to
        organisms, so this returns an empty list. The proper way to get nearby organisms is
        through the simulation's spatial grid.
        
        Args:
            x (float): Center x coordinate
            y (float): Center y coordinate
            radius (float): Radius to search within
            
        Returns:
            list: Empty list (the environment doesn't track organisms directly)
        """
        # Print a debug message to console to help with diagnosing the architectural issue
        print(f"WARNING: Environment.get_organisms_in_radius called at ({x:.1f}, {y:.1f}) with radius {radius:.1f}")
        print("This method should be called from the simulation, not the environment.")
        print("The white_blood_cell.py scan_for_targets method should be updated to accept a list of nearby organisms.")
        print("For now, returning an empty list as a fallback.")
        
        # This is a compatibility method that should ideally be in the simulation class
        # Return an empty list as a fallback
        return [] 
        
    def get_nearby_organisms(self, x, y, radius):
        """
        Get organisms near the specified coordinates.
        
        This method delegates to the simulation's spatial grid for finding nearby organisms.
        If the simulation reference is not set, returns an empty list.
        
        Args:
            x (float): Center x coordinate
            y (float): Center y coordinate
            radius (float): Radius to search within
            
        Returns:
            list: List of organisms near the specified location
        """
        if not self.simulation:
            print(f"WARNING: Environment.get_nearby_organisms called at ({x:.1f}, {y:.1f}) but simulation is not set")
            return []
            
        # Use the simulation's current organisms list
        nearby = []
        for organism in self.simulation.organisms:
            if not organism.is_alive:
                continue
                
            # Calculate distance
            dx = organism.x - x
            dy = organism.y - y
            distance = (dx**2 + dy**2)**0.5
            
            # Add if within radius
            if distance <= radius:
                nearby.append(organism)
                
        return nearby 