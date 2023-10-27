from pydantic import BaseModel
from typing import List


class HtmlPostData(BaseModel):
    url: str
    timeout: float = 30
    # 全部事件见 https://cloudlayer.io/blog/puppeteer-waituntil-options/
    wait_util: str = "domcontentloaded"
    wait: float = 0   # 页面加载完成后等待的时间
    js_name: str = "" # 预加载的js代码文件名
    filters: List[str] = [] # 过滤请求, 支持正则
    images: bool = 0  # 是否加载图片, 默认不加载
    # 禁止加载的类型 例如image、script、xhr
    # 所有的类型见: https://github.com/puppeteer/puppeteer/blob/v0.12.0/docs/api.md#requestresourcetype
    # 怎么定义某个请求的类型：https://stackoverflow.com/questions/47083776/how-is-defined-resourcetype-value-provided-by-the-devtool-protocol
    forbidden_content_types: List[str] = ["image", "media"]
    cache: bool = 1 # 是否启用缓存
    cookie: bool = 0 # 返回结果是否包含cookie
    text: bool = 1 # 返回结果是否包含html

class AjaxPostData(HtmlPostData):
    xhr: str = ""# 获取的接口正则
    text: bool = 0 # 默认不包含html
    
class PngPostData(HtmlPostData):
    # 是否截全图 1 or 0
    render_all: int = 0
    text: bool = 0
    images: bool = 1
    forbidden_content_types: List[str] = []
    wait_util: str = "networkidle2"

class JpegPostData(PngPostData):
    # 图片质量 0-100
    quality: int = 75

class ExecJsPostData(BaseModel):
    # 执行js的网站
    url: str 
    js: str = ""
    js_name: str = ""

class PostJsSourceData(BaseModel):
    js: str
    js_name: str

class RpcPostData(HtmlPostData):
    replace_source_type: str = ""
    replace_url_patten: str = ""
    replace_response: str = ""
    replace_response_patten: str = ""


if __name__ == "__main__":
    p = HtmlPostData(url=1)
    print(p)