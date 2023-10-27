'''多页面截图'''
import json
import sys
import asyncio
import base64
import aiohttp

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def get_sign(session, url, name):
    api = f'http://127.0.0.1:8080/render.png'
    data = {
        "url": url,
        #"render_all": 1,
        "images": 1,
        "cache": 1,
        "wait": 1 # 页面加载完成后继续等待1秒
    }
    async with session.post(api, data=json.dumps(data)) as resp:
        data = await resp.json()
        if data.get('image'):
            image_bytes = base64.b64decode(data["image"])
            with open(name, 'wb') as f:
                f.write(image_bytes)
            print(url, name, len(image_bytes))
        return data


async def main():
    urls = [
        "https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=1&tn=44004473_102_oem_dg&wd=%E5%9B%BE%E7%89%87&rn=50",
        "https://www.toutiao.com/article/7145668657396564518/",
        "https://new.qq.com/rain/a/NEW2022092100053400",
        "https://new.qq.com/rain/a/DSG2022092100053300"
    ]
    headers = {
        "Content-Type": "application/json",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
    }
    loop = asyncio.get_event_loop()
    t = loop.time()
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [asyncio.create_task(get_sign(session, url, f"{n}.png")) for n,url in enumerate(urls)]
        await asyncio.gather(*tasks)
    print(loop.time()-t)

        

if __name__ == "__main__":
    
    asyncio.run(main())