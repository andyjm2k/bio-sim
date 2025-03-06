"""
Treatment Panel Module for Bio-Sim
Provides a UI panel for applying treatments to the simulation
"""

import pygame
from src.utils.treatments import create_treatment

class TreatmentPanel:
    """
    UI panel for selecting and applying treatments to the simulation.
    Displays available treatments, their effects, and allows users to apply them.
    """
    
    def __init__(self, screen, config):
        """
        Initialize the treatment panel
        
        Args:
            screen: Pygame screen surface
            config (dict): Configuration data
        """
        self.screen = screen
        self.config = config
        
        # Panel positioning and appearance
        self.width = 200
        self.height = screen.get_height()
        self.x = screen.get_width() - self.width
        self.y = 0
        self.visible = False
        self.background_color = (30, 30, 40, 200)  # Semi-transparent dark blue
        self.text_color = (230, 230, 230)
        self.highlight_color = (60, 100, 160)
        self.button_color = (50, 70, 120)
        self.active_color = (100, 200, 100)
        
        # Fonts
        self.title_font = pygame.font.SysFont(None, 32)
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 16)
        
        # Treatment data
        self.treatments = []
        self.active_treatments = []
        self.selected_index = 0
        
        # Initialize default treatments
        self._initialize_treatments()
        
        # Panel components
        self.treatment_buttons = []
        self.apply_button_rect = pygame.Rect(self.x + 20, self.height - 60, self.width - 40, 40)
        
        # Scrolling
        self.scroll_offset = 0
        self.max_visible_treatments = 6
        
    def _initialize_treatments(self):
        """Initialize the available treatments in the panel"""
        # Standard treatments
        self.treatments = [
            create_treatment("antibiotic", name="Broad Spectrum Antibiotic", 
                            description="Effective against most bacteria", 
                            strength=0.7),
            create_treatment("antibiotic", name="Targeted Antibiotic", 
                            description="Specific against E. coli", 
                            strength=0.9, 
                            specificity=["EColi"]),
            create_treatment("antiviral", name="General Antiviral", 
                            description="Reduces viral reproduction", 
                            strength=0.6),
            create_treatment("antiviral", name="Flu Antiviral", 
                            description="Specifically targets influenza viruses", 
                            strength=0.8, 
                            specificity=["Influenza"]),
            create_treatment("probiotic", name="Beneficial Bacteria", 
                            description="Introduces helpful microbes", 
                            strength=0.5, 
                            bacteria_type="BeneficialBacteria"),
            create_treatment("immunization", name="Flu Vaccine", 
                            description="Boosts immunity against influenza", 
                            strength=0.8, 
                            target_pathogens=["Influenza"]),
            create_treatment("immunization", name="Common Cold Vaccine", 
                            description="Boosts immunity against rhinovirus", 
                            strength=0.7, 
                            target_pathogens=["Rhinovirus"])
        ]
        
    def toggle_visibility(self):
        """Toggle the visibility of the treatment panel"""
        self.visible = not self.visible
        if self.visible:
            # Show a message about active treatments when panel becomes visible
            active_count = len(self.active_treatments)
            if active_count > 0:
                treatment_names = ", ".join([t.name for t in self.active_treatments[:3]])
                if active_count > 3:
                    treatment_names += f" and {active_count - 3} more"
                print(f"Active treatments: {treatment_names}")
        
    def handle_event(self, event):
        """
        Handle user input events for the treatment panel
        
        Args:
            event: Pygame event
            
        Returns:
            bool: True if event was handled, False otherwise
        """
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check if mouse is in panel area - Fixed boundary check
            if mouse_pos[0] < self.x:
                return False
                
            # Print debug info to verify mouse position detection
            print(f"Treatment panel mouse click: {mouse_pos}, panel x: {self.x}")
                
            # Check treatment selection
            for i, rect in enumerate(self.treatment_buttons):
                if rect.collidepoint(mouse_pos):
                    self.selected_index = i + self.scroll_offset
                    return True
                    
            # Check apply button
            if self.apply_button_rect.collidepoint(mouse_pos):
                self._apply_selected_treatment()
                return True
                
            # Scroll handling
            if event.button == 4:  # Scroll up
                self._scroll(-1)
                return True
            elif event.button == 5:  # Scroll down
                self._scroll(1)
                return True
                
        elif event.type == pygame.KEYDOWN and self.visible:
            if event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
                self._adjust_scroll()
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.treatments) - 1, self.selected_index + 1)
                self._adjust_scroll()
                return True
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                self._apply_selected_treatment()
                return True
                
        return False
        
    def _scroll(self, direction):
        """
        Scroll the treatment list
        
        Args:
            direction (int): Scroll direction (positive = down, negative = up)
        """
        max_scroll = max(0, len(self.treatments) - self.max_visible_treatments)
        self.scroll_offset = max(0, min(self.scroll_offset + direction, max_scroll))
        
    def _adjust_scroll(self):
        """Adjust scroll position to ensure selected treatment is visible"""
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.max_visible_treatments:
            self.scroll_offset = self.selected_index - self.max_visible_treatments + 1
            
    def _apply_selected_treatment(self):
        """Apply the currently selected treatment to the simulation"""
        if 0 <= self.selected_index < len(self.treatments):
            treatment = self.treatments[self.selected_index]
            
            # Check if already active
            if treatment.active:
                return
                
            # Activate the treatment
            treatment.activate()
            
            # Add to active treatments list if not already there
            if treatment not in self.active_treatments:
                self.active_treatments.append(treatment)
                # Provide feedback that treatment was applied
                print(f"Applied treatment: {treatment.name} - {treatment.description}")
                # You could also trigger a visual effect here if desired
                
    def update(self, environment, organisms):
        """
        Update active treatments and their effects
        
        Args:
            environment: The simulation environment
            organisms (list): List of organisms in the simulation
        """
        # Update all active treatments
        for treatment in self.active_treatments[:]:
            treatment.apply(environment, organisms)
            
            # Remove inactive treatments from the active list
            if not treatment.active:
                self.active_treatments.remove(treatment)
                
    def render(self):
        """Render the treatment panel if visible"""
        if not self.visible:
            return
            
        # Create semi-transparent surface for panel background
        panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, self.background_color, 
                        (0, 0, self.width, self.height))
        self.screen.blit(panel_surface, (self.x, self.y))
        
        # Draw title
        title = self.title_font.render("Treatments", True, self.text_color)
        self.screen.blit(title, (self.x + (self.width - title.get_width()) // 2, 15))
        
        # Reset treatment buttons list before adding new ones
        self.treatment_buttons = []
        
        # Draw available treatments
        visible_treatments = self.treatments[self.scroll_offset:
                                           self.scroll_offset + self.max_visible_treatments]
                                           
        for i, treatment in enumerate(visible_treatments):
            index = i + self.scroll_offset
            y_pos = 60 + i * 60
            
            # Treatment button rectangle - ensure it's positioned correctly relative to panel
            button_rect = pygame.Rect(self.x + 10, y_pos, self.width - 20, 50)
            self.treatment_buttons.append(button_rect)
            
            # Debug info to verify button positions
            # print(f"Button {i}: {button_rect}, mouse can click: x={self.x+10} to {self.x+self.width-10}, y={y_pos} to {y_pos+50}")
            
            # Button color based on selection and active state
            if index == self.selected_index:
                button_color = self.highlight_color
            elif treatment.active:
                button_color = self.active_color
            else:
                button_color = self.button_color
                
            pygame.draw.rect(self.screen, button_color, button_rect, border_radius=5)
            
            # Treatment name
            name_text = self.font.render(treatment.name, True, self.text_color)
            self.screen.blit(name_text, (self.x + 15, y_pos + 5))
            
            # Treatment description
            desc_text = self.small_font.render(treatment.description, True, self.text_color)
            self.screen.blit(desc_text, (self.x + 15, y_pos + 25))
            
            # Treatment status if active
            if treatment.active:
                status_text = self.small_font.render(
                    f"Active: {treatment.remaining_duration} steps", True, self.text_color)
                self.screen.blit(status_text, (self.x + 15, y_pos + 40))
                
        # Draw scroll indicators if needed
        if self.scroll_offset > 0:
            pygame.draw.polygon(self.screen, self.text_color, 
                              [(self.x + self.width // 2, 45),
                               (self.x + self.width // 2 - 10, 55),
                               (self.x + self.width // 2 + 10, 55)])
                               
        if self.scroll_offset + self.max_visible_treatments < len(self.treatments):
            bottom_y = 60 + self.max_visible_treatments * 60 + 10
            pygame.draw.polygon(self.screen, self.text_color, 
                              [(self.x + self.width // 2, bottom_y + 10),
                               (self.x + self.width // 2 - 10, bottom_y),
                               (self.x + self.width // 2 + 10, bottom_y)])
                               
        # Make sure apply button has correct position
        self.apply_button_rect = pygame.Rect(self.x + 20, self.height - 60, self.width - 40, 40)
            
        # Draw apply button
        pygame.draw.rect(self.screen, self.button_color, self.apply_button_rect, border_radius=5)
        apply_text = self.font.render("Apply Treatment", True, self.text_color)
        self.screen.blit(apply_text, 
                       (self.x + (self.width - apply_text.get_width()) // 2, 
                        self.height - 60 + (40 - apply_text.get_height()) // 2))
                        
        # Draw active treatments section
        active_title = self.font.render("Active Treatments", True, self.text_color)
        active_y = self.height - 150
        self.screen.blit(active_title, 
                       (self.x + (self.width - active_title.get_width()) // 2, active_y))
                       
        # List active treatments
        if not self.active_treatments:
            none_text = self.small_font.render("None", True, self.text_color)
            self.screen.blit(none_text, 
                           (self.x + (self.width - none_text.get_width()) // 2, active_y + 30))
        else:
            for i, treatment in enumerate(self.active_treatments[:3]):  # Show max 3
                active_text = self.small_font.render(
                    f"{treatment.name}: {treatment.remaining_duration}", True, self.text_color)
                self.screen.blit(active_text, (self.x + 15, active_y + 25 + i * 20))
                
            # Indicator for more active treatments
            if len(self.active_treatments) > 3:
                more_text = self.small_font.render(
                    f"+ {len(self.active_treatments) - 3} more...", True, self.text_color)
                self.screen.blit(more_text, (self.x + 15, active_y + 25 + 3 * 20)) 