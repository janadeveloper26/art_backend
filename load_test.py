import asyncio
import httpx
import time

URL = "http://127.0.0.1:8000/api/v1/docs"

async def fetch(client, url):
    start_time = time.time()
    try:
        response = await client.get(url, timeout=10.0)
        return response.status_code, time.time() - start_time
    except Exception as e:
        return 0, time.time() - start_time

async def load_test(num_requests, url):
    # Using a connection pool with larger limits for high concurrency
    limits = httpx.Limits(max_connections=2000, max_keepalive_connections=2000)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [fetch(client, url) for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
    successes = sum(1 for r in results if r[0] == 200)
    failures = num_requests - successes
    total_time = sum(r[1] for r in results)
    avg_time = total_time / num_requests if num_requests else 0
    max_time = max(r[1] for r in results) if results else 0
    min_time = min(r[1] for r in results) if results else 0
    
    return successes, failures, avg_time, min_time, max_time

async def main():
    levels = [100, 500, 1000, 2000]
    
    print("| Requests | Success | Failures | Avg Time (s) | Min Time (s) | Max Time (s) |")
    print("|----------|---------|----------|--------------|--------------|--------------|")
    
    for level in levels:
        start_overall = time.time()
        successes, failures, avg_time, min_time, max_time = await load_test(level, URL)
        overall_time = time.time() - start_overall
        print(f"| {level:<8} | {successes:<7} | {failures:<8} | {avg_time:<12.4f} | {min_time:<12.4f} | {max_time:<12.4f} |")
        
        # Give a short rest before the next level
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
