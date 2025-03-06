"""
Treatments Module for Bio-Sim
Defines synthetic treatments that can be introduced to the simulation
"""

class Treatment:
    """Base class for all treatments that can be applied to the simulation"""
    
    def __init__(self, name, description, duration, strength, color):
        """
        Initialize a treatment
        
        Args:
            name (str): Name of the treatment
            description (str): Description of the treatment's effects
            duration (int): How many simulation steps the treatment remains active
            strength (float): How powerful the treatment is (0.0-1.0)
            color (tuple): RGB color to represent this treatment visually
        """
        self.name = name
        self.description = description
        self.duration = duration
        self.strength = min(max(strength, 0.0), 1.0)  # Clamp between 0 and 1
        self.color = color
        self.remaining_duration = duration
        self.active = False
        
    def _get_organism_type(self, organism):
        """Helper method to get the type of an organism in a consistent way"""
        # Try different ways to get the class name or type
        result = None
        if hasattr(organism, "__class__") and hasattr(organism.__class__, "__name__"):
            result = organism.__class__.__name__
        elif hasattr(organism, "_type"):
            result = organism._type
        elif hasattr(organism, "type"):
            result = organism.type
        else:
            # Default fallback
            result = str(type(organism).__name__)
        
        return result
        
    def _matches_specificity(self, organism_type, specificity):
        """Helper method to check if an organism matches the specificity criteria"""
        if specificity is None:
            return True
        
        # Check each specificity criterion against the organism type
        for specific_type in specificity:
            if specific_type == organism_type:
                return True
        
        return False
        
    def apply(self, environment, organisms):
        """
        Apply treatment effects to the environment and organisms
        
        Args:
            environment: The simulation environment
            organisms (list): List of organisms in the simulation
            
        Returns:
            None
        """
        if self.active and self.remaining_duration > 0:
            self._apply_effects(environment, organisms)
            self.remaining_duration -= 1
            
            # Deactivate if duration has ended
            if self.remaining_duration <= 0:
                self.active = False
                
    def activate(self):
        """Activate the treatment"""
        self.active = True
        self.remaining_duration = self.duration
        
    def _apply_effects(self, environment, organisms):
        """
        Apply the specific effects of this treatment
        
        Args:
            environment: The simulation environment
            organisms (list): List of organisms in the simulation
            
        Returns:
            None
        """
        pass  # Implemented by subclasses
        
    def get_info(self):
        """Return information about the treatment for display"""
        return {
            "name": self.name,
            "description": self.description,
            "duration": self.duration,
            "remaining": self.remaining_duration,
            "strength": self.strength,
            "active": self.active,
            "color": self.color
        }


class Antibiotic(Treatment):
    """Treatment that targets and kills bacteria"""
    
    def __init__(self, name="Antibiotic", description="Targets and kills bacteria", 
                 duration=200, strength=0.7, specificity=None):
        """
        Initialize an antibiotic treatment
        
        Args:
            name (str): Name of the antibiotic
            description (str): Description of the antibiotic's effects
            duration (int): How many simulation steps the treatment remains active
            strength (float): How powerful the treatment is (0.0-1.0)
            specificity (list): List of bacteria types this targets (None = all)
        """
        super().__init__(name, description, duration, strength, (0, 191, 255))  # Deep Sky Blue
        self.specificity = specificity
        
    def _apply_effects(self, environment, organisms):
        """Apply antibiotic effects to bacteria"""
        for organism in organisms:
            # Check if organism is a bacteria by examining class name or type attribute
            org_type = self._get_organism_type(organism)
            
            if "Bacteria" in org_type:
                # Check if this organism matches the specificity criteria
                if self.specificity is None or self._matches_specificity(org_type, self.specificity):
                    # Calculate kill probability based on strength and bacteria's resistance
                    resistance = getattr(organism, "antibiotic_resistance", 0.0)
                    kill_chance = self.strength * (1.0 - resistance)
                    
                    # Apply a more significant health reduction
                    organism.health -= environment.random.uniform(0.3, 0.6) * self.strength
                    
                    # Chance to immediately kill the bacteria based on kill_chance
                    if environment.random.random() < kill_chance * 0.2:  # Scale down slightly for balance
                        organism.health = 0  # Kill the bacteria
                        
                    # Reduce energy to limit reproduction
                    if hasattr(organism, "energy"):
                        organism.energy *= (1.0 - kill_chance * 0.5)


