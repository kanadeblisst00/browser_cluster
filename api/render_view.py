import traceback
import asyncio
import re
import os
import aiofiles
import aiofiles.os as aios
from typing import Optional, List, Dict
from aiohttp import web
from asyncio.exceptions import CancelledError
from aiohttp.web_response import Response
from aiohttp.web import Application
from .postdata import HtmlPostData, PngPostData, JpegPostData, AjaxPostData
from json.decoder import JSONDecodeError
from pydantic.error_wrappers import ValidationError
from pyppeteer.errors import TimeoutError as PPTimeoutError
from pyppeteer.errors import NetworkError
from pyppeteer.page import Page


class RenderView(web.View):
    PostDataClass = HtmlPostData
    async def get(self) -> Response:
        return await self.post()

    async def post(self) -> Response:
        _options = await self.get_options()
        if isinstance(_options, Response):
            return _options
        options = self.valid_options(_options)
        if isinstance(options, Response):
            return options
        return await self.get_response(options)

    async def get_response(self, options: Dict) -> Response:
        raise NotImplementedError

    async def get_options(self) -> Dict:
        options = {}
        options.update(self.request.query)
        if self.request.can_read_body:
            try:
                post_data = await self.request.json()
            except JSONDecodeError:
                err_data = {"status":400,"err":"json格式错误"}
                return web.json_response(err_data)
            else:
                options.update(post_data)
        return options
    
    def get_app_root_dir(self) -> str:
        path = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.join(path, os.path.pardir)
        return root_dir
    
    def fix_forbidden_content_types(self, images: int, forbidden_content_types: List) -> List:
        forbidden_content_types = list(forbidden_content_types)
        if images and "image" in forbidden_content_types:
            forbidden_content_types.remove("image")
        elif not images and "image" not in forbidden_content_types:
            forbidden_content_types.append("image")
        return forbidden_content_types
    
    async def intercept_request(self, page: Optional[Page], filters:List=[], forbidden_content_types: List=[]) -> None:
        '''已弃用，该方法拦截会导致302跳转的xhr请求无法正常跳转'''
        await page.setRequestInterception(True)
        async def intercept(request):
            if request.resourceType in forbidden_content_types or\
                 any([re.search(ptn, request.url) for ptn in filters]):
                await request.abort()
            else:
                await request.continue_()
        page.on('request', lambda req: asyncio.ensure_future(intercept(req)))
    
    async def setup_request_interceptor(self, page: Optional[Page], filters:List=[], forbidden_content_types: List=[]) -> None:
        client = page._networkManager._client
        async def intercept(event: dict) -> None:
            interception_id = event["interceptionId"]
            request = event["request"]
            url, resourceType = request["url"], event.get('resourceType', '').lower()
            options = {"interceptionId": interception_id}
            if resourceType in forbidden_content_types or\
                 any([i for i in filters if i in url]) or\
                 any([re.search(ptn, url) for ptn in filters]):
                options["errorReason"] = "BlockedByClient"
            try:
                await client.send("Network.continueInterceptedRequest", options)
            except NetworkError:
                pass

        client.on(
            "Network.requestIntercepted",
            lambda event: client._loop.create_task(intercept(event)),
        )
        patterns = [{"urlPattern": "*"}]
        await client.send("Network.setRequestInterception", {"patterns": patterns})
    
    async def load_js_script(self, js_name: str) -> str:
        root_dir = self.get_app_root_dir()
        if not js_name.endswith('.js'):
            js_name = js_name + '.js'
        script_path = os.path.join(root_dir, "script", js_name)
        if not await aios.path.exists(script_path):
            return ""
        async with aiofiles.open(script_path, mode='r', encoding='utf-8') as f:
            js_str = await f.read()
        return "() => {%s}"%js_str
    
    def valid_options(self, options: Dict) -> HtmlPostData:
        try:
            new_options = self.PostDataClass(**options)
        except ValidationError:
            err_data = {"status":500, "err": traceback.format_exc()}
            return web.json_response(err_data)
        return new_options


