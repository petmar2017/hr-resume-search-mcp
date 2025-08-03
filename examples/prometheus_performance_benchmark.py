#!/usr/bin/env python3
"""
Prometheus-Integrated Performance Benchmarking
Real-time performance monitoring and benchmarking for HR Resume Search API
"""

import asyncio
import httpx
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Prometheus client for metrics export
try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    print("Install prometheus_client for metrics export: pip install prometheus_client")
    PROMETHEUS_AVAILABLE = False


@dataclass
class PerformanceMetric:
    """Container for performance metrics"""
    endpoint: str
    method: str
    response_time_ms: float
    status_code: int
    payload_size: int
    timestamp: datetime
    error: Optional[str] = None
    cache_hit: bool = False


@dataclass 
class BenchmarkResult:
    """Benchmark test results"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    requests_per_second: float
    error_rate: float
    cache_hit_rate: float
    start_time: datetime
    end_time: datetime
    duration_seconds: float = field(init=False)
    
    def __post_init__(self):
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()


class PrometheusMetricsCollector:
    """Collect and export metrics to Prometheus"""
    
    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url
        self.registry = CollectorRegistry()
        
        if PROMETHEUS_AVAILABLE:
            # Define Prometheus metrics
            self.request_counter = Counter(
                'benchmark_requests_total',
                'Total number of benchmark requests',
                ['endpoint', 'method', 'status'],
                registry=self.registry
            )
            
            self.response_time_histogram = Histogram(
                'benchmark_response_duration_seconds',
                'Response time distribution',
                ['endpoint', 'method'],
                buckets=(0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0),
                registry=self.registry
            )
            
            self.error_counter = Counter(
                'benchmark_errors_total',
                'Total number of errors',
                ['endpoint', 'error_type'],
                registry=self.registry
            )
            
            self.cache_hit_counter = Counter(
                'benchmark_cache_hits_total',
                'Total cache hits',
                ['endpoint'],
                registry=self.registry
            )
            
            self.active_connections_gauge = Gauge(
                'benchmark_active_connections',
                'Currently active connections',
                registry=self.registry
            )
    
    def record_request(self, metric: PerformanceMetric):
        """Record a request metric"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        # Update counters
        self.request_counter.labels(
            endpoint=metric.endpoint,
            method=metric.method,
            status=str(metric.status_code)
        ).inc()
        
        # Record response time
        self.response_time_histogram.labels(
            endpoint=metric.endpoint,
            method=metric.method
        ).observe(metric.response_time_ms / 1000)  # Convert to seconds
        
        # Record cache hits
        if metric.cache_hit:
            self.cache_hit_counter.labels(endpoint=metric.endpoint).inc()
        
        # Record errors
        if metric.error:
            self.error_counter.labels(
                endpoint=metric.endpoint,
                error_type=type(metric.error).__name__
            ).inc()
    
    async def query_prometheus(self, query: str) -> Optional[float]:
        """Query Prometheus for metrics"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={"query": query}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data["data"]["result"]:
                        return float(data["data"]["result"][0]["value"][1])
            except Exception as e:
                print(f"Prometheus query failed: {e}")
        return None
    
    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format"""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(self.registry)
        return b""