class Antiviral(Treatment):
    """Treatment that inhibits virus reproduction and reduces viral load"""
    
    def __init__(self, name="Antiviral", description="Inhibits virus reproduction", 
                 duration=250, strength=0.6, specificity=None):
        """
        Initialize an antiviral treatment
        
        Args:
            name (str): Name of the antiviral
            description (str): Description of the antiviral's effects
            duration (int): How many simulation steps the treatment remains active
            strength (float): How powerful the treatment is (0.0-1.0)
            specificity (list): List of virus types this targets (None = all)
        """
        super().__init__(name, description, duration, strength, (255, 105, 180))  # Hot Pink
        self.specificity = specificity
        
    def _apply_effects(self, environment, organisms):
        """Apply antiviral effects to viruses"""
        for organism in organisms:
            # Check if organism is a virus by examining class name or type attribute
            org_type = self._get_organism_type(organism)
            
            if "Virus" in org_type:
                # Check if this organism matches the specificity criteria
                if self.specificity is None or self._matches_specificity(org_type, self.specificity):
                    # Significantly increase reproduction cooldown
                    if hasattr(organism, "reproduction_cooldown"):
                        # Add a larger cooldown based on strength
                        cooldown_increase = int(25 * self.strength)
                        organism.reproduction_cooldown += max(15, cooldown_increase)
                    
                    # Reduce virus health
                    organism.health -= environment.random.uniform(0.2, 0.4) * self.strength
                    
                    # Reduce energy to inhibit reproduction
                    if hasattr(organism, "energy"):
                        # Reduce energy by 10-30% based on strength
                        organism.energy *= (1.0 - environment.random.uniform(0.1, 0.3) * self.strength)
                        
                    # Small chance to detach from host
                    if hasattr(organism, "host") and organism.host is not None:
                        if environment.random.random() < 0.1 * self.strength:
                            organism.host = None


class Probiotic(Treatment):
    """Treatment that introduces beneficial bacteria to the environment"""
    
    def __init__(self, name="Probiotic", description="Introduces beneficial bacteria", 
                 duration=300, strength=0.5, bacteria_type=None):
        """
        Initialize a probiotic treatment
        
        Args:
            name (str): Name of the probiotic
            description (str): Description of the probiotic's effects
            duration (int): How many simulation steps the treatment remains active
            strength (float): How powerful the treatment is (0.0-1.0)
            bacteria_type (str): Type of beneficial bacteria to introduce
        """
        super().__init__(name, description, duration, strength, (127, 255, 0))  # Chartreuse
        self.bacteria_type = bacteria_type or "BeneficialBacteria"
        self.spawn_cooldown = 0
        
    def _apply_effects(self, environment, organisms):
        """Introduce beneficial bacteria to the environment"""
        from src.organisms import create_organism
        
        # Introduce new beneficial bacteria periodically
        self.spawn_cooldown -= 1
        if self.spawn_cooldown <= 0:
            # Create new beneficial bacteria
            spawn_count = int(self.strength * 3) + 1
            for _ in range(spawn_count):
                # Random position in the environment
                x = environment.random.uniform(0, environment.width)
                y = environment.random.uniform(0, environment.height)
                
                # Create beneficial bacteria
                new_bacteria = create_organism(self.bacteria_type, x, y, environment)
                if new_bacteria:
                    organisms.append(new_bacteria)
                    
            # Reset cooldown (higher strength = faster spawning)
            self.spawn_cooldown = int(100 / self.strength)


class Immunization(Treatment):
    """Treatment that strengthens white blood cells against specific pathogens"""
    
    def __init__(self, name="Immunization", description="Boosts immune response", 
                 duration=400, strength=0.8, target_pathogens=None):
        """
        Initialize an immunization treatment
        
        Args:
            name (str): Name of the immunization
            description (str): Description of the immunization's effects
            duration (int): How many simulation steps the treatment remains active
            strength (float): How powerful the treatment is (0.0-1.0)
            target_pathogens (list): List of pathogen types this targets
        """
        super().__init__(name, description, duration, strength, (255, 215, 0))  # Gold
        self.target_pathogens = target_pathogens or ["Influenza", "Rhinovirus"]
        
    def _apply_effects(self, environment, organisms):
        """Boost immune system effectiveness against target pathogens"""
        # Enhance white blood cells' detection and attack capabilities
        for organism in organisms:
            org_type = self._get_organism_type(organism)
            
            if "BloodCell" in org_type or "Macrophage" in org_type or "TCell" in org_type:
                # Significantly increase detection range for immune cells
                if hasattr(organism, "detection_range"):
                    organism.detection_range_boost = self.strength * 2.5
                
                # Increase attack strength against targets
                if hasattr(organism, "attack_strength"):
                    # Only apply to target pathogens with a stronger boost
                    organism.target_boost = {
                        pathogen: self.strength * 1.0  # Full strength boost
                        for pathogen in self.target_pathogens
                    }
                    
                # Increase movement speed to chase pathogens better
                if hasattr(organism, "speed"):
                    organism.speed_boost = self.strength * 0.4
                    
            # Reduce health of targeted pathogens (representing antibody effects)
            else:
                for pathogen in self.target_pathogens:
                    if self._matches_specificity(org_type, [pathogen]):
                        # More significant health reduction
                        organism.health -= environment.random.uniform(0.05, 0.15) * self.strength
                        
                        # Chance to mark pathogen for targeting by immune cells
                        if hasattr(organism, "mark_with_antibodies") and environment.random.random() < self.strength * 0.3:
                            organism.mark_with_antibodies("general", self.strength * 0.7)


def create_treatment(treatment_type, **kwargs):
    """
    Factory function to create treatment instances
    
    Args:
        treatment_type (str): Type of treatment to create
        **kwargs: Additional arguments to pass to the treatment constructor
        
    Returns:
        Treatment: A new treatment instance
    """
    treatment_classes = {
        "antibiotic": Antibiotic,
        "antiviral": Antiviral,
        "probiotic": Probiotic,
        "immunization": Immunization
    }
    
    if treatment_type.lower() in treatment_classes:
        return treatment_classes[treatment_type.lower()](**kwargs)
    else:
        raise ValueError(f"Unknown treatment type: {treatment_type}") 