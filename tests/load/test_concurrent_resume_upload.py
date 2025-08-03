#!/usr/bin/env python3
"""
Concurrent Resume Upload Load Tests
Tests system performance under concurrent file upload and processing load
"""
import asyncio
import time
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import random

class MockServices:
    """Mock services for load testing"""
    
    def __init__(self):
        self.processing_times = []
        self.error_count = 0
        self.success_count = 0
    
    async def process_file_upload(self, file_id: str, file_size: int, processing_delay: float = 0.1) -> Dict[str, Any]:
        """Mock file processing with configurable delay"""
        start_time = time.time()
        
        try:
            # Simulate file validation
            await asyncio.sleep(0.01)
            
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                self.error_count += 1
                return {"success": False, "error": "File too large", "file_id": file_id}
            
            # Simulate file processing (varies by file size)
            processing_time = processing_delay + (file_size / (1024 * 1024)) * 0.05
            await asyncio.sleep(processing_time)
            
            # Random processing failures (5% failure rate)
            if random.random() < 0.05:
                self.error_count += 1
                return {"success": False, "error": "Processing failed", "file_id": file_id}
            
            self.success_count += 1
            total_time = time.time() - start_time
            self.processing_times.append(total_time)
            
            return {
                "success": True,
                "file_id": file_id,
                "file_size": file_size,
                "processing_time": total_time,
                "extracted_text": f"Mock extracted text for file {file_id}",
                "keywords": ["Python", "Developer", "Experience"]
            }
            
        except Exception as e:
            self.error_count += 1
            return {"success": False, "error": str(e), "file_id": file_id}

