from dataclasses import dataclass, field
from typing import Dict

@dataclass
class FluidBatch:
    """
    Represents a packet of fluid at a specific location.
    Tracks total mass and the ratio of chemical components.
    """
    mass: float = 0.0  # kg
    
    # Composition: Normalized dictionary { 'ChemicalName': Fraction (0.0-1.0) }
    # Example: { 'Water': 0.9, 'Rust': 0.1 }
    composition: Dict[str, float] = field(default_factory=dict)
    
    def volume(self, density=1000.0):
        # In a full sim, density depends on composition and P/T.
        # For prototype, assume liquid water density (1000 kg/m^3)
        return self.mass / density

    def add(self, other_mass, other_comp):
        """Mixes incoming fluid into this batch."""
        if other_mass <= 0: 
            return

        total_mass = self.mass + other_mass
        
        # Mix compositions
        # New_Frac = (Old_Mass * Old_Frac + Added_Mass * Added_Frac) / Total_Mass
        new_comp = {}
        all_keys = set(self.composition.keys()) | set(other_comp.keys())
        
        for key in all_keys:
            m1 = self.mass * self.composition.get(key, 0.0)
            m2 = other_mass * other_comp.get(key, 0.0)
            new_comp[key] = (m1 + m2) / total_mass
            
        self.mass = total_mass
        self.composition = new_comp

    def extract(self, amount_kg):
        """Removes a chunk of mass, returning the extracted FluidBatch."""
        if amount_kg > self.mass:
            amount_kg = self.mass
        
        if amount_kg <= 0:
            return FluidBatch(0.0)
            
        # The composition of the extracted chunk is identical to the source (Perfect Mixing)
        extracted = FluidBatch(amount_kg, self.composition.copy())
        
        self.mass -= amount_kg
        if self.mass < 0.0001: # Floating point cleanup
            self.mass = 0.0
            
        return extracted