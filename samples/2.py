'''拦截指定ajax请求的响应'''
import json
import sys
import asyncio
import aiohttp

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def get_sign(session, url):
    api = f'http://127.0.0.1:8080/render.json'
    data = {
        "url": url,
        "xhr": "/api/", # 拦截接口包含/api/的响应并返回
        "cache": 0,
        "filters": [".png", ".jpg"],
        "timeout": 0.5
    }
    async with session.post(api, data=json.dumps(data)) as resp:
        data = await resp.json()
        print(url, data)
        return data


async def main():
    urls = ["https://spa1.scrape.center/"]
    headers = {
        "Content-Type": "application/json",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
    }
    loop = asyncio.get_event_loop()
    t = loop.time()
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [asyncio.create_task(get_sign(session, url)) for url in urls]
        await asyncio.gather(*tasks)
    print("耗时: ", loop.time()-t)

        
if __name__ == "__main__":
    asyncio.run(main())