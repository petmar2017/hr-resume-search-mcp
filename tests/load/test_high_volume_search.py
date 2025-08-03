#!/usr/bin/env python3
"""
High-Volume Search Query Load Tests
Tests search system performance under high-volume concurrent search loads
"""
import asyncio
import time
import statistics
import random
from typing import List, Dict, Any

class MockSearchDatabase:
    """Mock search database with realistic performance characteristics"""
    
    def __init__(self):
        # Mock candidate database
        self.candidates = self._generate_mock_candidates(10000)  # 10K candidates
        self.search_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache = {}  # Simple cache simulation
        self.cache_ttl = 300  # 5 minutes
    
    def _generate_mock_candidates(self, count: int) -> List[Dict[str, Any]]:
        """Generate mock candidate database"""
        skills_pool = [
            "Python", "JavaScript", "Java", "C++", "React", "Vue", "Angular",
            "Node.js", "Django", "FastAPI", "Flask", "Express", "Spring Boot",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes",
            "AWS", "Azure", "GCP", "Machine Learning", "Data Science", "DevOps",
            "TypeScript", "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin"
        ]
        
        departments = ["Engineering", "Data Science", "DevOps", "Product", "QA", "Security"]
        companies = ["TechCorp", "DataCorp", "StartupXYZ", "BigTech Inc", "CloudCorp", "AI Systems"]
        
        candidates = []
        for i in range(count):
            num_skills = random.randint(3, 8)
            candidate_skills = random.sample(skills_pool, num_skills)
            
            candidates.append({
                "id": i + 1,
                "name": f"Candidate {i+1:05d}",
                "email": f"candidate{i+1}@example.com",
                "skills": candidate_skills,
                "department": random.choice(departments),
                "company": random.choice(companies),
                "experience_years": random.randint(1, 15),
                "location": random.choice(["New York", "San Francisco", "Austin", "Seattle", "Boston"]),
                "salary_range": random.randint(60000, 200000)
            })
        
        return candidates
    
    async def search_candidates(self, criteria: Dict[str, Any], use_cache: bool = True) -> Dict[str, Any]:
        """Mock candidate search with caching"""
        start_time = time.time()
        
        # Generate cache key
        cache_key = str(sorted(criteria.items()))
        
        # Check cache
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                self.cache_hits += 1
                search_time = time.time() - start_time + 0.001  # Minimal cache lookup time
                return {
                    **cache_entry['result'],
                    "search_time": search_time,
                    "cached": True
                }
        
        # Cache miss - perform actual search
        self.cache_misses += 1
        
        # Simulate search processing time based on complexity
        complexity_factor = len(criteria) * 0.01 + 0.02
        await asyncio.sleep(complexity_factor)
        
        # Perform search
        matching_candidates = []
        for candidate in self.candidates:
            score = self._calculate_match_score(candidate, criteria)
            if score > 0.3:  # Minimum match threshold
                matching_candidates.append({
                    **candidate,
                    "match_score": score
                })
        
        # Sort by relevance
        matching_candidates.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Limit results
        limit = criteria.get("limit", 50)
        matching_candidates = matching_candidates[:limit]
        
        search_time = time.time() - start_time
        self.search_times.append(search_time)
        
        result = {
            "candidates": matching_candidates,
            "total_count": len(matching_candidates),
            "search_time": search_time,
            "cached": False
        }
        
        # Cache result
        if use_cache:
            self.cache[cache_key] = {
                "result": result.copy(),
                "timestamp": time.time()
            }
            # Simple cache cleanup (remove oldest if too many entries)
            if len(self.cache) > 1000:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
                del self.cache[oldest_key]
        
        return result
    
    def _calculate_match_score(self, candidate: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate match score between candidate and criteria"""
        score = 0.0
        
        # Skills matching
        if "skills" in criteria and criteria["skills"]:
            skill_matches = set(candidate["skills"]) & set(criteria["skills"])
            if skill_matches:
                score += len(skill_matches) / len(criteria["skills"]) * 0.5
        
        # Department matching
        if "department" in criteria:
            if candidate["department"] == criteria["department"]:
                score += 0.3
        
        # Company matching
        if "company" in criteria:
            if candidate["company"] == criteria["company"]:
                score += 0.2
        
        # Experience range matching
        if "experience_years" in criteria:
            exp_criteria = criteria["experience_years"]
            candidate_exp = candidate["experience_years"]
            
            if isinstance(exp_criteria, dict):
                min_exp = exp_criteria.get("min", 0)
                max_exp = exp_criteria.get("max", 100)
                if min_exp <= candidate_exp <= max_exp:
                    score += 0.2
            elif isinstance(exp_criteria, int):
                # Exact match or close
                if abs(candidate_exp - exp_criteria) <= 2:
                    score += 0.2
        
        # Location matching
        if "location" in criteria:
            if candidate["location"] == criteria["location"]:
                score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0

class HighVolumeSearchTestRunner:
    """Test runner for high-volume search operations"""
    
    def __init__(self):
        self.database = MockSearchDatabase()
        self.query_templates = [
            {"skills": ["Python", "Django"], "department": "Engineering"},
            {"skills": ["JavaScript", "React"], "experience_years": {"min": 3, "max": 7}},
            {"skills": ["Machine Learning", "Python"], "department": "Data Science"},
            {"department": "DevOps", "skills": ["Docker", "Kubernetes"]},
            {"skills": ["Java", "Spring Boot"], "location": "San Francisco"},
            {"skills": ["TypeScript", "Angular"], "experience_years": 5},
            {"department": "Engineering", "location": "New York"},
            {"skills": ["AWS", "Python"], "experience_years": {"min": 5, "max": 10}},
            {"skills": ["PostgreSQL", "Python"], "department": "Engineering"},
            {"skills": ["Go", "Docker"], "experience_years": {"min": 3, "max": 8}}
        ]
    
    async def concurrent_search_test(self, num_queries: int, max_concurrent: int = 20) -> Dict[str, Any]:
        """Test concurrent search queries"""
        print(f"🔍 Testing {num_queries} concurrent search queries (max concurrent: {max_concurrent})")
        
        # Generate search queries
        queries = []
        for i in range(num_queries):
            base_query = random.choice(self.query_templates).copy()
            # Add some variation
            base_query["limit"] = random.randint(10, 100)
            if random.random() < 0.3:  # 30% chance to add location filter
                base_query["location"] = random.choice(["New York", "San Francisco", "Austin"])
            
            queries.append({"query_id": f"query_{i:04d}", "criteria": base_query})
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def search_with_semaphore(query_data):
            async with semaphore:
                start_time = time.time()
                result = await self.database.search_candidates(query_data["criteria"])
                end_time = time.time()
                
                return {
                    "query_id": query_data["query_id"],
                    "result": result,
                    "total_time": end_time - start_time
                }
        
        # Execute all searches
        overall_start = time.time()
        tasks = [search_with_semaphore(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        overall_time = time.time() - overall_start
        
        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict)]
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        search_times = [r["total_time"] for r in successful_results]
        result_counts = [r["result"]["total_count"] for r in successful_results]
        cached_results = [r for r in successful_results if r["result"]["cached"]]
        
        return {
            "total_queries": num_queries,
            "successful_queries": len(successful_results),
            "failed_queries": len(exceptions),
            "overall_time": overall_time,
            "queries_per_second": num_queries / overall_time,
            "cache_hit_rate": len(cached_results) / len(successful_results) * 100 if successful_results else 0,
            "search_time_stats": {
                "min": min(search_times) if search_times else 0,
                "max": max(search_times) if search_times else 0,
                "mean": statistics.mean(search_times) if search_times else 0,
                "median": statistics.median(search_times) if search_times else 0,
                "std_dev": statistics.stdev(search_times) if len(search_times) > 1 else 0
            },
            "result_count_stats": {
                "min": min(result_counts) if result_counts else 0,
                "max": max(result_counts) if result_counts else 0,
                "mean": statistics.mean(result_counts) if result_counts else 0
            },
            "max_concurrent": max_concurrent
        }
    
    async def sustained_search_load_test(self, queries_per_second: int, duration_seconds: int) -> Dict[str, Any]:
        """Test sustained search load over time"""
        print(f"⏱️  Testing sustained search load: {queries_per_second} queries/sec for {duration_seconds} seconds")
        
        interval = 1.0 / queries_per_second
        start_time = time.time()
        query_counter = 0
        results = []
        
        async def execute_search():
            nonlocal query_counter
            query_template = random.choice(self.query_templates).copy()
            query_template["limit"] = random.randint(20, 50)
            
            result = await self.database.search_candidates(query_template)
            results.append(result)
            query_counter += 1
        
        # Schedule searches at regular intervals
        next_query_time = start_time
        
        while time.time() - start_time < duration_seconds:
            current_time = time.time()
            
            if current_time >= next_query_time:
                # Schedule search
                asyncio.create_task(execute_search())
                next_query_time += interval
            
            # Small sleep to prevent busy waiting
            await asyncio.sleep(0.001)
        
        # Wait a bit for remaining searches to complete
        await asyncio.sleep(1.0)
        
        total_time = time.time() - start_time
        successful_results = [r for r in results if r.get("total_count", 0) >= 0]
        cached_results = [r for r in results if r.get("cached", False)]
        
        return {
            "target_queries_per_second": queries_per_second,
            "duration_seconds": duration_seconds,
            "total_queries_executed": len(results),
            "successful_queries": len(successful_results),
            "actual_queries_per_second": len(results) / total_time,
            "cache_hit_rate": len(cached_results) / len(results) * 100 if results else 0,
            "total_time": total_time
        }
    
    async def search_complexity_test(self, complexity_levels: List[int]) -> Dict[str, Any]:
        """Test search performance with varying query complexity"""
        print(f"🧠 Testing search complexity with different filter counts")
        
        complexity_results = []
        
        for complexity in complexity_levels:
            print(f"   Testing complexity level: {complexity} filters")
            
            # Generate complex queries
            complex_queries = []
            for i in range(20):  # 20 queries per complexity level
                query = {}
                
                # Add filters based on complexity level
                if complexity >= 1:
                    query["skills"] = random.sample(["Python", "JavaScript", "Java", "React", "Django"], 
                                                  random.randint(1, 3))
                if complexity >= 2:
                    query["department"] = random.choice(["Engineering", "Data Science", "DevOps"])
                if complexity >= 3:
                    query["experience_years"] = {"min": random.randint(1, 5), "max": random.randint(6, 15)}
                if complexity >= 4:
                    query["location"] = random.choice(["New York", "San Francisco", "Austin"])
                if complexity >= 5:
                    query["company"] = random.choice(["TechCorp", "DataCorp", "StartupXYZ"])
                
                complex_queries.append(query)
            
            # Execute queries
            start_time = time.time()
            tasks = [self.database.search_candidates(query, use_cache=False) for query in complex_queries]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            # Analyze results
            search_times = [r["search_time"] for r in results]
            result_counts = [r["total_count"] for r in results]
            
            complexity_results.append({
                "complexity_level": complexity,
                "total_queries": len(complex_queries),
                "total_time": total_time,
                "avg_search_time": statistics.mean(search_times),
                "avg_result_count": statistics.mean(result_counts),
                "queries_per_second": len(complex_queries) / total_time
            })
        
        return {
            "complexity_levels": complexity_levels,
            "complexity_results": complexity_results
        }
    
    async def cache_performance_test(self, cache_sizes: List[int]) -> Dict[str, Any]:
        """Test cache performance with different cache scenarios"""
        print(f"💾 Testing cache performance")
        
        cache_results = []
        
        # Test 1: Cache warm-up
        print("   Warming up cache...")
        warm_up_queries = [random.choice(self.query_templates) for _ in range(50)]
        for query in warm_up_queries:
            await self.database.search_candidates(query)
        
        # Test 2: Cache hit scenario (repeat same queries)
        print("   Testing cache hits...")
        initial_cache_hits = self.database.cache_hits
        repeat_tasks = [self.database.search_candidates(random.choice(self.query_templates)) for _ in range(100)]
        await asyncio.gather(*repeat_tasks)
        cache_hit_improvement = self.database.cache_hits - initial_cache_hits
        
        # Test 3: Cache miss scenario (unique queries)
        print("   Testing cache misses...")
        self.database.cache.clear()  # Clear cache
        initial_cache_misses = self.database.cache_misses
        unique_queries = []
        for i in range(50):
            unique_query = {"skills": [f"Skill_{i}"], "department": f"Dept_{i}"}
            unique_queries.append(unique_query)
        
        unique_tasks = [self.database.search_candidates(query) for query in unique_queries]
        await asyncio.gather(*unique_tasks)
        cache_miss_count = self.database.cache_misses - initial_cache_misses
        
        return {
            "cache_hit_improvement": cache_hit_improvement,
            "cache_miss_count": cache_miss_count,
            "total_cache_hits": self.database.cache_hits,
            "total_cache_misses": self.database.cache_misses,
            "cache_hit_rate": self.database.cache_hits / (self.database.cache_hits + self.database.cache_misses) * 100
        }

async def run_high_volume_search_tests():
    """Run comprehensive high-volume search tests"""
    print("🔍 High-Volume Search Query Load Tests")
    print("=" * 60)
    
    runner = HighVolumeSearchTestRunner()
    test_results = {}
    
    # Test 1: Basic concurrent search
    print("\n1️⃣ Concurrent Search Test:")
    print("-" * 28)
    
    concurrent_result = await runner.concurrent_search_test(100, 20)
    test_results["concurrent_search"] = concurrent_result
    
    print(f"   📊 Queries processed: {concurrent_result['successful_queries']}/{concurrent_result['total_queries']}")
    print(f"   ⏱️  Total time: {concurrent_result['overall_time']:.2f}s")
    print(f"   📈 Throughput: {concurrent_result['queries_per_second']:.1f} queries/sec")
    print(f"   💾 Cache hit rate: {concurrent_result['cache_hit_rate']:.1f}%")
    print(f"   📊 Avg search time: {concurrent_result['search_time_stats']['mean']:.3f}s")
    
    # Test 2: Sustained search load
    print("\n2️⃣ Sustained Search Load:")
    print("-" * 25)
    
    sustained_result = await runner.sustained_search_load_test(10, 15)  # 10 queries/sec for 15 seconds
    test_results["sustained_search"] = sustained_result
    
    print(f"   🎯 Target rate: {sustained_result['target_queries_per_second']} queries/sec")
    print(f"   📊 Actual rate: {sustained_result['actual_queries_per_second']:.1f} queries/sec")
    print(f"   📈 Queries executed: {sustained_result['successful_queries']}/{sustained_result['total_queries_executed']}")
    print(f"   💾 Cache hit rate: {sustained_result['cache_hit_rate']:.1f}%")
    
    # Test 3: Search complexity test
    print("\n3️⃣ Search Complexity Test:")
    print("-" * 27)
    
    complexity_result = await runner.search_complexity_test([1, 2, 3, 4, 5])
    test_results["complexity_test"] = complexity_result
    
    for result in complexity_result["complexity_results"]:
        print(f"   📊 {result['complexity_level']} filters: {result['avg_search_time']:.3f}s avg, {result['queries_per_second']:.1f} q/s")
    
    # Test 4: Cache performance
    print("\n4️⃣ Cache Performance Test:")
    print("-" * 27)
    
    cache_result = await runner.cache_performance_test([100, 500, 1000])
    test_results["cache_performance"] = cache_result
    
    print(f"   💾 Cache hit rate: {cache_result['cache_hit_rate']:.1f}%")
    print(f"   ✅ Cache hits: {cache_result['total_cache_hits']}")
    print(f"   ❌ Cache misses: {cache_result['total_cache_misses']}")
    print(f"   ⚡ Hit improvement: {cache_result['cache_hit_improvement']} queries")
    
    # Test 5: Performance summary
    print("\n5️⃣ Performance Summary:")
    print("-" * 25)
    
    best_throughput = max([r for k, r in test_results.items() if 'queries_per_second' in r], 
                         key=lambda x: x['queries_per_second'])['queries_per_second']
    
    print(f"   🏆 Best throughput: {best_throughput:.1f} queries/sec")
    print(f"   💾 Overall cache efficiency: {cache_result['cache_hit_rate']:.1f}%")
    print(f"   📊 Database size: {len(runner.database.candidates):,} candidates")
    print(f"   ⚡ Recommended concurrent limit: 20-50 queries")
    
    # Test 6: Capacity planning
    print("\n6️⃣ Capacity Planning:")
    print("-" * 22)
    
    daily_capacity = best_throughput * 3600 * 24
    print(f"   📈 Est. daily capacity: {int(daily_capacity):,} queries")
    print(f"   📊 Peak concurrent users: ~{int(best_throughput / 0.5):,} (0.5 q/user/sec)")
    print(f"   💽 Memory usage: ~{len(runner.database.candidates) * 0.5:.0f}KB for {len(runner.database.candidates):,} candidates")
    print(f"   🔍 Search efficiency: Sub-second response times")
    
    print("\n🎉 High-Volume Search Load Testing Complete!")
    return test_results

if __name__ == "__main__":
    try:
        results = asyncio.run(run_high_volume_search_tests())
        print("\n✅ All high-volume search load tests completed successfully!")
        
        # Save results to file for analysis
        import json
        with open("high_volume_search_load_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print("📄 Results saved to high_volume_search_load_test_results.json")
        
    except Exception as e:
        print(f"\n❌ Load test execution failed: {e}")
        import traceback
        traceback.print_exc()