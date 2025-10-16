"""
Unit tests for cache service.
"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open
from datetime import datetime, timedelta

from backend.services.cache_service import CacheService


class TestCacheService:
    """Test CacheService."""
    
    def test_cache_service_initialization(self):
        """Test cache service initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            
            with patch('backend.services.cache_service.SCENIC_CACHE_DIR', cache_dir), \
                 patch('backend.services.cache_service.FEASIBLE_PAIRS_CACHE_DIR', cache_dir):
                
                service = CacheService()
                assert service.ttl_hours == 24
                assert service.scenic_cache_dir == cache_dir
                assert service.feasible_pairs_cache_dir == cache_dir
    
    def test_is_cache_valid(self):
        """Test cache validity checking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            
            with patch('backend.services.cache_service.SCENIC_CACHE_DIR', cache_dir), \
                 patch('backend.services.cache_service.FEASIBLE_PAIRS_CACHE_DIR', cache_dir):
                
                service = CacheService()
                
                # Test with non-existent file
                fake_file = cache_dir / "nonexistent.json"
                assert not service._is_cache_valid(fake_file)
                
                # Test with valid file
                valid_file = cache_dir / "valid.json"
                valid_file.write_text("{}")
                assert service._is_cache_valid(valid_file)
                
                # Test with expired file (mock old timestamp)
                expired_file = cache_dir / "expired.json"
                expired_file.write_text("{}")
                
                # Mock the file to be older than TTL
                old_time = datetime.now() - timedelta(hours=25)
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value.st_mtime = old_time.timestamp()
                    assert not service._is_cache_valid(expired_file)
    
    def test_scenic_points_caching(self):
        """Test scenic points caching."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            
            with patch('backend.services.cache_service.SCENIC_CACHE_DIR', cache_dir), \
                 patch('backend.services.cache_service.FEASIBLE_PAIRS_CACHE_DIR', cache_dir):
                
                service = CacheService()
                region_id = "test_region"
                scenic_points = [
                    {"name": "Test Peak", "type": "Peak", "coords": [-3.0, 54.0]}
                ]
                
                # Test setting scenic points
                service.set_scenic_points(region_id, scenic_points)
                
                # Test getting scenic points
                result = service.get_scenic_points(region_id)
                assert result == scenic_points
                
                # Test getting non-existent region
                result = service.get_scenic_points("nonexistent")
                assert result is None
    
    def test_feasible_pairs_caching(self):
        """Test feasible pairs caching."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            
            with patch('backend.services.cache_service.SCENIC_CACHE_DIR', cache_dir), \
                 patch('backend.services.cache_service.FEASIBLE_PAIRS_CACHE_DIR', cache_dir):
                
                service = CacheService()
                region_id = "test_region"
                feasible_pairs = [
                    {"from": "A", "to": "B", "distance": 12.5}
                ]
                
                # Test setting feasible pairs
                service.set_feasible_pairs(region_id, feasible_pairs)
                
                # Test getting feasible pairs
                result = service.get_feasible_pairs(region_id)
                assert result == feasible_pairs
                
                # Test getting non-existent region
                result = service.get_feasible_pairs("nonexistent")
                assert result is None
    
    def test_invalidate_region_cache(self):
        """Test region cache invalidation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            
            with patch('backend.services.cache_service.SCENIC_CACHE_DIR', cache_dir), \
                 patch('backend.services.cache_service.FEASIBLE_PAIRS_CACHE_DIR', cache_dir):
                
                service = CacheService()
                region_id = "test_region"
                
                # Create cache files
                scenic_file = cache_dir / f"{region_id}.json"
                feasible_file = cache_dir / f"{region_id}.json"
                scenic_file.write_text("{}")
                feasible_file.write_text("{}")
                
                # Invalidate cache
                service.invalidate_region_cache(region_id)
                
                # Check files are deleted
                assert not scenic_file.exists()
                assert not feasible_file.exists()
    
    def test_clear_all_caches(self):
        """Test clearing all caches."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            
            with patch('backend.services.cache_service.SCENIC_CACHE_DIR', cache_dir), \
                 patch('backend.services.cache_service.FEASIBLE_PAIRS_CACHE_DIR', cache_dir):
                
                service = CacheService()
                
                # Create some cache files
                (cache_dir / "region1.json").write_text("{}")
                (cache_dir / "region2.json").write_text("{}")
                
                # Clear all caches
                service.clear_all_caches()
                
                # Check files are deleted
                assert len(list(cache_dir.glob("*.json"))) == 0
    
    def test_get_cache_stats(self):
        """Test cache statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            
            with patch('backend.services.cache_service.SCENIC_CACHE_DIR', cache_dir), \
                 patch('backend.services.cache_service.FEASIBLE_PAIRS_CACHE_DIR', cache_dir):
                
                service = CacheService()
                
                # Create some cache files
                region1_file = cache_dir / "region1.json"
                region1_file.write_text('{"test": "data"}')
                
                # Get stats
                stats = service.get_cache_stats()
                
                assert "scenic_cache" in stats
                assert "feasible_pairs_cache" in stats
                assert "region1" in stats["scenic_cache"]
                assert stats["scenic_cache"]["region1"]["valid"] is True
