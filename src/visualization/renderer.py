"""
Renderer Module for Bio-Sim
Handles rendering the simulation with advanced visualization features
"""

import pygame
import numpy as np
import colorsys

class Renderer:
    """
    Renderer class responsible for visualizing the simulation.
    Handles drawing organisms, environment visualization, UI, and camera controls.
    """
    
    def __init__(self, screen, config):
        """
        Initialize a new renderer
        
        Args:
            screen: Pygame screen surface
            config (dict): Configuration data
        """
        self.screen = screen
        self.config = config
        self.width, self.height = screen.get_size()
        
        # Get world dimensions
        self.world_width = config["simulation"].get("world_width", self.width)
        self.world_height = config["simulation"].get("world_height", self.height)
        
        # Camera settings - start centered in the world
        self.zoom = 1.0
        self.camera_x = self.world_width / 2 - self.width / 2
        self.camera_y = self.world_height / 2 - self.height / 2
        
        # Auto-camera tracking
        self.auto_track = True  # Enable auto tracking by default
        self.selected_organism = None  # Will store a specific organism to follow, if selected
        self.show_organism_details = False  # Whether to show detailed info for the selected organism
        
        # Visualization settings
        vis_config = config.get("visualization", {})
        self.show_stats = vis_config.get("show_stats", True)
        self.show_grid = vis_config.get("show_grid", False)
        self.show_labels = vis_config.get("show_labels", True)
        self.theme = vis_config.get("theme", "dark")
        
        # UI elements
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 16)
        
        # Environment visualization
        self.show_environment = False  # Off by default
        self.env_view_mode = 0  # 0=temperature, 1=pH, 2=nutrients, 3=flow
        
        # Create color maps for environment visualization
        self._create_color_maps()
        
        # Stats tracking
        self.stats = {
            "fps": 0,
            "bacteria": 0,
            "virus": 0,
            "white_blood_cell": 0,
            "beneficial_bacteria": 0,
            "macrophage": 0,
            "tcell": 0
        }
        
        # Store current environment info
        self.current_environment = config["simulation"]["environment"]
        self.env_conditions = {}  # Will be populated during render
        
        # For selecting organisms
        self.selected_organism = None
    
    def _create_color_maps(self):
        """Create color maps for visualizing environmental conditions"""
        # Temperature: Blue (cold) to Red (hot)
        self.temp_colormap = []
        for i in range(256):
            # 0 = 20°C (blue), 255 = 50°C (red)
            t = i / 255.0
            r = min(1.0, max(0, 2 * t - 0.5))
            g = min(1.0, max(0, 2 - 2 * abs(t - 0.5)))
            b = min(1.0, max(0, 1.5 - 3 * t))
            self.temp_colormap.append((int(r * 255), int(g * 255), int(b * 255)))
        
        # pH: Red (acidic) to Purple (basic)
        self.ph_colormap = []
        for i in range(256):
            # 0 = pH 3 (red), 128 = pH 7 (green), 255 = pH 10 (purple)
            t = i / 255.0
            h = 0 + t * 0.8  # Hue ranges from red (0) to purple (0.8)
            s = 0.8
            v = 0.9
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            self.ph_colormap.append((int(r * 255), int(g * 255), int(b * 255)))
        
        # Nutrients: Dark green (low) to Bright green (high)
        self.nutrient_colormap = []
        for i in range(256):
            # 0 = 0 nutrients, 255 = 200 nutrients
            t = i / 255.0
            self.nutrient_colormap.append((
                int(50 * t),
                int(100 + 155 * t),
                int(50 * t)
            ))
        
        # Flow: White (low) to Blue (high)
        self.flow_colormap = []
        for i in range(256):
            # 0 = no flow, 255 = high flow
            t = i / 255.0
            self.flow_colormap.append((
                int(200 + 55 * (1 - t)),
                int(200 + 55 * (1 - t)),
                int(200 + 55 * t)
            ))
    
    def world_to_screen(self, x, y):
        """
        Convert world coordinates to screen coordinates
        
        Args:
            x, y (float): World coordinates
            
        Returns:
            tuple: Screen coordinates (screen_x, screen_y)
        """
        screen_x = int((x - self.camera_x) * self.zoom + self.width / 2)
        screen_y = int((y - self.camera_y) * self.zoom + self.height / 2)
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x, screen_y):
        """
        Convert screen coordinates to world coordinates
        
        Args:
            screen_x, screen_y (int): Screen coordinates
            
        Returns:
            tuple: World coordinates (world_x, world_y)
        """
        world_x = (screen_x - self.width / 2) / self.zoom + self.camera_x
        world_y = (screen_y - self.height / 2) / self.zoom + self.camera_y
        return world_x, world_y
    
    def handle_input(self, event):
        """
        Handle input events for camera control
        
        Args:
            event: Pygame event object
            
        Returns:
            bool: True if event was handled
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                # Convert screen coordinates to world coordinates
                mouse_x, mouse_y = pygame.mouse.get_pos()
                world_x, world_y = self.screen_to_world(mouse_x, mouse_y)
                
                # Check if an organism was clicked
                return False  # Let the simulation class handle organism selection
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                # Zoom in
                self.zoom *= 1.1
                return True
            elif event.key == pygame.K_MINUS:
                # Zoom out
                self.zoom /= 1.1
                if self.zoom < 0.1:
                    self.zoom = 0.1
                return True
            elif event.key == pygame.K_UP:
                # Pan up (camera moves down)
                self.camera_y -= 40 / self.zoom
                # Disable auto-tracking when manually moving the camera
                if self.auto_track:
                    self.auto_track = False
                    print("Auto tracking: OFF (disabled by manual camera movement)")
                return True
            elif event.key == pygame.K_DOWN:
                # Pan down (camera moves up)
                self.camera_y += 40 / self.zoom
                # Disable auto-tracking when manually moving the camera
                if self.auto_track:
                    self.auto_track = False
                    print("Auto tracking: OFF (disabled by manual camera movement)")
                return True
            elif event.key == pygame.K_LEFT:
                # Pan left (camera moves right)
                self.camera_x -= 40 / self.zoom
                # Disable auto-tracking when manually moving the camera
                if self.auto_track:
                    self.auto_track = False
                    print("Auto tracking: OFF (disabled by manual camera movement)")
                return True
            elif event.key == pygame.K_RIGHT:
                # Pan right (camera moves left)
                self.camera_x += 40 / self.zoom
                # Disable auto-tracking when manually moving the camera
                if self.auto_track:
                    self.auto_track = False
                    print("Auto tracking: OFF (disabled by manual camera movement)")
                return True
            elif event.key == pygame.K_g:
                # Toggle grid
                self.show_grid = not self.show_grid
                return True
            elif event.key == pygame.K_h:
                # Toggle stats
                self.show_stats = not self.show_stats
                return True
            elif event.key == pygame.K_TAB:
                # Cycle environment view mode
                self.cycle_visualization_mode()
                return True
        
        return False
    
    def clear(self):
        """Clear the screen"""
        if self.theme == "dark":
            self.screen.fill((10, 10, 30))
        else:
            self.screen.fill((240, 240, 250))
    
    def render_environment(self, environment):
        """
        Render the environment visualization
        
        Args:
            environment: Environment object to visualize
        """
        # Initialize the view flag if it doesn't exist
        if not hasattr(self, 'show_environment'):
            self.show_environment = False
            
        # Initialize view mode if it doesn't exist
        if not hasattr(self, 'env_view_mode'):
            self.env_view_mode = 0  # Default to temperature view
            
        if not self.show_environment:
            return
            
        # Choose the grid and colormap based on view mode
        if self.env_view_mode == 0:
            # Temperature
            grid = environment.temperature_grid
            colormap = self.temp_colormap
            min_val, max_val = 20, 50  # °C
        elif self.env_view_mode == 1:
            # pH
            grid = environment.ph_grid
            colormap = self.ph_colormap
            min_val, max_val = 3, 10  # pH
        elif self.env_view_mode == 2:
            # Nutrients
            grid = environment.nutrient_grid
            colormap = self.nutrient_colormap
            min_val, max_val = 0, 200  # arbitrary units
        else:
            # Flow rate
            grid = environment.flow_rate_grid
            colormap = self.flow_colormap
            min_val, max_val = 0, 1  # arbitrary units
        
        # Normalize grid values to 0-255 for color mapping
        normalized_grid = np.clip((grid - min_val) / (max_val - min_val), 0, 1) * 255
        
        # Draw environment grid
        cell_width = environment.width / environment.grid_res
        cell_height = environment.height / environment.grid_res
        
        for x in range(environment.grid_res):
            for y in range(environment.grid_res):
                # Get color for this cell
                color_idx = int(normalized_grid[x, y])
                color = colormap[min(255, max(0, color_idx))]
                
                # World coordinates of cell
                world_x = x * cell_width
                world_y = y * cell_height
                
                # Screen coordinates
                screen_x, screen_y = self.world_to_screen(world_x, world_y)
                screen_w = max(1, int(cell_width * self.zoom))
                screen_h = max(1, int(cell_height * self.zoom))
                
                # Draw cell
                pygame.draw.rect(
                    self.screen,
                    color,
                    (screen_x, screen_y, screen_w, screen_h)
                )
        
        # Add a small legend
        mode_names = ["Temperature", "pH", "Nutrients", "Flow Rate"]
        mode_units = ["°C", "pH", "", ""]
        
        legend_text = f"{mode_names[self.env_view_mode]}: {min_val}-{max_val}{mode_units[self.env_view_mode]}"
        legend_surf = self.font.render(legend_text, True, (255, 255, 255))
        self.screen.blit(legend_surf, (10, self.height - 30))
    
    def render_grid(self, environment):
        """
        Render a coordinate grid
        
        Args:
            environment: Environment object for size reference
        """
        if not self.show_grid:
            return
            
        # Draw grid lines
        grid_spacing = 100  # World units
        grid_color = (70, 70, 90) if self.theme == "dark" else (200, 200, 220)
        
        # Calculate visible grid area
        left, top = self.screen_to_world(0, 0)
        right, bottom = self.screen_to_world(self.width, self.height)
        
        # Adjust to grid
        left = (left // grid_spacing) * grid_spacing
        top = (top // grid_spacing) * grid_spacing
        
        # Draw vertical lines
        x = left
        while x <= right:
            start_x, start_y = self.world_to_screen(x, top)
            end_x, end_y = self.world_to_screen(x, bottom)
            
            # Only draw if visible
            if 0 <= start_x < self.width:
                pygame.draw.line(self.screen, grid_color, (start_x, start_y), (end_x, end_y), 1)
                
                # Draw coordinate label
                if self.show_labels:
                    label = self.small_font.render(str(int(x)), True, grid_color)
                    self.screen.blit(label, (start_x + 2, 2))
            
            x += grid_spacing
        
        # Draw horizontal lines
        y = top
        while y <= bottom:
            start_x, start_y = self.world_to_screen(left, y)
            end_x, end_y = self.world_to_screen(right, y)
            
            # Only draw if visible
            if 0 <= start_y < self.height:
                pygame.draw.line(self.screen, grid_color, (start_x, start_y), (end_x, end_y), 1)
                
                # Draw coordinate label
                if self.show_labels:
                    label = self.small_font.render(str(int(y)), True, grid_color)
                    self.screen.blit(label, (2, start_y + 2))
            
            y += grid_spacing
    
    def render_organisms(self, organisms):
        """
        Render all organisms
        
        Args:
            organisms (list): List of organisms to render
        """
        # Reset organism counts for stats
        for key in list(self.stats.keys()):
            if key != "fps":  # Don't reset fps
                self.stats[key] = 0
        
        # Initialize total WBC count
        total_wbc_count = 0
        
        # Ensure we have keys for all cell types we want to track
        for cell_type in ["neutrophil", "macrophage", "tcell", "redbloodcell", "platelet", "epithelialcell"]:
            if cell_type not in self.stats:
                self.stats[cell_type] = 0
        
        # Render each organism
        for organism in organisms:
            if not organism.is_alive:
                continue
                
            # Count by type for stats - dynamically add new types
            org_type = organism.get_type().lower()  # Convert to lowercase for consistency
            if org_type not in self.stats:
                self.stats[org_type] = 0
            self.stats[org_type] += 1
            
            # Also track specific immune cell types and other important cells
            if hasattr(organism, 'type'):
                org_specific_type = organism.type.lower()  # Convert to lowercase for consistency
                
                # Handle specific cell types we want to track
                if org_specific_type == "neutrophil":
                    self.stats["neutrophil"] += 1
                    total_wbc_count += 1
                elif org_specific_type == "macrophage":
                    self.stats["macrophage"] += 1
                    total_wbc_count += 1
                elif org_specific_type == "tcell":
                    self.stats["tcell"] += 1
                    total_wbc_count += 1
                elif org_specific_type == "redbloodcell":
                    self.stats["redbloodcell"] += 1
                elif org_specific_type == "platelet":
                    self.stats["platelet"] += 1
                elif org_specific_type == "epithelialcell":
                    self.stats["epithelialcell"] += 1
            
            # Count all immune cells as WBCs (this is a fallback if the above doesn't catch some)
            elif org_type.lower() in ["neutrophil", "macrophage", "tcell"] or "white_blood_cell" in org_type.lower():
                total_wbc_count += 1
            
            # Use the organism's custom render method if it exists
            if hasattr(organism, 'render'):
                organism.render(self.screen, self.camera_x, self.camera_y, self.zoom)
            else:
                # Fallback to default rendering if the organism doesn't have a custom render method
                # World to screen coordinates
                screen_x, screen_y = self.world_to_screen(organism.x, organism.y)
                screen_radius = max(1, int(organism.size * self.zoom))
                
                # Skip if not visible
                if (screen_x + screen_radius < 0 or screen_x - screen_radius > self.width or
                    screen_y + screen_radius < 0 or screen_y - screen_radius > self.height):
                    continue
                
                # Draw the organism
                pygame.draw.circle(
                    self.screen,
                    organism.color,
                    (screen_x, screen_y),
                    screen_radius
                )
                
                # Draw organism outline
                pygame.draw.circle(
                    self.screen,
                    (min(255, organism.color[0] + 40), 
                     min(255, organism.color[1] + 40), 
                     min(255, organism.color[2] + 40)),
                    (screen_x, screen_y),
                    screen_radius,
                    1
                )
            
            # Draw health indicator (outside the custom rendering path to ensure visibility)
            if organism.health < 100:
                screen_x, screen_y = self.world_to_screen(organism.x, organism.y)
                screen_radius = max(1, int(organism.size * self.zoom))
                health_pct = max(0, organism.health / 100)
                bar_width = max(4, screen_radius * 2)
                health_width = int(bar_width * health_pct)
                
                pygame.draw.rect(
                    self.screen,
                    (200, 0, 0),
                    (screen_x - bar_width // 2, screen_y - screen_radius - 4, bar_width, 2)
                )
                
                pygame.draw.rect(
                    self.screen,
                    (0, 200, 0),
                    (screen_x - bar_width // 2, screen_y - screen_radius - 4, health_width, 2)
                )
            
            # Draw target indicator for white blood cells
            if organism.get_type() == "white_blood_cell" and hasattr(organism, 'target') and organism.target:
                # Check if target is the new dictionary structure
                if isinstance(organism.target, dict) and 'organism' in organism.target:
                    target_organism = organism.target['organism']
                    if hasattr(target_organism, 'is_alive') and target_organism.is_alive:
                        screen_x, screen_y = self.world_to_screen(organism.x, organism.y)
                        target_x, target_y = self.world_to_screen(target_organism.x, target_organism.y)
                        pygame.draw.line(
                            self.screen,
                            (255, 50, 50),
                            (screen_x, screen_y),
                            (target_x, target_y),
                            1
                        )
                # Legacy support for direct organism reference
                elif hasattr(organism.target, 'is_alive') and organism.target.is_alive:
                    screen_x, screen_y = self.world_to_screen(organism.x, organism.y)
                    target_x, target_y = self.world_to_screen(organism.target.x, organism.target.y)
                    pygame.draw.line(
                        self.screen,
                        (255, 50, 50),
                        (screen_x, screen_y),
                        (target_x, target_y),
                        1
                    )
            
            # Draw host indicator for viruses
            if organism.get_type() == "virus" and hasattr(organism, "host") and organism.host:
                if organism.host.is_alive:
                    screen_x, screen_y = self.world_to_screen(organism.x, organism.y)
                    host_x, host_y = self.world_to_screen(organism.host.x, organism.host.y)
                    pygame.draw.line(
                        self.screen,
                        (255, 100, 255),
                        (screen_x, screen_y),
                        (host_x, host_y),
                        1
                    )
        
        # Store the total WBC count
        self.stats["wbc_total"] = total_wbc_count
        
        # Calculate total bacteria count by summing all bacteria types
        bacteria_total = 0
        for key in self.stats:
            # Check if the key contains 'bacteria' or is a specific bacteria type
            if 'bacteria' in key or key in ['ecoli', 'streptococcus', 'salmonella', 'staphylococcus']:
                bacteria_total += self.stats[key]
        
        # Update the bacteria total
        self.stats['bacteria'] = bacteria_total
    
    def render_stats(self, fps):
        """
        Render statistics overlay
        
        Args:
            fps (float): Current frames per second
        """
        if not self.show_stats:
            return
            
        self.stats["fps"] = int(fps)
        
        # Background for stats
        pygame.draw.rect(
            self.screen,
            (0, 0, 0, 128),
            (10, 10, 300, 250),  # Increased height to accommodate additional cell types
            border_radius=5
        )
        
        # Render stats text
        y_pos = 15
        stats_color = (255, 255, 255)
        
        # FPS
        fps_text = self.font.render(f"FPS: {self.stats['fps']}", True, stats_color)
        self.screen.blit(fps_text, (15, y_pos))
        y_pos += 20
        
        # World size and camera position
        world_text = self.small_font.render(f"World: {self.world_width}x{self.world_height}", True, stats_color)
        self.screen.blit(world_text, (15, y_pos))
        y_pos += 15
        
        # Camera position (rounded to integers for clarity)
        cam_text = self.small_font.render(f"Camera: ({int(self.camera_x)}, {int(self.camera_y)})", True, stats_color)
        self.screen.blit(cam_text, (15, y_pos))
        y_pos += 15
        
        # Environment info
        if hasattr(self, 'current_environment'):
            env_name = self.current_environment.capitalize()
            env_text = self.font.render(f"Environment: {env_name}", True, stats_color)
            self.screen.blit(env_text, (15, y_pos))
            y_pos += 20
            
            # Show current conditions
            if hasattr(self, 'env_conditions'):
                temp_text = self.small_font.render(f"Temp: {self.env_conditions['temperature']:.1f}°C", True, stats_color)
                self.screen.blit(temp_text, (15, y_pos))
                y_pos += 15
                
                ph_text = self.small_font.render(f"pH: {self.env_conditions['ph_level']:.1f}", True, stats_color)
                self.screen.blit(ph_text, (15, y_pos))
                y_pos += 15
        else:
            # Skip space for environment info
            y_pos += 50
        
        # Organism counts
        bacteria_text = self.font.render(f"Bacteria: {self.stats['bacteria']}", True, stats_color)
        self.screen.blit(bacteria_text, (15, y_pos))
        y_pos += 20
        
        virus_text = self.font.render(f"Viruses: {self.stats['virus']}", True, stats_color)
        self.screen.blit(virus_text, (15, y_pos))
        y_pos += 20
        
        # Display the total WBC count (includes all immune cells)
        wbc_text = self.font.render(f"WBCs: {self.stats['wbc_total']}", True, stats_color)
        self.screen.blit(wbc_text, (15, y_pos))
        
        # Show breakdown of immune cells in smaller text
        y_pos += 20
        neutrophil_count = self.stats.get('neutrophil', 0)
        macrophage_count = self.stats.get('macrophage', 0)
        tcell_count = self.stats.get('tcell', 0)
        
        # Use normalized organism type names for display
        neutrophil_name = self._normalize_organism_type('neutrophil')
        macrophage_name = self._normalize_organism_type('macrophage')
        tcell_name = self._normalize_organism_type('tcell')
        
        immune_breakdown = self.small_font.render(
            f"  {neutrophil_name}s: {neutrophil_count} | {macrophage_name}s: {macrophage_count} | {tcell_name}s: {tcell_count}", 
            True, 
            stats_color
        )
        self.screen.blit(immune_breakdown, (15, y_pos))
        y_pos += 20
        
        # Display red blood cells, platelets, and epithelial cells
        rbc_count = self.stats.get('redbloodcell', 0)
        platelet_count = self.stats.get('platelet', 0)
        epithelial_count = self.stats.get('epithelialcell', 0)
        
        # Use normalized organism type names for display
        rbc_name = self._normalize_organism_type('redbloodcell')
        platelet_name = self._normalize_organism_type('platelet')
        epithelial_name = self._normalize_organism_type('epithelialcell')
        
        # Red blood cells
        rbc_text = self.font.render(f"{rbc_name}s: {rbc_count}", True, stats_color)
        self.screen.blit(rbc_text, (15, y_pos))
        y_pos += 20
        
        # Platelets
        platelet_text = self.font.render(f"{platelet_name}s: {platelet_count}", True, stats_color)
        self.screen.blit(platelet_text, (15, y_pos))
        y_pos += 20
        
        # Epithelial cells
        epithelial_text = self.font.render(f"{epithelial_name}s: {epithelial_count}", True, stats_color)
        self.screen.blit(epithelial_text, (15, y_pos))
        
        # Show zoom level
        zoom_text = self.font.render(f"Zoom: {self.zoom:.1f}x", True, stats_color)
        self.screen.blit(zoom_text, (self.width - 100, 15))
        
        # Controls reminder
        controls_text = self.small_font.render("Controls: Arrow Keys = Pan | +/- = Zoom | E = Change Environment | V = Toggle View", True, stats_color)
        self.screen.blit(controls_text, (15, self.height - 15))
    
    def render_organism_details(self, organism):
        """
        Render detailed information about the selected organism
        
        Args:
            organism: The selected organism
        """
        if not organism or not self.show_organism_details:
            return
            
        # Create a semi-transparent background panel
        panel_width = 300
        panel_height = 220  # Increased height to accommodate name
        panel_x = 20
        panel_y = self.height - panel_height - 20
        
        # Draw panel
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((10, 10, 30, 220))  # Dark blue with alpha
        
        # Draw border
        pygame.draw.rect(panel, (100, 180, 255), (0, 0, panel_width, panel_height), 2)
        
        # Get organism specific type - try different ways to get the most specific type
        if hasattr(organism, 'organism_type'):
            org_type = organism.organism_type
        elif hasattr(organism, 'specific_type'):
            org_type = organism.specific_type
        else:
            # Get the class name as fallback
            org_type = organism.__class__.__name__
        
        # Get organism name - either from a name property or generate one based on type and ID
        if hasattr(organism, 'name') and organism.name:
            org_name = organism.name
        else:
            # Generate a name based on type and first 4 characters of ID
            id_short = organism.id[:4]
            org_name = f"{org_type}-{id_short}"
        
        # Title with organism name
        title_font = pygame.font.SysFont(None, 28)
        title = title_font.render(f"{org_name} Details", True, (200, 220, 255))
        panel.blit(title, (10, 10))
        
        # Attributes - using different colors for variety
        y_pos = 50
        line_height = 22
        
        # Draw basic properties
        detail_font = pygame.font.SysFont(None, 22)
        
        # Type information - show both specific type and general category
        type_text = detail_font.render(f"Type: {org_type}", True, (180, 180, 255))
        panel.blit(type_text, (10, y_pos))
        y_pos += line_height
        
        # Try to get the general category if available
        if hasattr(organism, 'get_type') and callable(getattr(organism, 'get_type')):
            category = organism.get_type()
            if category != org_type:  # Only show if different from specific type
                category_text = detail_font.render(f"Category: {category}", True, (180, 180, 255))
                panel.blit(category_text, (10, y_pos))
                y_pos += line_height
        
        id_text = detail_font.render(f"ID: {organism.id}", True, (180, 180, 255))
        panel.blit(id_text, (10, y_pos))
        y_pos += line_height
        
        # Position
        pos_text = detail_font.render(f"Position: ({organism.x:.1f}, {organism.y:.1f})", True, (180, 180, 255))
        panel.blit(pos_text, (10, y_pos))
        y_pos += line_height
        
        # Health and energy - with color indicating status
        health_color = (100, 255, 100) if organism.health > 70 else (255, 255, 100) if organism.health > 30 else (255, 100, 100)
        health_text = detail_font.render(f"Health: {organism.health:.1f}%", True, health_color)
        panel.blit(health_text, (10, y_pos))
        y_pos += line_height
        
        energy_color = (100, 255, 100) if organism.energy > 70 else (255, 255, 100) if organism.energy > 30 else (255, 100, 100)
        energy_text = detail_font.render(f"Energy: {organism.energy:.1f}%", True, energy_color)
        panel.blit(energy_text, (10, y_pos))
        y_pos += line_height
        
        # Age
        age_text = detail_font.render(f"Age: {organism.age}", True, (180, 180, 255))
        panel.blit(age_text, (10, y_pos))
        y_pos += line_height
        
        # Size and speed
        size_text = detail_font.render(f"Size: {organism.size:.1f}", True, (180, 180, 255))
        panel.blit(size_text, (10, y_pos))
        y_pos += line_height
        
        speed_text = detail_font.render(f"Speed: {organism.base_speed:.1f}", True, (180, 180, 255))
        panel.blit(speed_text, (10, y_pos))
        y_pos += line_height
        
        # DNA preview (first 10 bases)
        dna_preview = ''.join(organism.dna[:10]) + "..." if len(organism.dna) > 10 else ''.join(organism.dna)
        dna_text = detail_font.render(f"DNA: {dna_preview}", True, (180, 180, 255))
        panel.blit(dna_text, (10, y_pos))
        
        # Blit the panel onto the screen
        self.screen.blit(panel, (panel_x, panel_y))
    
    def render_all(self, environment, organisms, fps):
        """
        Render the complete simulation
        
        Args:
            environment: Environment object
            organisms: List of organisms
            fps: Current frames per second
        """
        # Auto-update camera position based on organisms
        if self.auto_track:
            self.update_camera_position(organisms)
            
        # Clear the screen
        self.clear()
        
        # Store current environment info
        self.current_environment = environment.config["simulation"]["environment"]
        
        # Store environment conditions
        self.env_conditions = {
            "temperature": np.mean(environment.temperature_grid),
            "ph_level": np.mean(environment.ph_grid),
            "nutrients": np.mean(environment.nutrient_grid),
            "flow_rate": np.mean(environment.flow_rate_grid)
        }
        
        # Render environment first (background layer)
        self.render_environment(environment)
        
        # Render grid
        if self.show_grid:
            self.render_grid(environment)
        
        # Render organisms
        self.render_organisms(organisms)
        
        # Render stats overlay
        if self.show_stats:
            self.stats["fps"] = fps
            self.render_stats(fps)
        
        # Render organism details if there's a selected organism
        if self.selected_organism and self.show_organism_details:
            # Check if the selected organism is still in the list
            for org in organisms:
                if org.id == self.selected_organism.id:
                    self.render_organism_details(org)
                    break
    
    def update_camera_position(self, organisms):
        """
        Updates the camera position to follow organisms
        
        Args:
            organisms (list): List of organisms in the simulation
        """
        # If no organisms, don't move the camera
        if not organisms:
            return
            
        # If tracking a specific organism
        if self.selected_organism and self.selected_organism in organisms and self.selected_organism.is_alive:
            # Center camera on selected organism
            self.camera_x = self.selected_organism.x
            self.camera_y = self.selected_organism.y
            return
            
        # Otherwise calculate the average position of all living organisms
        total_x = 0
        total_y = 0
        count = 0
        
        for organism in organisms:
            if getattr(organism, 'is_alive', True):
                total_x += organism.x
                total_y += organism.y
                count += 1
                
        if count > 0:
            # Set camera to the average position of all organisms
            target_x = total_x / count
            target_y = total_y / count
            
            # Smooth camera movement - move 5% of the distance to the target
            self.camera_x += (target_x - self.camera_x) * 0.05
            self.camera_y += (target_y - self.camera_y) * 0.05
    
    def toggle_auto_tracking(self):
        """Toggles automatic camera tracking of organisms"""
        self.auto_track = not self.auto_track
        self.selected_organism = None
        print(f"Auto tracking: {'ON' if self.auto_track else 'OFF'}")
    
    def toggle_environment_view(self):
        """Toggle the environment visualization on/off"""
        if not hasattr(self, 'show_environment'):
            self.show_environment = False
            
        self.show_environment = not self.show_environment
    
    def cycle_visualization_mode(self):
        """Cycle through environment visualization modes"""
        # Always cycle through all 4 modes regardless of whether environment view is on
        self.env_view_mode = (self.env_view_mode + 1) % 4
        modes = ["Temperature", "pH", "Nutrients", "Flow"]
        print(f"Environment view mode: {modes[self.env_view_mode]}")
        
        # Ensure environment view is enabled when cycling with Tab
        if not self.show_environment:
            self.show_environment = True
            print("Environment view: ON")
    
    def _normalize_organism_type(self, org_type):
        """
        Normalize organism type string for consistent display
        
        Args:
            org_type (str): Original organism type
            
        Returns:
            str: Normalized organism type with proper capitalization
        """
        # Handle special case for T-Cell
        if org_type.lower() == 'tcell':
            return 'T-Cell'
            
        # Capitalize first letter of each word
        return org_type[0].upper() + org_type[1:].lower() 