class RenderHtmlView(RenderView):
    async def get_response(self, options: HtmlPostData) -> Response:
        app = self.request.app
        try:
            result = await self.browser_get(app, options)
        except CancelledError:
            print('CancelledError')
            return
        except:
            result = {"status":500, "err": traceback.format_exc()}
        return web.json_response(result)
    
    async def _browser_get(self, page: Optional[Page], options: HtmlPostData) -> Dict:
        result = {}
        if not options.cache:
            await page.setCacheEnabled(False) 
        if options.js_name:
            js_str = await self.load_js_script(options.js_name)
            if js_str:
                await page.evaluateOnNewDocument(js_str)
        forbidden_content_types = self.fix_forbidden_content_types(options.images, options.forbidden_content_types)
        filters = options.filters
        if filters or forbidden_content_types:
            #await self.intercept_request(page, options.filters, forbidden_content_types)
            await self.setup_request_interceptor(page, options.filters, forbidden_content_types)
        # 如果请求的是render.json,但是没有给定xhr，则返回html
        if not hasattr(options, "xhr") or not options.xhr:
            options.text = 1
        ajax_result = await self._goto(page, options)
        if ajax_result:
            result.update(ajax_result)
        if options.wait:
            await page.waitFor(options.wait*1000)
        if options.text:
            text = await page.content()
            result["text"] = text
        if options.cookie:
            cookies = await page.cookies()
            result["cookies"] = cookies
        result["status"] = 200
        return result
    
    async def _goto(self, page: Optional[Page], options: AjaxPostData) -> Dict:
        try:
            await page.goto(options.url, 
                waitUntil=options.wait_util, timeout=options.timeout*1000)
        except PPTimeoutError:
            #await page.evaluate('() => window.stop()')
            await page._client.send("Page.stopLoading")
        finally:
            page.remove_all_listeners("request")
    
    async def browser_get(self, app: Application, options: HtmlPostData) -> Dict:
        pages_queue = app["pages_queue"]
        page = await pages_queue.get()
        try:
            result = await self._browser_get(page, options)
        except Exception as e:
            raise e
        else:
            return result
        finally:
            await pages_queue.put(page)

class RenderPngView(RenderHtmlView):
    PostDataClass = PngPostData
    
    async def screenshot(self, page: Optional[Page], options: PngPostData):
        kwargs = {
            "encoding": 'base64', 
            "fullPage": bool(options.render_all),
            "type": "png"
        }
        page.bringToFront()
        await asyncio.sleep(0)
        return await page.screenshot(**kwargs)
    
    async def browser_get(self, app: Application, options: PngPostData) -> Dict:
        pages_queue = app["pages_queue"]
        page = await pages_queue.get()
        try:
            result = await self._browser_get(page, options)
            async with app["screenshot_lock"]:
                result["image"] = await self.screenshot(page, options)
        except Exception as e:
            raise e
        else:
            return result
        finally:
            await pages_queue.put(page)
        

class RenderJpegView(RenderPngView):
    PostDataClass = JpegPostData
    
    async def screenshot(self, page: Optional[Page], options: JpegPostData):
        kwargs = {
            "encoding": 'base64', 
            "fullPage": bool(options.render_all),
            "type": "jpeg",
            "quality": options.quality
        }
        await asyncio.sleep(0)
        return await page.screenshot(**kwargs)


class RenderJsonView(RenderHtmlView):
    PostDataClass = AjaxPostData
    
    async def _goto(self, page: Optional[Page], options: AjaxPostData) -> Dict:
        if not options.xhr:
            results = await super()._goto(page, options)
            return results
        try:
            resp, _ = await asyncio.gather(
                page.waitForResponse(lambda res:re.search(options.xhr, res.url) 
                                                    and res.status == 200),
                page.goto(options.url, 
                             waitUntil=options.wait_util, timeout=options.timeout*1000)
            )
        except PPTimeoutError:
            #await page.evaluate('() => window.stop()')
            await page._client.send("Page.stopLoading")
        else:
            content = await resp.text()
            result = {
                "status": resp.status,
                "url": resp.url,
                "headers": resp.headers,
                "content": content
            }
            return result
        finally:
            page.remove_all_listeners("request")


if __name__ == "__main__":
    pass
