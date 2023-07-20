import json
from typing import Any
from java import (
    jclass, dynamic_proxy
)
import logging
from threading import Event, Semaphore


from webview.util import DEFAULT_HTML, js_bridge_call, parse_api_js
from webview.window import Window


logger = logging.getLogger('pywebview')

renderer = "pyanwe"

ValueCallbackInterface = jclass("android.webkit.ValueCallback")
RunnableInterface = jclass("java.lang.Runnable")
JavascriptInterface = jclass("android.webkit.JavascriptInterface")

class ValueCallback(dynamic_proxy(ValueCallbackInterface)):
    
    def __init__(self, cb):
        super().__init__()
        self.cb = cb

    def onReceiveValue(self, val, *arg):
        self.cb(val)


class Runnable(dynamic_proxy(RunnableInterface)):

    def __init__(self, cb):
            super().__init__()
            self.cb = cb
    
    def run(self):
        self.cb()



class WebkitWebView:

    def loadUrl(self, url: str):
        pass

    def loadDataWithBaseURL(
            self,
            base_url: str, data: str, 
            mime_type: str, encoding: str,
            history_url: str
        ):
        pass

    def evaluateJavascript(self, script, cb):
        pass


class BrowserPresenter:

    def setupWebView() -> WebkitWebView:
        pass

    def toggleFullscreen():
        pass

    def toast(message: str):
        pass

    def getActivity() -> Any:
        pass

mainPresenter: BrowserPresenter = None  # Init from java


class PythonJSBridge:

    def __init__(self, window):
        self.window = window

    def call(self, func_name, param, value_id):
        if param == 'undefined':
            param = None
        return js_bridge_call(self.window, func_name, param, value_id)

    

class BrowserView:
    instances = {}

    app_menu_list = None

    def __init__(self, window: Window):
        super().__init__()
        self.uid = window.uid
        self.pywebview_window = window
        self.real_url = None
        self.title = window.title


        self.closed = window.events.closed
        self.closing = window.events.closing
        self.shown = window.events.shown
        self.loaded = window.events.loaded
        self.url = window.real_url
        self.text_select = window.text_select
        self.on_top = window.on_top
        self.scale_factor = 1

        self.is_fullscreen = False
        if window.fullscreen:
            self.toggle_fullscreen()


        if BrowserView.app_menu_list:
            self.set_window_menu(BrowserView.app_menu_list)


        self.localization = window.localization

        self.browser: WebkitWebView = mainPresenter.setupWebView()
        self.browser.getWebViewClient().setBrowserView(self)
        JSBridgeClass = jclass("com.utils.JSBridge")
        self.browser.addJavascriptInterface(
            JSBridgeClass(PythonJSBridge(window)), "jsBridge"
        )

        if window.real_url:
            self.url = window.real_url
            self.load_url(window.real_url)
        elif window.html:
            self.load_html(window.html, '')
        else:
            self.load_html(DEFAULT_HTML, '')
        if window.fullscreen or window.maximized:
            self.toggle_fullscreen()
        self.shown.set()

    def on_load_finished(self):
        self._set_js_api()

    def evaluate_js(self, script):
        def eval():
            def _eval():
                _handler = ValueCallback(handler)
                self.browser.evaluateJavascript(script, _handler)
            mainPresenter.getActivity().runOnUiThread(Runnable(_eval))

        def handler(result):
            JSResult.result = None if result is None else json.loads(result)
            JSResult.result_semaphore.release()

        class JSResult:
            result = None
            result_semaphore = Semaphore(0)

        self.loaded.wait()
        eval()

        JSResult.result_semaphore.acquire()
        return JSResult.result

    def get_cookies(self):
        pass

    def load_html(self, content, base_uri):
        def _load_html():
            self.loaded.clear()
            self.browser.loadDataWithBaseURL(base_uri, content, None, None, None)
        mainPresenter.getActivity().runOnUiThread(Runnable(_load_html))

    def load_url(self, url: str):
        def _load_url():
            self.loaded.clear()
            self.browser.loadUrl(url)
        mainPresenter.getActivity().runOnUiThread(Runnable(_load_url))

    def hide(self):
        pass

    def first_show(self):
        self.load_url(self.pywebview_window.real_url)

    def show(self):
        pass

    def set_window_menu(self, menu_list):
        pass

    def toggle_fullscreen(self):
        mainPresenter.toggleFullscreen()

    def resize(self, width, height, fix_point):
        pass

    def move(self, x, y):
        pass

    def minimize(self):
        pass

    def restore(self):
        pass

    def _set_js_api(self):
        script = parse_api_js(self.pywebview_window, renderer, self.pywebview_window.uid)
        self.browser.evaluateJavascript(script, None)
        self.loaded.set()

    @staticmethod
    def alert(message):
        mainPresenter.toast(message)



_main_window_created = Event()
_main_window_created.clear()

_already_set_up_app = False


def setup_app():
    global _already_set_up_app
    if _already_set_up_app:
        return

    _already_set_up_app = True


def create_window(window):
    browser = BrowserView(window)
    BrowserView.instances[window.uid] = browser
    browser.first_show()
    print("End create window")


def set_title(title, uid):
    pass


def create_confirmation_dialog(title, message, _):
    pass


def create_file_dialog(dialog_type, directory, allow_multiple, save_filename, file_types, uid):
    window = BrowserView.instances[uid]
    return None


def get_cookies(uid):
    window = BrowserView.instances[uid]
    return window.get_cookies()



def get_current_url(uid):
    window = BrowserView.instances[uid]
    window.loaded.wait()
    return window.browser.url



def load_url(url, uid):
    window = BrowserView.instances[uid]
    window.loaded.clear()
    window.load_url(url)


def load_html(content, base_uri, uid):
    BrowserView.instances[uid].load_html(content, base_uri)


def set_app_menu(app_menu_list):
    """
    Create a custom menu for the app bar menu (on supported platforms).
    Otherwise, this menu is used across individual windows.

    Args:
        app_menu_list ([webview.menu.Menu])
    """
    BrowserView.app_menu_list = app_menu_list


def get_active_window():
    return BrowserView.instances.values()[0].pywebview_window

def show(uid):
    pass


def hide(uid):
    pass


def toggle_fullscreen(uid):
    window = BrowserView.instances[uid]
    window.toggle_fullscreen()


def set_on_top(uid, on_top):
    pass


def resize(width, height, uid, fix_point):
    pass


def move(x, y, uid):
    pass


def minimize(uid):
    pass


def restore(uid):
    pass


def destroy_window(uid):
    pass


def evaluate_js(script, uid, result_id=None):
    return BrowserView.instances[uid].evaluate_js(script)


def get_position(uid):
    pass


def get_size(uid):
    pass


def get_screens():
    pass


def add_tls_cert(certfile):
    raise NotImplementedError