class PerformanceBenchmark:
    """Comprehensive performance benchmarking suite"""
    
    def __init__(
        self,
        api_base_url: str = "http://localhost:8000",
        prometheus_url: str = "http://localhost:9090"
    ):
        self.api_base_url = api_base_url
        self.metrics_collector = PrometheusMetricsCollector(prometheus_url)
        self.metrics: List[PerformanceMetric] = []
        self.auth_token: Optional[str] = None
    
    async def authenticate(self, email: str = "test@example.com", password: str = "testpass123"):
        """Authenticate and get JWT token"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/auth/login",
                    json={"email": email, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    print(f"✅ Authentication successful")
                    return True
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
        return False
    
    async def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> PerformanceMetric:
        """Make a single request and measure performance"""
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        start_time = time.time()
        metric = PerformanceMetric(
            endpoint=endpoint,
            method=method,
            response_time_ms=0,
            status_code=0,
            payload_size=0,
            timestamp=datetime.now()
        )
        
        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(
                        f"{self.api_base_url}{endpoint}",
                        headers=headers,
                        params=params
                    )
                elif method == "POST":
                    response = await client.post(
                        f"{self.api_base_url}{endpoint}",
                        headers=headers,
                        json=data
                    )
                
                metric.response_time_ms = (time.time() - start_time) * 1000
                metric.status_code = response.status_code
                metric.payload_size = len(response.content)
                
                # Check for cache hit header
                if response.headers.get("X-Cache-Hit") == "true":
                    metric.cache_hit = True
                
            except Exception as e:
                metric.error = str(e)
                metric.response_time_ms = (time.time() - start_time) * 1000
        
        # Record to Prometheus
        self.metrics_collector.record_request(metric)
        self.metrics.append(metric)
        
        return metric
    
    async def benchmark_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        concurrent_users: int = 10,
        requests_per_user: int = 10
    ) -> BenchmarkResult:
        """Benchmark a specific endpoint"""
        
        print(f"\n📊 Benchmarking {method} {endpoint}")
        print(f"   Users: {concurrent_users}, Requests/user: {requests_per_user}")
        
        start_time = datetime.now()
        tasks = []
        
        # Create concurrent user tasks
        for user in range(concurrent_users):
            for req in range(requests_per_user):
                tasks.append(self.make_request(endpoint, method, data))
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.now()
        
        # Analyze results
        successful_metrics = [r for r in results if isinstance(r, PerformanceMetric) and not r.error]
        failed_metrics = [r for r in results if isinstance(r, PerformanceMetric) and r.error]
        
        response_times = [m.response_time_ms for m in successful_metrics]
        cache_hits = sum(1 for m in successful_metrics if m.cache_hit)
        
        if response_times:
            result = BenchmarkResult(
                test_name=f"{method} {endpoint}",
                total_requests=len(tasks),
                successful_requests=len(successful_metrics),
                failed_requests=len(failed_metrics),
                avg_response_time_ms=statistics.mean(response_times),
                p50_response_time_ms=np.percentile(response_times, 50),
                p95_response_time_ms=np.percentile(response_times, 95),
                p99_response_time_ms=np.percentile(response_times, 99),
                min_response_time_ms=min(response_times),
                max_response_time_ms=max(response_times),
                requests_per_second=len(successful_metrics) / (end_time - start_time).total_seconds(),
                error_rate=len(failed_metrics) / len(tasks) * 100,
                cache_hit_rate=cache_hits / len(successful_metrics) * 100 if successful_metrics else 0,
                start_time=start_time,
                end_time=end_time
            )
        else:
            # All requests failed
            result = BenchmarkResult(
                test_name=f"{method} {endpoint}",
                total_requests=len(tasks),
                successful_requests=0,
                failed_requests=len(tasks),
                avg_response_time_ms=0,
                p50_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                requests_per_second=0,
                error_rate=100,
                cache_hit_rate=0,
                start_time=start_time,
                end_time=end_time
            )
        
        return result
    
    async def run_comprehensive_benchmark(self) -> List[BenchmarkResult]:
        """Run comprehensive benchmark suite"""
        
        print("\n" + "="*80)
        print("🚀 COMPREHENSIVE PERFORMANCE BENCHMARK")
        print("="*80)
        
        results = []
        
        # Test scenarios
        test_scenarios = [
            # (endpoint, method, data, concurrent_users, requests_per_user)
            ("/health", "GET", None, 10, 10),
            ("/api/v1/search/candidates", "POST", {
                "query": "Python developer",
                "search_type": "skills_match",
                "limit": 10
            }, 5, 20),
            ("/api/v1/search/similar", "POST", {
                "candidate_id": "test-id",
                "limit": 5
            }, 5, 10),
            ("/api/v1/resumes", "GET", None, 10, 5),
        ]
        
        # Authenticate first
        if not await self.authenticate():
            print("❌ Authentication failed, running limited tests")
            test_scenarios = [("/health", "GET", None, 10, 10)]
        
        # Run benchmarks
        for endpoint, method, data, users, requests in test_scenarios:
            result = await self.benchmark_endpoint(
                endpoint, method, data, users, requests
            )
            results.append(result)
            
            # Display result
            self.display_result(result)
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Generate summary report
        self.generate_summary_report(results)
        
        return results
    
    def display_result(self, result: BenchmarkResult):
        """Display benchmark result"""
        print(f"\n✅ {result.test_name}")
        print(f"   Requests: {result.successful_requests}/{result.total_requests} successful")
        print(f"   Response Time (ms):")
        print(f"      Avg: {result.avg_response_time_ms:.2f}")
        print(f"      P50: {result.p50_response_time_ms:.2f}")
        print(f"      P95: {result.p95_response_time_ms:.2f}")
        print(f"      P99: {result.p99_response_time_ms:.2f}")
        print(f"   Throughput: {result.requests_per_second:.2f} req/s")
        print(f"   Error Rate: {result.error_rate:.2f}%")
        print(f"   Cache Hit Rate: {result.cache_hit_rate:.2f}%")
    
    def generate_summary_report(self, results: List[BenchmarkResult]):
        """Generate summary performance report"""
        print("\n" + "="*80)
        print("📊 PERFORMANCE SUMMARY REPORT")
        print("="*80)
        
        # Overall statistics
        total_requests = sum(r.total_requests for r in results)
        total_successful = sum(r.successful_requests for r in results)
        avg_response_times = [r.avg_response_time_ms for r in results if r.successful_requests > 0]
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Requests: {total_requests}")
        print(f"   Successful: {total_successful} ({total_successful/total_requests*100:.1f}%)")
        print(f"   Average Response Time: {statistics.mean(avg_response_times):.2f}ms")
        
        # Performance against targets
        print(f"\n🎯 Performance vs Targets:")
        targets = [
            ("API Response (P95)", 200, max(r.p95_response_time_ms for r in results)),
            ("Search Response (P95)", 150, next((r.p95_response_time_ms for r in results if "search" in r.test_name.lower()), 0)),
            ("Error Rate", 1, statistics.mean([r.error_rate for r in results])),
            ("Cache Hit Rate", 80, statistics.mean([r.cache_hit_rate for r in results if r.cache_hit_rate > 0]))
        ]
        
        for metric, target, actual in targets:
            if metric == "Error Rate":
                status = "✅" if actual <= target else "❌"
                print(f"   {metric}: {actual:.2f}% (Target: <{target}%) {status}")
            elif metric == "Cache Hit Rate":
                status = "✅" if actual >= target else "⚠️"
                print(f"   {metric}: {actual:.2f}% (Target: >{target}%) {status}")
            else:
                status = "✅" if actual <= target else "❌"
                print(f"   {metric}: {actual:.2f}ms (Target: <{target}ms) {status}")
        
        # Export Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            metrics_data = self.metrics_collector.export_metrics()
            print(f"\n📊 Prometheus Metrics: {len(metrics_data)} bytes exported")
        
        print("\n🎉 Benchmark completed successfully!")


async def main():
    """Main execution function"""
    
    # Create benchmark instance
    benchmark = PerformanceBenchmark()
    
    # Run comprehensive benchmark
    results = await benchmark.run_comprehensive_benchmark()
    
    # Query Prometheus for additional metrics
    if PROMETHEUS_AVAILABLE:
        print("\n📊 Querying Prometheus for system metrics...")
        
        queries = {
            "CPU Usage": 'rate(process_cpu_seconds_total[1m])',
            "Memory Usage": 'process_resident_memory_bytes',
            "DB Connections": 'db_connections_active',
            "Request Rate": 'rate(http_requests_total[5m])'
        }
        
        for name, query in queries.items():
            value = await benchmark.metrics_collector.query_prometheus(query)
            if value is not None:
                print(f"   {name}: {value:.2f}")


if __name__ == "__main__":
    print("🎯 HR Resume Search - Performance Benchmark with Prometheus")
    print("="*60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("This benchmark requires Python 3.8 or higher")
        sys.exit(1)
    
    # Run benchmark
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Benchmark interrupted by user")
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")