class LoadTestRunner:
    """Load test runner for concurrent operations"""
    
    def __init__(self):
        self.services = MockServices()
    
    async def single_file_upload_test(self, file_count: int, max_concurrent: int = 10) -> Dict[str, Any]:
        """Test concurrent file uploads with specified concurrency"""
        print(f"🔄 Testing {file_count} concurrent file uploads (max concurrent: {max_concurrent})")
        
        # Generate test files with varying sizes
        test_files = []
        for i in range(file_count):
            file_size = random.randint(100_000, 5_000_000)  # 100KB to 5MB
            test_files.append({
                "file_id": f"test_file_{i:04d}",
                "file_size": file_size,
                "processing_delay": random.uniform(0.05, 0.2)  # Variable processing time
            })
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def upload_with_semaphore(file_data):
            async with semaphore:
                return await self.services.process_file_upload(
                    file_data["file_id"],
                    file_data["file_size"],
                    file_data["processing_delay"]
                )
        
        # Execute all uploads
        start_time = time.time()
        tasks = [upload_with_semaphore(file_data) for file_data in test_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        processing_times = [r["processing_time"] for r in successful_results]
        
        return {
            "total_files": file_count,
            "successful_uploads": len(successful_results),
            "failed_uploads": len(failed_results),
            "exceptions": len(exceptions),
            "total_time": total_time,
            "average_time_per_file": total_time / file_count,
            "throughput_files_per_second": file_count / total_time,
            "processing_time_stats": {
                "min": min(processing_times) if processing_times else 0,
                "max": max(processing_times) if processing_times else 0,
                "mean": statistics.mean(processing_times) if processing_times else 0,
                "median": statistics.median(processing_times) if processing_times else 0,
                "std_dev": statistics.stdev(processing_times) if len(processing_times) > 1 else 0
            },
            "success_rate": len(successful_results) / file_count * 100,
            "max_concurrent": max_concurrent
        }
    
    async def burst_load_test(self, burst_size: int, burst_count: int, burst_interval: float = 1.0) -> Dict[str, Any]:
        """Test system under burst load conditions"""
        print(f"💥 Testing burst load: {burst_count} bursts of {burst_size} files each")
        
        burst_results = []
        overall_start = time.time()
        
        for burst_num in range(burst_count):
            print(f"   Burst {burst_num + 1}/{burst_count}")
            
            # Generate burst files
            burst_files = []
            for i in range(burst_size):
                file_id = f"burst_{burst_num}_{i:03d}"
                file_size = random.randint(500_000, 2_000_000)  # 500KB to 2MB
                burst_files.append({
                    "file_id": file_id,
                    "file_size": file_size,
                    "processing_delay": 0.1
                })
            
            # Execute burst
            burst_start = time.time()
            tasks = [
                self.services.process_file_upload(f["file_id"], f["file_size"], f["processing_delay"])
                for f in burst_files
            ]
            burst_results_batch = await asyncio.gather(*tasks, return_exceptions=True)
            burst_time = time.time() - burst_start
            
            # Track burst metrics
            successful_in_burst = sum(1 for r in burst_results_batch if isinstance(r, dict) and r.get("success"))
            burst_results.append({
                "burst_number": burst_num + 1,
                "burst_time": burst_time,
                "successful_files": successful_in_burst,
                "total_files": burst_size,
                "burst_throughput": burst_size / burst_time
            })
            
            # Wait between bursts (except for the last one)
            if burst_num < burst_count - 1:
                await asyncio.sleep(burst_interval)
        
        overall_time = time.time() - overall_start
        total_files = burst_size * burst_count
        total_successful = sum(b["successful_files"] for b in burst_results)
        
        return {
            "burst_count": burst_count,
            "burst_size": burst_size,
            "total_files": total_files,
            "total_successful": total_successful,
            "overall_time": overall_time,
            "overall_throughput": total_files / overall_time,
            "success_rate": total_successful / total_files * 100,
            "burst_results": burst_results,
            "average_burst_time": statistics.mean([b["burst_time"] for b in burst_results]),
            "average_burst_throughput": statistics.mean([b["burst_throughput"] for b in burst_results])
        }
    
    async def sustained_load_test(self, files_per_second: int, duration_seconds: int) -> Dict[str, Any]:
        """Test sustained load over time"""
        print(f"⏱️  Testing sustained load: {files_per_second} files/sec for {duration_seconds} seconds")
        
        interval = 1.0 / files_per_second
        start_time = time.time()
        file_counter = 0
        results = []
        
        async def upload_file():
            nonlocal file_counter
            file_id = f"sustained_{file_counter:05d}"
            file_size = random.randint(200_000, 1_000_000)  # 200KB to 1MB
            file_counter += 1
            
            result = await self.services.process_file_upload(file_id, file_size, 0.08)
            results.append(result)
        
        # Schedule uploads at regular intervals
        tasks = []
        next_upload_time = start_time
        
        while time.time() - start_time < duration_seconds:
            current_time = time.time()
            
            if current_time >= next_upload_time:
                # Schedule upload
                task = asyncio.create_task(upload_file())
                tasks.append(task)
                next_upload_time += interval
            
            # Small sleep to prevent busy waiting
            await asyncio.sleep(0.001)
        
        # Wait for all uploads to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        
        return {
            "target_files_per_second": files_per_second,
            "duration_seconds": duration_seconds,
            "total_files_uploaded": len(results),
            "successful_uploads": len(successful_results),
            "actual_files_per_second": len(results) / total_time,
            "success_rate": len(successful_results) / len(results) * 100 if results else 0,
            "total_time": total_time
        }
    
    async def stress_test(self, max_files: int, concurrency_levels: List[int]) -> Dict[str, Any]:
        """Test system stress at different concurrency levels"""
        print(f"🔥 Stress testing with {max_files} files at various concurrency levels")
        
        stress_results = []
        
        for concurrency in concurrency_levels:
            print(f"   Testing concurrency level: {concurrency}")
            
            # Reset services for each test
            self.services = MockServices()
            
            result = await self.single_file_upload_test(max_files, concurrency)
            result["concurrency_level"] = concurrency
            stress_results.append(result)
            
            # Brief pause between stress levels
            await asyncio.sleep(0.5)
        
        return {
            "max_files": max_files,
            "concurrency_levels": concurrency_levels,
            "stress_results": stress_results,
            "optimal_concurrency": max(stress_results, key=lambda x: x["throughput_files_per_second"])["concurrency_level"]
        }

async def run_concurrent_upload_load_tests():
    """Run comprehensive concurrent upload load tests"""
    print("🚀 Concurrent Resume Upload Load Tests")
    print("=" * 60)
    
    runner = LoadTestRunner()
    test_results = {}
    
    # Test 1: Basic concurrent uploads
    print("\n1️⃣ Basic Concurrent Upload Test:")
    print("-" * 35)
    
    basic_result = await runner.single_file_upload_test(50, 10)
    test_results["basic_concurrent"] = basic_result
    
    print(f"   📊 Files processed: {basic_result['successful_uploads']}/{basic_result['total_files']}")
    print(f"   ⏱️  Total time: {basic_result['total_time']:.2f}s")
    print(f"   📈 Throughput: {basic_result['throughput_files_per_second']:.1f} files/sec")
    print(f"   ✅ Success rate: {basic_result['success_rate']:.1f}%")
    print(f"   📊 Avg processing: {basic_result['processing_time_stats']['mean']:.3f}s")
    
    # Test 2: Burst load test
    print("\n2️⃣ Burst Load Test:")
    print("-" * 20)
    
    burst_result = await runner.burst_load_test(20, 5, 0.5)
    test_results["burst_load"] = burst_result
    
    print(f"   💥 Bursts completed: {burst_result['burst_count']}")
    print(f"   📊 Total files: {burst_result['total_successful']}/{burst_result['total_files']}")
    print(f"   📈 Overall throughput: {burst_result['overall_throughput']:.1f} files/sec")
    print(f"   📊 Avg burst throughput: {burst_result['average_burst_throughput']:.1f} files/sec")
    print(f"   ✅ Success rate: {burst_result['success_rate']:.1f}%")
    
    # Test 3: Sustained load test
    print("\n3️⃣ Sustained Load Test:")
    print("-" * 23)
    
    sustained_result = await runner.sustained_load_test(5, 10)  # 5 files/sec for 10 seconds
    test_results["sustained_load"] = sustained_result
    
    print(f"   🎯 Target rate: {sustained_result['target_files_per_second']} files/sec")
    print(f"   📊 Actual rate: {sustained_result['actual_files_per_second']:.1f} files/sec")
    print(f"   📈 Files uploaded: {sustained_result['successful_uploads']}/{sustained_result['total_files_uploaded']}")
    print(f"   ✅ Success rate: {sustained_result['success_rate']:.1f}%")
    
    # Test 4: Stress test with varying concurrency
    print("\n4️⃣ Stress Test (Concurrency Levels):")
    print("-" * 38)
    
    stress_result = await runner.stress_test(30, [5, 10, 20, 50])
    test_results["stress_test"] = stress_result
    
    print(f"   🔥 Optimal concurrency: {stress_result['optimal_concurrency']}")
    for result in stress_result["stress_results"]:
        print(f"   📊 Concurrency {result['concurrency_level']:2d}: {result['throughput_files_per_second']:.1f} files/sec ({result['success_rate']:.1f}% success)")
    
    # Test 5: Performance summary
    print("\n5️⃣ Performance Summary:")
    print("-" * 25)
    
    print(f"   🏆 Best throughput: {max([r for k, r in test_results.items() if 'throughput_files_per_second' in r], key=lambda x: x['throughput_files_per_second'])['throughput_files_per_second']:.1f} files/sec")
    print(f"   📊 Average success rate: {statistics.mean([r['success_rate'] for k, r in test_results.items() if 'success_rate' in r]):.1f}%")
    print(f"   ⚡ Recommended concurrency: {stress_result['optimal_concurrency']}")
    
    # Test 6: Resource usage simulation
    print("\n6️⃣ Resource Usage Analysis:")
    print("-" * 30)
    
    peak_concurrent = stress_result['optimal_concurrency']
    peak_throughput = max([r['throughput_files_per_second'] for r in stress_result['stress_results']])
    
    print(f"   💾 Peak concurrent uploads: {peak_concurrent}")
    print(f"   📈 Peak throughput: {peak_throughput:.1f} files/sec")
    print(f"   ⏱️  Est. daily capacity: {int(peak_throughput * 3600 * 24):,} files")
    print(f"   📊 Memory per upload: ~2-5MB (estimated)")
    print(f"   💽 Peak memory usage: ~{peak_concurrent * 3.5:.0f}MB")
    
    print("\n🎉 Concurrent Upload Load Testing Complete!")
    return test_results

if __name__ == "__main__":
    try:
        results = asyncio.run(run_concurrent_upload_load_tests())
        print("\n✅ All concurrent upload load tests completed successfully!")
        
        # Save results to file for analysis
        import json
        with open("concurrent_upload_load_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print("📄 Results saved to concurrent_upload_load_test_results.json")
        
    except Exception as e:
        print(f"\n❌ Load test execution failed: {e}")
        import traceback
        traceback.print_exc()