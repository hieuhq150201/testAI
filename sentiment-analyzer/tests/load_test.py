"""
Load test — 600 concurrent users
Dùng: python3 tests/load_test.py
Hoặc: locust -f tests/load_test.py --headless -u 600 -r 50 --run-time 60s --host http://localhost:8000
"""
import asyncio, httpx, random, time, statistics
from datetime import datetime

# ── 600 user profiles ──────────────────────────────────────────────
POSITIVE_REVIEWS = [
    "Phim hay lắm, diễn xuất tuyệt vời!",
    "Sản phẩm chất lượng tốt, giao nhanh!",
    "Quán ngon, giá hợp lý, sẽ quay lại!",
    "Bài hát hay quá, nghe mãi không chán!",
    "This movie was absolutely amazing, loved it!",
    "Great product, fast shipping, highly recommend!",
    "The acting was superb and the story was engaging!",
    "Best purchase I've made this year!",
    "Ứng dụng dễ dùng, giao diện đẹp!",
    "Khách sạn sạch, nhân viên thân thiện!",
]
NEGATIVE_REVIEWS = [
    "Phim chán, cốt truyện dở, không hay!",
    "Hàng kém chất lượng, không như quảng cáo!",
    "Quán ăn tệ, phục vụ chậm, đồ ăn nguội!",
    "Nhạc này dở quá, không nghe được!",
    "Terrible movie, complete waste of time!",
    "Poor quality product, very disappointed!",
    "Worst service I've ever experienced!",
    "Total waste of money, do not buy!",
    "App bị lỗi liên tục, rất khó chịu!",
    "Khách sạn bẩn, không đúng như ảnh!",
]
BATCH_INPUTS = POSITIVE_REVIEWS[:5] + NEGATIVE_REVIEWS[:5]

ENDPOINTS = [
    ("POST", "/predict",       lambda: {"text": random.choice(POSITIVE_REVIEWS + NEGATIVE_REVIEWS)}),
    ("POST", "/predict",       lambda: {"text": random.choice(POSITIVE_REVIEWS + NEGATIVE_REVIEWS)}),
    ("POST", "/predict",       lambda: {"text": random.choice(POSITIVE_REVIEWS + NEGATIVE_REVIEWS)}),
    ("GET",  "/health",        lambda: None),
    ("POST", "/predict/batch", lambda: {"texts": random.sample(BATCH_INPUTS, random.randint(2,6))}),
    ("GET",  "/stats",         lambda: None),
]

async def single_user(client: httpx.AsyncClient, user_id: int, results: list, duration: int = 30):
    """1 user thực hiện requests liên tục trong `duration` giây"""
    end_time = time.monotonic() + duration
    user_results = {"user_id": user_id, "requests": 0, "errors": 0, "latencies": []}

    while time.monotonic() < end_time:
        method, path, body_fn = random.choice(ENDPOINTS)
        body = body_fn()
        start = time.monotonic()
        try:
            if method == "GET":
                r = await client.get(path, timeout=5.0)
            else:
                r = await client.post(path, json=body, timeout=5.0)
            latency = (time.monotonic() - start) * 1000
            user_results["requests"] += 1
            user_results["latencies"].append(latency)
            if r.status_code >= 400:
                user_results["errors"] += 1
        except Exception:
            user_results["errors"] += 1

        # Think time: 0.05–0.3s (realistic user)
        await asyncio.sleep(random.uniform(0.05, 0.3))

    results.append(user_results)

async def run_load_test(num_users: int = 600, duration: int = 30, ramp_up: int = 10):
    print(f"🚀 Load Test: {num_users} users | {duration}s | ramp-up {ramp_up}s")
    print(f"   Target: http://localhost:8000")
    print(f"   Started: {datetime.now().strftime('%H:%M:%S')}\n")

    results = []
    limits  = httpx.Limits(max_connections=700, max_keepalive_connections=200)

    async with httpx.AsyncClient(base_url="http://localhost:8000", limits=limits) as client:
        # Health check trước
        try:
            r = await client.get("/health")
            print(f"✅ Server online — {r.json().get('version','?')}\n")
        except Exception as e:
            print(f"❌ Server offline: {e}")
            print("   Chạy server trước: uvicorn api.main:app --port 8000 --workers 4")
            return

        # Ramp-up: spawn dần 600 users
        batch_size = num_users // ramp_up
        tasks = []
        for wave in range(ramp_up):
            for i in range(batch_size):
                uid = wave * batch_size + i
                tasks.append(asyncio.create_task(single_user(client, uid, results, duration)))
            await asyncio.sleep(1)
            print(f"  ↑ Wave {wave+1}/{ramp_up} — {(wave+1)*batch_size} users spawned", end="\r")

        print(f"\n  ✅ All {num_users} users active\n")
        await asyncio.gather(*tasks)

    # ── REPORT ──────────────────────────────────────────────────────
    total_req     = sum(r["requests"] for r in results)
    total_errors  = sum(r["errors"]   for r in results)
    all_latencies = [l for r in results for l in r["latencies"]]

    print("=" * 55)
    print("📊 LOAD TEST REPORT")
    print("=" * 55)
    print(f"  Users:          {num_users}")
    print(f"  Duration:       {duration}s")
    print(f"  Total requests: {total_req:,}")
    print(f"  Errors:         {total_errors} ({total_errors/max(total_req,1)*100:.1f}%)")
    print(f"  RPS:            {total_req/duration:.1f} req/s")
    print()
    if all_latencies:
        all_latencies.sort()
        n = len(all_latencies)
        print(f"  Latency (ms):")
        print(f"    avg:  {statistics.mean(all_latencies):.1f}")
        print(f"    p50:  {all_latencies[int(n*0.50)]:.1f}")
        print(f"    p90:  {all_latencies[int(n*0.90)]:.1f}")
        print(f"    p95:  {all_latencies[int(n*0.95)]:.1f}")
        print(f"    p99:  {all_latencies[int(n*0.99)]:.1f}")
        print(f"    max:  {all_latencies[-1]:.1f}")
    print()
    ok = total_errors/max(total_req,1) < 0.01 and (statistics.mean(all_latencies) if all_latencies else 999) < 200
    print(f"  Status: {'✅ PASS' if ok else '❌ FAIL'} (target: <1% error, <200ms avg)")
    print("=" * 55)

if __name__ == "__main__":
    asyncio.run(run_load_test(num_users=600, duration=30, ramp_up=10))
