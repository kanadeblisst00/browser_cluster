import asyncio
from pyppeteer.launcher import launch
from aiohttp import web


class LaunchChrome:
    def __init__(self):
        self.browser = None
    
    async def _launch(self):
        chrome_args = ["--window-size=1280,800", "--user-data-dir=userdata"]
        executablePath = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.browser = await launch(
            headless=False,
            autoClose=False,
            executablePath=executablePath,
            args=chrome_args, 
            ignoreDefaultArgs=['--enable-automation'],
            defaultViewport={"width":1280, "height": 800}
        )

    async def launch_tab(self):
        await self.browser.newPage()
    
    async def on_startup_tasks(self, app: web.Application) -> None:
        page_count = 4
        await asyncio.create_task(self._launch())
        app["browser"] = self.browser
        tasks = [asyncio.create_task(self.launch_tab()) for _ in range(page_count-1)]
        await asyncio.gather(*tasks)
        queue = asyncio.Queue(maxsize=page_count+1)
        for i in await self.browser.pages():
            await queue.put(i)
        app["pages_queue"] = queue
        app["screenshot_lock"] = asyncio.Lock()
        
    async def on_cleanup_tasks(self, app: web.Application) -> None:
        await self.browser.close()
