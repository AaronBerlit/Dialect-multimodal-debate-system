import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream('POST', 'http://localhost:8000/api/debate', json={'question': 'future of AI', 'dynamics': 'dialectical'}, timeout=120.0) as r:
                async for line in r.aiter_lines():
                    print(line)
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(main())
