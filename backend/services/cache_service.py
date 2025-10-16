"""
Region-aware caching service.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..config import CACHE_TTL_HOURS, SCENIC_CACHE_DIR, FEASIBLE_PAIRS_CACHE_DIR


class CacheService:
    """Service for managing region-specific caches."""
    
    def __init__(self, ttl_hours: int = None):
        self.ttl_hours = ttl_hours or CACHE_TTL_HOURS
        self.scenic_cache_dir = SCENIC_CACHE_DIR
        self.feasible_pairs_cache_dir = FEASIBLE_PAIRS_CACHE_DIR
        
        # Ensure cache directories exist
        self.scenic_cache_dir.mkdir(parents=True, exist_ok=True)
        self.feasible_pairs_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file is still valid based on TTL."""
        if not cache_file.exists():
            return False
        
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        return file_age < timedelta(hours=self.ttl_hours)
    
    def get_scenic_points(self, region_id: str) -> Optional[List[Dict]]:
        """Get cached scenic points for a region."""
        cache_file = self.scenic_cache_dir / f"{region_id}.json"
        
        if not self._is_cache_valid(cache_file):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[LOG] Error loading scenic cache for {region_id}: {e}")
            return None
    
    def set_scenic_points(self, region_id: str, scenic_points: List[Dict]) -> None:
        """Cache scenic points for a region."""
        cache_file = self.scenic_cache_dir / f"{region_id}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(scenic_points, f, indent=2)
        except Exception as e:
            print(f"[LOG] Error saving scenic cache for {region_id}: {e}")
    
    def get_feasible_pairs(self, region_id: str) -> Optional[List[Dict]]:
        """Get cached feasible pairs for a region."""
        cache_file = self.feasible_pairs_cache_dir / f"{region_id}.json"
        
        if not self._is_cache_valid(cache_file):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[LOG] Error loading feasible pairs cache for {region_id}: {e}")
            return None
    
    def set_feasible_pairs(self, region_id: str, feasible_pairs: List[Dict]) -> None:
        """Cache feasible pairs for a region."""
        cache_file = self.feasible_pairs_cache_dir / f"{region_id}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(feasible_pairs, f, indent=2)
        except Exception as e:
            print(f"[LOG] Error saving feasible pairs cache for {region_id}: {e}")
    
    def invalidate_region_cache(self, region_id: str) -> None:
        """Invalidate all caches for a region."""
        scenic_file = self.scenic_cache_dir / f"{region_id}.json"
        feasible_file = self.feasible_pairs_cache_dir / f"{region_id}.json"
        
        for cache_file in [scenic_file, feasible_file]:
            if cache_file.exists():
                try:
                    cache_file.unlink()
                    print(f"[LOG] Invalidated cache: {cache_file}")
                except Exception as e:
                    print(f"[LOG] Error invalidating cache {cache_file}: {e}")
    
    def clear_all_caches(self) -> None:
        """Clear all cached data."""
        for cache_dir in [self.scenic_cache_dir, self.feasible_pairs_cache_dir]:
            for cache_file in cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                    print(f"[LOG] Cleared cache: {cache_file}")
                except Exception as e:
                    print(f"[LOG] Error clearing cache {cache_file}: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "scenic_cache": {},
            "feasible_pairs_cache": {}
        }
        
        # Scenic cache stats
        for cache_file in self.scenic_cache_dir.glob("*.json"):
            region_id = cache_file.stem
            file_size = cache_file.stat().st_size
            file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            
            stats["scenic_cache"][region_id] = {
                "size_bytes": file_size,
                "age_hours": file_age.total_seconds() / 3600,
                "valid": self._is_cache_valid(cache_file)
            }
        
        # Feasible pairs cache stats
        for cache_file in self.feasible_pairs_cache_dir.glob("*.json"):
            region_id = cache_file.stem
            file_size = cache_file.stat().st_size
            file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            
            stats["feasible_pairs_cache"][region_id] = {
                "size_bytes": file_size,
                "age_hours": file_age.total_seconds() / 3600,
                "valid": self._is_cache_valid(cache_file)
            }
        
        return stats
