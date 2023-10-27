'''多个标签同时运行，总耗时为时间最长的标签页耗时'''
import sys
import asyncio
import aiohttp

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def get_sign(session, delay):
    url = f"http://www.httpbin.org/delay/{delay}"
    api = f'http://127.0.0.1:8080/render.html?url={url}'
    async with session.get(api) as resp:
        data = await resp.json()
        print(url, data.get("status"))
        return data

async def main():
    headers = {
        "Content-Type": "application/json",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
    }
    loop = asyncio.get_event_loop()
    t = loop.time()
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [asyncio.create_task(get_sign(session, i)) for i in range(1, 5)]
        await asyncio.gather(*tasks)
    print("耗时: ", loop.time()-t)

        
if __name__ == "__main__":
    asyncio.run(main())