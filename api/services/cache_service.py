"""
Redis Caching Service for HR Resume Search
Optimizes frequent searches and expensive computations
"""

import redis
import json
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Union
from datetime import timedelta
import logging

from ..config import get_settings

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service for search optimization"""
    
    def __init__(self):
        self.settings = get_settings()
        self._redis_client = None
        self._connect()
    
    def _connect(self):
        """Initialize Redis connection"""
        try:
            if self.settings.redis_url:
                self._redis_client = redis.from_url(
                    self.settings.redis_url,
                    decode_responses=False,  # We'll handle encoding ourselves
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    max_connections=20
                )
                # Test connection
                self._redis_client.ping()
                logger.info("✅ Redis connection established")
            else:
                logger.warning("⚠️ Redis URL not configured, caching disabled")
                self._redis_client = None
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self._redis_client = None
    
    def _generate_cache_key(self, prefix: str, data: Union[str, Dict, List]) -> str:
        """Generate consistent cache key from data"""
        if isinstance(data, (dict, list)):
            # Sort and serialize for consistent keys
            serialized = json.dumps(data, sort_keys=True, default=str)
        else:
            serialized = str(data)
        
        # Hash for consistent length and avoid special characters
        hash_obj = hashlib.md5(serialized.encode('utf-8'))
        return f"{self.settings.redis_prefix}{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, cache_key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._redis_client:
            return None
        
        try:
            cached_data = self._redis_client.get(cache_key)
            if cached_data:
                return pickle.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")
            return None
    
    def set(
        self, 
        cache_key: str, 
        value: Any, 
        ttl: int = 300  # 5 minutes default
    ) -> bool:
        """Set value in cache with TTL"""
        if not self._redis_client:
            return False
        
        try:
            serialized_data = pickle.dumps(value)
            return self._redis_client.setex(cache_key, ttl, serialized_data)
        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            return False
    
    def delete(self, cache_key: str) -> bool:
        """Delete value from cache"""
        if not self._redis_client:
            return False
        
        try:
            return bool(self._redis_client.delete(cache_key))
        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        if not self._redis_client:
            return 0
        
        try:
            keys = self._redis_client.keys(f"{self.settings.redis_prefix}{pattern}*")
            if keys:
                return self._redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate pattern error for {pattern}: {e}")
            return 0
    
    # === Search-specific caching methods ===
    
    def cache_search_results(
        self, 
        search_params: Dict, 
        results: List[Dict], 
        ttl: int = 300
    ) -> bool:
        """Cache search results"""
        cache_key = self._generate_cache_key("search", search_params)
        return self.set(cache_key, {
            "results": results,
            "cached_at": str(timedelta.total_seconds(timedelta())),
            "params": search_params
        }, ttl)
    
    def get_cached_search_results(self, search_params: Dict) -> Optional[Dict]:
        """Get cached search results"""
        cache_key = self._generate_cache_key("search", search_params)
        return self.get(cache_key)
    
    def cache_candidate_profile(
        self, 
        candidate_id: str, 
        profile_data: Dict, 
        ttl: int = 600  # 10 minutes
    ) -> bool:
        """Cache complete candidate profile"""
        cache_key = self._generate_cache_key("candidate", candidate_id)
        return self.set(cache_key, profile_data, ttl)
    
    def get_cached_candidate_profile(self, candidate_id: str) -> Optional[Dict]:
        """Get cached candidate profile"""
        cache_key = self._generate_cache_key("candidate", candidate_id)
        return self.get(cache_key)
    
    def cache_colleague_analysis(
        self, 
        candidate_id: str, 
        colleagues_data: List[Dict], 
        ttl: int = 900  # 15 minutes
    ) -> bool:
        """Cache expensive colleague analysis"""
        cache_key = self._generate_cache_key("colleagues", candidate_id)
        return self.set(cache_key, colleagues_data, ttl)
    
    def get_cached_colleague_analysis(self, candidate_id: str) -> Optional[List[Dict]]:
        """Get cached colleague analysis"""
        cache_key = self._generate_cache_key("colleagues", candidate_id)
        return self.get(cache_key)
    
    def cache_skill_suggestions(
        self, 
        skill_query: str, 
        suggestions: List[str], 
        ttl: int = 3600  # 1 hour
    ) -> bool:
        """Cache skill suggestions for autocomplete"""
        cache_key = self._generate_cache_key("skills", skill_query.lower())
        return self.set(cache_key, suggestions, ttl)
    
    def get_cached_skill_suggestions(self, skill_query: str) -> Optional[List[str]]:
        """Get cached skill suggestions"""
        cache_key = self._generate_cache_key("skills", skill_query.lower())
        return self.get(cache_key)
    
    def cache_search_filters(
        self, 
        filters_data: Dict, 
        ttl: int = 1800  # 30 minutes
    ) -> bool:
        """Cache expensive filter aggregations"""
        cache_key = self._generate_cache_key("filters", "all")
        return self.set(cache_key, filters_data, ttl)
    
    def get_cached_search_filters(self) -> Optional[Dict]:
        """Get cached search filters"""
        cache_key = self._generate_cache_key("filters", "all")
        return self.get(cache_key)
    
    def cache_company_analysis(
        self, 
        company_name: str, 
        analysis_data: Dict, 
        ttl: int = 1200  # 20 minutes
    ) -> bool:
        """Cache company analysis data"""
        cache_key = self._generate_cache_key("company", company_name.lower())
        return self.set(cache_key, analysis_data, ttl)
    
    def get_cached_company_analysis(self, company_name: str) -> Optional[Dict]:
        """Get cached company analysis"""
        cache_key = self._generate_cache_key("company", company_name.lower())
        return self.get(cache_key)
    
    # === Cache invalidation methods ===
    
    def invalidate_candidate_cache(self, candidate_id: str) -> bool:
        """Invalidate all cache entries for a candidate"""
        patterns = [
            f"candidate:{candidate_id}",
            f"colleagues:*{candidate_id}*",
            f"search:*{candidate_id}*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.invalidate_pattern(pattern)
        
        logger.info(f"Invalidated {total_deleted} cache entries for candidate {candidate_id}")
        return total_deleted > 0
    
    def invalidate_search_cache(self) -> bool:
        """Invalidate all search-related cache"""
        patterns = ["search:", "filters:", "skills:"]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.invalidate_pattern(pattern)
        
        logger.info(f"Invalidated {total_deleted} search cache entries")
        return total_deleted > 0
    
    # === Cache statistics and monitoring ===
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        if not self._redis_client:
            return {"status": "disabled", "error": "Redis not connected"}
        
        try:
            info = self._redis_client.info()
            
            # Get key count by pattern
            patterns = ["search:", "candidate:", "colleagues:", "filters:", "skills:", "company:"]
            key_counts = {}
            
            for pattern in patterns:
                keys = self._redis_client.keys(f"{self.settings.redis_prefix}{pattern}*")
                key_counts[pattern.rstrip(":")] = len(keys)
            
            return {
                "status": "connected",
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "hit_rate": self._calculate_hit_rate(info),
                "key_counts": key_counts,
                "uptime_seconds": info.get("uptime_in_seconds")
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate"""
        try:
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = hits + misses
            
            if total == 0:
                return 0.0
            
            return round((hits / total) * 100, 2)
        except Exception:
            return 0.0
    
    def warm_cache(self) -> Dict[str, int]:
        """Warm up cache with commonly requested data"""
        if not self._redis_client:
            return {"status": "disabled"}
        
        warmed_count = {}
        
        try:
            # This would typically be called during application startup
            # or via a scheduled task to pre-populate frequently accessed data
            
            # Example: Pre-cache popular search filters
            # This would be implemented based on actual usage patterns
            
            logger.info("Cache warming completed")
            return {"status": "completed", "entries_warmed": sum(warmed_count.values())}
            
        except Exception as e:
            logger.error(f"Cache warming error: {e}")
            return {"status": "error", "error": str(e)}

# Global cache service instance
cache_service = CacheService()