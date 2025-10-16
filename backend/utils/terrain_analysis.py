"""
Terrain analysis utilities.
"""
from typing import Dict, List
from ..services.osm_client import SurfaceData


def analyze_surface_types(surface_data: List[SurfaceData], terrain_defaults: Dict[str, int] = None) -> Dict:
    """
    Analyze surface data to determine terrain characteristics.
    
    Args:
        surface_data: List of surface data from OSM
        terrain_defaults: Default terrain composition for the region
    
    Returns:
        Dictionary with terrain analysis
    """
    if not surface_data:
        return {
            'primary_surface': 'unknown',
            'surface_types': [],
            'trail_characteristics': 'mixed terrain',
            'terrain_estimate': terrain_defaults or {
                'mountain': 25,
                'forest': 25,
                'coastal': 25,
                'valley': 25
            }
        }
    
    # Count surface types
    surface_counts = {}
    highway_types = []
    tracktypes = []
    
    for data in surface_data:
        surface = data.surface
        if surface != 'unknown':
            surface_counts[surface] = surface_counts.get(surface, 0) + 1
        
        if data.highway:
            highway_types.append(data.highway)
        
        if data.tracktype:
            tracktypes.append(data.tracktype)
    
    # Determine primary surface
    if surface_counts:
        primary_surface = max(surface_counts, key=surface_counts.get)
    else:
        primary_surface = 'unpaved'  # Default for hiking trails
    
    # Create trail characteristics description
    characteristics = []
    
    # Surface-based characteristics
    surface_descriptions = {
        'paved': 'well-maintained path',
        'asphalt': 'paved surface',
        'concrete': 'paved surface',
        'unpaved': 'natural trail',
        'gravel': 'gravel path',
        'dirt': 'dirt track',
        'grass': 'grassy path',
        'mud': 'muddy conditions possible',
        'rock': 'rocky terrain',
        'stone': 'stone path',
        'sand': 'sandy surface'
    }
    
    if primary_surface in surface_descriptions:
        characteristics.append(surface_descriptions[primary_surface])
    
    # Highway type characteristics
    if 'footway' in highway_types or 'path' in highway_types:
        characteristics.append('designated footpath')
    elif 'track' in highway_types:
        characteristics.append('track/bridleway')
    elif 'bridleway' in highway_types:
        characteristics.append('bridleway')
    
    # Track type characteristics (for tracks)
    if tracktypes:
        tracktype_descriptions = {
            'grade1': 'smooth track',
            'grade2': 'track with some ruts',
            'grade3': 'rough track',
            'grade4': 'very rough track',
            'grade5': 'extremely rough track'
        }
        
        for tracktype in tracktypes:
            if tracktype in tracktype_descriptions:
                characteristics.append(tracktype_descriptions[tracktype])
    
    # Estimate terrain breakdown based on surface types and location
    terrain_estimate = estimate_terrain_from_surface(surface_counts, highway_types, terrain_defaults)
    
    return {
        'primary_surface': primary_surface,
        'surface_types': list(surface_counts.keys()),
        'trail_characteristics': ', '.join(characteristics) if characteristics else 'mixed terrain',
        'terrain_estimate': terrain_estimate
    }


def estimate_terrain_from_surface(surface_counts: Dict[str, int], highway_types: List[str], terrain_defaults: Dict[str, int] = None) -> Dict[str, int]:
    """
    Estimate terrain breakdown based on surface types and highway types.
    
    Args:
        surface_counts: Count of each surface type
        highway_types: List of highway types found
        terrain_defaults: Default terrain composition for the region
    
    Returns:
        Dictionary with terrain percentages
    """
    # Default terrain (can be overridden by region)
    terrain = terrain_defaults or {
        'mountain': 25,
        'forest': 25,
        'coastal': 25,
        'valley': 25
    }
    
    # Adjust based on surface types
    if surface_counts:
        total_surfaces = sum(surface_counts.values())
        
        # Rocky/stone surfaces suggest mountainous terrain
        rocky_surfaces = surface_counts.get('rock', 0) + surface_counts.get('stone', 0)
        if rocky_surfaces > 0:
            terrain['mountain'] += min(20, (rocky_surfaces / total_surfaces) * 40)
            terrain['coastal'] -= min(15, (rocky_surfaces / total_surfaces) * 30)
        
        # Gravel/dirt surfaces suggest forest/valley terrain
        natural_surfaces = surface_counts.get('gravel', 0) + surface_counts.get('dirt', 0) + surface_counts.get('grass', 0)
        if natural_surfaces > 0:
            terrain['forest'] += min(15, (natural_surfaces / total_surfaces) * 30)
            terrain['valley'] += min(10, (natural_surfaces / total_surfaces) * 20)
        
        # Sand surfaces suggest coastal terrain
        sand_surfaces = surface_counts.get('sand', 0)
        if sand_surfaces > 0:
            terrain['coastal'] += min(20, (sand_surfaces / total_surfaces) * 40)
            terrain['mountain'] -= min(10, (sand_surfaces / total_surfaces) * 20)
    
    # Adjust based on highway types
    if 'footway' in highway_types or 'path' in highway_types:
        # Designated footpaths often go through varied terrain
        terrain['forest'] += 5
        terrain['mountain'] += 5
        terrain['coastal'] -= 5
        terrain['valley'] -= 5
    
    # Normalize to ensure percentages add up to 100
    total = sum(terrain.values())
    for key in terrain:
        terrain[key] = max(5, min(60, round(terrain[key] / total * 100)))
    
    # Final normalization
    total = sum(terrain.values())
    for key in terrain:
        terrain[key] = round(terrain[key] / total * 100)
    
    return terrain
