import asyncio
from aiohttp import web
from api.render_view import RenderHtmlView, RenderPngView, RenderJpegView, RenderJsonView
from browser.launch import LaunchChrome


c = LaunchChrome()

app = web.Application()
app.router.add_view('/render.html', RenderHtmlView)
app.router.add_view('/render.png', RenderPngView)
app.router.add_view('/render.jpeg', RenderJpegView)
app.router.add_view('/render.json', RenderJsonView)
app.on_startup.append(c.on_startup_tasks)
app.on_cleanup.append(c.on_cleanup_tasks)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    web.run_app(app, loop=loop)