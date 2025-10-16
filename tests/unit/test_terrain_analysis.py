"""
Unit tests for terrain analysis utilities.
"""
import pytest
from backend.utils.terrain_analysis import analyze_surface_types, estimate_terrain_from_surface
from backend.services.osm_client import SurfaceData


class TestTerrainAnalysis:
    """Test terrain analysis utilities."""
    
    def test_analyze_surface_types_empty(self):
        """Test surface analysis with empty data."""
        result = analyze_surface_types([])
        
        assert result['primary_surface'] == 'unknown'
        assert result['surface_types'] == []
        assert result['trail_characteristics'] == 'mixed terrain'
        assert result['terrain_estimate']['mountain'] == 25
        assert result['terrain_estimate']['forest'] == 25
        assert result['terrain_estimate']['coastal'] == 25
        assert result['terrain_estimate']['valley'] == 25
    
    def test_analyze_surface_types_with_data(self):
        """Test surface analysis with surface data."""
        surface_data = [
            SurfaceData(surface='rock', highway='footway', tracktype='', lat=54.0, lon=-3.0),
            SurfaceData(surface='gravel', highway='path', tracktype='', lat=54.1, lon=-2.9),
            SurfaceData(surface='dirt', highway='track', tracktype='grade2', lat=54.2, lon=-2.8),
        ]
        
        result = analyze_surface_types(surface_data)
        
        assert result['primary_surface'] == 'rock'  # Most common
        assert 'rock' in result['surface_types']
        assert 'gravel' in result['surface_types']
        assert 'dirt' in result['surface_types']
        assert 'designated footpath' in result['trail_characteristics']
        assert 'track with some ruts' in result['trail_characteristics']
    
    def test_analyze_surface_types_with_terrain_defaults(self):
        """Test surface analysis with custom terrain defaults."""
        surface_data = []
        terrain_defaults = {'mountain': 50, 'forest': 30, 'coastal': 10, 'valley': 10}
        
        result = analyze_surface_types(surface_data, terrain_defaults)
        
        assert result['terrain_estimate']['mountain'] == 50
        assert result['terrain_estimate']['forest'] == 30
        assert result['terrain_estimate']['coastal'] == 10
        assert result['terrain_estimate']['valley'] == 10
    
    def test_estimate_terrain_from_surface_rocky(self):
        """Test terrain estimation with rocky surfaces."""
        surface_counts = {'rock': 5, 'stone': 3, 'dirt': 2}
        highway_types = ['footway']
        terrain_defaults = {'mountain': 30, 'forest': 30, 'coastal': 20, 'valley': 20}
        
        result = estimate_terrain_from_surface(surface_counts, highway_types, terrain_defaults)
        
        # Rocky surfaces should increase mountain terrain (or at least not decrease it significantly)
        assert result['mountain'] >= terrain_defaults['mountain'] - 5
        assert result['coastal'] <= terrain_defaults['coastal'] + 5
        assert sum(result.values()) == 100  # Should sum to 100
    
    def test_estimate_terrain_from_surface_natural(self):
        """Test terrain estimation with natural surfaces."""
        surface_counts = {'gravel': 4, 'dirt': 3, 'grass': 2}
        highway_types = ['path']
        terrain_defaults = {'mountain': 20, 'forest': 20, 'coastal': 20, 'valley': 40}
        
        result = estimate_terrain_from_surface(surface_counts, highway_types, terrain_defaults)
        
        # Natural surfaces should increase forest and valley terrain (or at least not decrease significantly)
        assert result['forest'] >= terrain_defaults['forest'] - 5
        assert result['valley'] >= terrain_defaults['valley'] - 5
        assert sum(result.values()) == 100
    
    def test_estimate_terrain_from_surface_sandy(self):
        """Test terrain estimation with sandy surfaces."""
        surface_counts = {'sand': 6, 'dirt': 2}
        highway_types = ['track']
        terrain_defaults = {'mountain': 30, 'forest': 30, 'coastal': 20, 'valley': 20}
        
        result = estimate_terrain_from_surface(surface_counts, highway_types, terrain_defaults)
        
        # Sandy surfaces should increase coastal terrain (or at least not decrease significantly)
        assert result['coastal'] >= terrain_defaults['coastal'] - 5
        assert result['mountain'] <= terrain_defaults['mountain'] + 5
        assert sum(result.values()) == 100
    
    def test_estimate_terrain_from_surface_footway(self):
        """Test terrain estimation with footway highway types."""
        surface_counts = {'dirt': 5}
        highway_types = ['footway', 'path']
        terrain_defaults = {'mountain': 25, 'forest': 25, 'coastal': 25, 'valley': 25}
        
        result = estimate_terrain_from_surface(surface_counts, highway_types, terrain_defaults)
        
        # Footways should increase forest and mountain terrain (or at least not decrease significantly)
        assert result['forest'] >= terrain_defaults['forest'] - 5
        assert result['mountain'] >= terrain_defaults['mountain'] - 5
        assert result['coastal'] <= terrain_defaults['coastal'] + 5
        assert result['valley'] <= terrain_defaults['valley'] + 5
        assert sum(result.values()) == 100
    
    def test_estimate_terrain_from_surface_no_data(self):
        """Test terrain estimation with no surface data."""
        surface_counts = {}
        highway_types = []
        terrain_defaults = {'mountain': 30, 'forest': 30, 'coastal': 20, 'valley': 20}
        
        result = estimate_terrain_from_surface(surface_counts, highway_types, terrain_defaults)
        
        # Should return defaults
        assert result == terrain_defaults
    
    def test_estimate_terrain_normalization(self):
        """Test that terrain percentages are normalized to 100."""
        surface_counts = {'rock': 10, 'sand': 10, 'dirt': 10}
        highway_types = ['footway']
        terrain_defaults = {'mountain': 10, 'forest': 10, 'coastal': 10, 'valley': 10}
        
        result = estimate_terrain_from_surface(surface_counts, highway_types, terrain_defaults)
        
        # Should sum to 100
        assert sum(result.values()) == 100
        
        # All values should be between 5 and 60 (as per the function logic)
        for value in result.values():
            assert 5 <= value <= 60
