import sys
import speech_recognition as sr
import darkdetect
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTabWidget, QWidget, QMainWindow, 
                             QAction, QToolBar, QDialog, QListWidget, QStyleFactory, QFrame, QLabel, QMessageBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtCore import QUrl, Qt, QTimer
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtNetwork import QNetworkProxy, QNetworkProxyFactory, QNetworkAccessManager, QNetworkReply
from adblockparser import AdblockRules
import requests
import google.generativeai as genai
import urllib.parse
import subprocess

class WebView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        self.page().fullScreenRequested.connect(self.handle_fullscreen_request)

    def handle_fullscreen_request(self, request):
        request.accept()
        if request.toggleOn():
            self.showFullScreen()
        else:
            self.showNormal()

class CustomProxyFactory(QNetworkProxyFactory):
    def __init__(self, proxy):
        super().__init__()
        self.proxy = proxy

    def queryProxy(self, query=None):
        return [self.proxy]

class BrowserApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize VPN settings early
        self.vpn_enabled = False
        self.proxy = QNetworkProxy()

        self.setWindowTitle('Goon Browser')  # Changed the window title here
        self.setStyleSheet("""
            QMainWindow { background-color: #FFF1E6; }
            QWidget { color: #333333; }
        """)
        self.showMaximized()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Top bar
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #FFD7BA; border-radius: 10px;")
        top_layout = QHBoxLayout(top_bar)
        
        # Window controls
        window_controls = QWidget()
        window_controls.setFixedSize(80, 30)
        window_layout = QHBoxLayout(window_controls)
        for color in ['#FF6B6B', '#FFD93D', '#6BCB77']:
            dot = QLabel()
            dot.setStyleSheet(f"background-color: {color}; border-radius: 7px;")
            dot.setFixedSize(15, 15)
            window_layout.addWidget(dot)
        top_layout.addWidget(window_controls)

        # URL bar
        self.url_input = QLineEdit()
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 14px;
            }
        """)
        self.url_input.returnPressed.connect(self.load_url)
        top_layout.addWidget(self.url_input)

        # Action buttons
        action_buttons = QWidget()
        action_buttons.setFixedWidth(300)  # Increased width to accommodate larger icons
        action_layout = QHBoxLayout(action_buttons)
        
        icon_size = 64  # Increased icon size to 64x64

        # Helper function to create buttons
        def create_button(icon_path, function):
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QtCore.QSize(icon_size, icon_size))
            btn.setStyleSheet("background-color: transparent; border: none;")
            btn.setFixedSize(icon_size + 10, icon_size + 10)
            btn.clicked.connect(function)
            return btn

        voice_search_btn = create_button('voicesearch.jpeg', self.voice_search)
        action_layout.addWidget(voice_search_btn)

        new_tab_btn = create_button('newtab.jpeg', self.add_new_tab)
        action_layout.addWidget(new_tab_btn)

        full_screen_btn = create_button('fullscreen.jpeg', self.toggle_full_screen)
        action_layout.addWidget(full_screen_btn)

        self.dark_mode_btn = create_button('darkmode.jpeg', self.toggle_dark_mode)
        action_layout.addWidget(self.dark_mode_btn)

        # VPN button
        self.vpn_btn = create_button('vpn.png', self.toggle_vpn)
        self.vpn_btn.setCheckable(True)
        action_layout.addWidget(self.vpn_btn)

        top_layout.addWidget(action_buttons)

        main_layout.addWidget(top_bar)

        # Main content area
        content_area = QWidget()
        content_area.setStyleSheet("background-color: #FFD7BA; border-radius: 10px;")
        content_layout = QHBoxLayout(content_area)

        # Left sidebar
        left_sidebar = QWidget()
        left_sidebar.setFixedWidth(150)
        left_sidebar.setStyleSheet("background-color: #FFA45B; border-radius: 10px;")
        sidebar_layout = QVBoxLayout(left_sidebar)
        sidebar_items = [
            ('pie_chart.png', 'Pie Chart'),
            ('stats.png', 'Stats'),
            ('calendar.png', 'Calendar')
        ]
        for icon, text in sidebar_items:
            item = QPushButton(text)
            item.setIcon(QIcon(icon))
            item.setStyleSheet("""
                QPushButton {
                    background-color: #FF6B6B;
                    border-radius: 5px;
                    padding: 10px;
                    text-align: left;
                    color: white;
                }
            """)
            sidebar_layout.addWidget(item)
        sidebar_layout.addStretch()
        content_layout.addWidget(left_sidebar)

        # Web view area
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 0; }
            QTabWidget::tab-bar { left: 5px; }
            QTabBar::tab { 
                background-color: #FFA45B;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                min-width: 100px;
                padding: 5px;
            }
            QTabBar::tab:selected { 
                background-color: #FF6B6B;
            }
        """)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        content_layout.addWidget(self.tab_widget)

        main_layout.addWidget(content_area)

        # Bottom bar
        bottom_bar = QWidget()
        bottom_bar.setStyleSheet("background-color: #FFD7BA; border-radius: 10px;")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_items = [
            ('home.png', self.go_home),
            ('zoomin.jpeg', self.zoom_in),
            ('zoomout.jpeg', self.zoom_out)
        ]
        for icon, function in bottom_items:
            btn = create_button(icon, function)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFA45B;
                    border-radius: 10px;
                    padding: 5px;
                }
            """)
            bottom_layout.addWidget(btn)
        main_layout.addWidget(bottom_bar)

        # Load ad-blocking rules
        self.load_adblock_rules()

        # Add initial tab
        self.add_new_tab()

        # Dark mode settings
        self.dark_mode = False
        self.youtube_fullscreen_script = """
        (function() {
            var videoElement = document.querySelector('video');
            if (videoElement) {
                videoElement.webkitRequestFullscreen();
            }
        })();
        """

        self.spotlight_search = SpotlightSearch(self)

        # Modify the web profile settings
        self.web_profile.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        self.web_profile.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
        self.web_profile.settings().setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        self.web_profile.settings().setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        self.web_profile.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        self.web_profile.settings().setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        self.web_profile.settings().setAttribute(QWebEngineSettings.AllowGeolocationOnInsecureOrigins, True)

    def current_web_view(self):
        return self.tab_widget.currentWidget()

    def add_new_tab(self, url=None):
        if url is None:
            url = QUrl("https://duckduckgo.com/")
        elif isinstance(url, str):
            url = QUrl(url)
        elif not isinstance(url, QUrl):
            url = QUrl("https://duckduckgo.com/")
        
        web_view = WebView(self)
        web_view.setPage(QWebEnginePage(self.web_profile, web_view))
        web_view.load(url)
        web_view.loadFinished.connect(self.update_url_bar)
        
        # Apply VPN settings to the new tab if enabled
        if self.vpn_enabled:
            proxy_factory = CustomProxyFactory(self.proxy)
            web_view.page().profile().setProxyFactory(proxy_factory)
        
        index = self.tab_widget.addTab(web_view, QIcon("tab_icon.png"), "New Tab")
        self.tab_widget.setCurrentIndex(index)
        
        web_view.loadFinished.connect(lambda ok, view=web_view: self.on_load_finished(ok, view))
        
        # Modify the web view settings
        settings = web_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.AllowGeolocationOnInsecureOrigins, True)
        
        return web_view

    def open_multiple_tabs(self, urls):
        for url in urls:
            self.add_new_tab(url)

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
        else:
            self.close()

    def load_url(self):
        query = self.url_input.text()
        if not query.startswith(('http://', 'https://')):
            if '.' in query and ' ' not in query:
                query = 'http://' + query
            else:
                query = f'https://duckduckgo.com/?q={urllib.parse.quote_plus(query)}'
        
        current_view = self.current_web_view()
        if current_view:
            current_view.setUrl(QUrl(query))

    def update_url_bar(self):
        current_view = self.current_web_view()
        if current_view:
            self.url_input.setText(current_view.url().toString())

    def voice_search(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                self.speak("Listening... How can I help you?")
                print("Listening... Speak now.")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                print("Processing speech...")
                
            try:
                query = recognizer.recognize_google(audio)
                print(f"You said: {query}")
                self.process_voice_command(query)
            except sr.UnknownValueError:
                self.speak("I'm sorry, I couldn't understand that. Please try again.")
                print("Could not understand audio. Please try again.")
            except sr.RequestError as e:
                self.speak("I'm having trouble connecting to the speech recognition service.")
                print(f"Could not request results from Google Speech Recognition service; {e}")
        except Exception as e:
            self.speak("An error occurred. Please try again.")
            print(f"An error occurred: {e}")

    def process_voice_command(self, query):
        query = query.lower()
        if "search for" in query:
            search_term = query.replace("search for", "").strip()
            self.speak(f"Searching for {search_term}")
            self.perform_search(search_term)
        elif "open" in query:
            website = query.replace("open", "").strip()
            self.speak(f"Opening {website}")
            self.open_website(website)
        elif "play" in query:
            video = query.replace("play", "").strip()
            self.speak(f"Playing {video} on YouTube")
            self.search_and_play_youtube(video)
        elif "what's the time" in query or "what is the time" in query:
            current_time = QtCore.QTime.currentTime().toString("hh:mm AP")
            self.speak(f"The current time is {current_time}")
        elif "close tab" in query:
            self.speak("Closing the current tab")
            self.close_current_tab()
        elif "new tab" in query:
            self.speak("Opening a new tab")
            self.add_new_tab()
        else:
            self.speak("Performing a web search for your query")
            self.perform_search(query)

    def speak(self, text):
        subprocess.run(["say", text])

    def open_website(self, website):
        if not website.startswith('http'):
            website = 'https://' + website
        self.add_new_tab(website)

    def close_current_tab(self):
        current_index = self.tab_widget.currentIndex()
        self.close_tab(current_index)

    def show_error_message(self, message):
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Warning)
        error_dialog.setText(message)
        error_dialog.setWindowTitle("Voice Search Error")
        error_dialog.exec_()

    def perform_search(self, query):
        if "youtube" in query.lower():
            self.search_and_play_youtube(query)
        elif "play" in query.lower():
            self.search_and_play_youtube(query.replace("play", "").strip())
        else:
            search_query = f'https://duckduckgo.com/?q={urllib.parse.quote_plus(query)}'
            self.url_input.setText(search_query)
            self.load_url()

    def search_and_play_youtube(self, query):
        search_query = f'https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}'
        
        current_view = self.current_web_view()
        if current_view:
            current_view.load(QUrl(search_query))
            current_view.loadFinished.connect(lambda: self.extract_and_play_youtube_video(current_view))

    def extract_and_play_youtube_video(self, web_view):
        web_view.page().runJavaScript("""
            var videos = document.querySelectorAll('a#video-title');
            if (videos.length > 0) {
                videos[0].click();
                return true;
            }
            return false;
        """, lambda result: self.handle_youtube_autoplay(result, web_view))

    def handle_youtube_autoplay(self, clicked, web_view):
        if not clicked:
            print("No videos found to autoplay.")
        else:
            print("Autoplaying first video result.")

    def zoom_in(self):
        current_view = self.current_web_view()
        if current_view:
            current_view.setZoomFactor(current_view.zoomFactor() + 0.1)

    def zoom_out(self):
        current_view = self.current_web_view()
        if current_view:
            current_view.setZoomFactor(current_view.zoomFactor() - 0.1)

    def toggle_full_screen(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.setStyleSheet("""
                QWidget { background-color: #181818; color: #FFFFFF; }
                QLineEdit { background-color: #212121; color: #FFFFFF; border: 1px solid #303030; }
                QPushButton { background-color: #212121; color: #FFFFFF; border: 1px solid #303030; }
                QTabWidget::pane { border-top: 1px solid #303030; }
                QTabBar::tab { background-color: #212121; color: #FFFFFF; border: 1px solid #303030; }
                QTabBar::tab:selected { background-color: #303030; }
            """)
            self.dark_mode_btn.setIcon(QIcon("lightmode.png"))  # Assuming you have a light mode icon
        else:
            self.setStyleSheet("")
            self.dark_mode_btn.setIcon(QIcon("darkmode.jpeg"))
        
        # Apply dark mode to all web views
        for i in range(self.tab_widget.count()):
            web_view = self.tab_widget.widget(i)
            self.apply_dark_mode_to_web_view(web_view)

    def apply_dark_mode_to_web_view(self, web_view):
        js = f"""
        (function() {{
            function applyDarkMode(node) {{
                if (node.nodeType === Node.ELEMENT_NODE) {{
                    node.style.setProperty('background-color', '{("#181818" if self.dark_mode else "#FFFFFF")}', 'important');
                    node.style.setProperty('color', '{("#FFFFFF" if self.dark_mode else "#000000")}', 'important');
                    node.style.setProperty('border-color', '{("#303030" if self.dark_mode else "#E5E5E5")}', 'important');
                    
                    if (node.tagName === 'A') {{
                        node.style.setProperty('color', '{("#3EA6FF" if self.dark_mode else "#065FD4")}', 'important');
                    }}
                    
                    if (node.tagName === 'INPUT' || node.tagName === 'TEXTAREA' || node.tagName === 'SELECT') {{
                        node.style.setProperty('background-color', '{("#212121" if self.dark_mode else "#FFFFFF")}', 'important');
                        node.style.setProperty('color', '{("#FFFFFF" if self.dark_mode else "#000000")}', 'important');
                    }}
                }}
                
                for (let child of node.childNodes) {{
                    applyDarkMode(child);
                }}
            }}
            
            document.documentElement.style.colorScheme = '{("dark" if self.dark_mode else "light")}';
            applyDarkMode(document.body);
            
            // Create a MutationObserver to apply dark mode to new elements
            var observer = new MutationObserver(function(mutations) {{
                mutations.forEach(function(mutation) {{
                    mutation.addedNodes.forEach(applyDarkMode);
                }});
            }});
            
            observer.observe(document.body, {{ childList: true, subtree: true }});
        }})();
        """
        
        web_view.page().runJavaScript(js)

    def load_adblock_rules(self):
        # Load EasyList rules
        easylist_url = "https://easylist.to/easylist/easylist.txt"
        response = requests.get(easylist_url)
        rules = AdblockRules(response.text.splitlines())
        
        # Create a custom QWebEngineProfile
        self.web_profile = QWebEngineProfile("AdBlockProfile", self)
        
        # Apply rules to the profile
        self.web_profile.setUrlRequestInterceptor(AdBlockInterceptor(rules))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_D and event.modifiers() == Qt.ShiftModifier:
            self.show_spotlight_search()
        else:
            super().keyPressEvent(event)

    def show_spotlight_search(self):
        # Center the spotlight search on the screen
        screen_geometry = QtWidgets.QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.spotlight_search.width()) // 2
        y = (screen_geometry.height() - self.spotlight_search.height()) // 2
        self.spotlight_search.move(x, y)
        
        self.spotlight_search.search_input.clear()
        self.spotlight_search.results_list.clear()
        self.spotlight_search.show()
        
        # Set focus to the search input after a short delay
        QTimer.singleShot(100, self.spotlight_search.search_input.setFocus)

    def go_home(self):
        self.load_url()  # This will load the default page

    def toggle_vpn(self):
        self.vpn_enabled = not self.vpn_enabled
        if self.vpn_enabled:
            self.enable_vpn()
        else:
            self.disable_vpn()

    def enable_vpn(self):
        # For demonstration purposes, we're using a public HTTPS proxy
        # In a real application, you'd want to use a proper VPN service
        self.proxy.setType(QNetworkProxy.HttpProxy)
        self.proxy.setHostName("203.30.189.169")  # Example proxy IP
        self.proxy.setPort(80)  # Example proxy port
        
        # Create a custom proxy factory
        proxy_factory = CustomProxyFactory(self.proxy)
        
        # Set the proxy for the application
        QNetworkProxyFactory.setApplicationProxyFactory(proxy_factory)
        
        # Apply proxy to all existing tabs
        for i in range(self.tab_widget.count()):
            web_view = self.tab_widget.widget(i)
            web_view.page().profile().setProxyFactory(proxy_factory)
        
        self.vpn_btn.setStyleSheet("background-color: #4CAF50;")  # Green when enabled
        print("VPN enabled")

    def disable_vpn(self):
        # Reset to system proxy settings
        QNetworkProxyFactory.setUseSystemConfiguration(True)
        
        # Remove proxy from all existing tabs
        for i in range(self.tab_widget.count()):
            web_view = self.tab_widget.widget(i)
            web_view.page().profile().setProxyFactory(None)
        
        self.vpn_btn.setStyleSheet("")  # Reset to default style
        print("VPN disabled")

    def on_load_finished(self, ok, web_view):
        if ok:
            current_url = web_view.url().toString()
            if "youtube.com" in current_url:
                self.setup_youtube_fullscreen(web_view)
            if self.dark_mode:
                self.apply_dark_mode_to_web_view(web_view)

    def setup_youtube_fullscreen(self, web_view):
        web_view.page().runJavaScript("""
        (function() {
            var style = document.createElement('style');
            style.textContent = `
                .ytp-fullscreen-button { display: none !important; }
                .custom-fullscreen-button {
                    position: absolute;
                    bottom: 0;
                    right: 0;
                    width: 48px;
                    height: 48px;
                    background-color: rgba(0, 0, 0, 0.5);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    cursor: pointer;
                    z-index: 1000;
                }
            `;
            document.head.appendChild(style);
            
            var button = document.createElement('div');
            button.className = 'custom-fullscreen-button';
            button.innerHTML = '⛶';
            button.onclick = function() {
                var video = document.querySelector('video');
                if (video) {
                    if (video.requestFullscreen) {
                        video.requestFullscreen();
                    } else if (video.webkitRequestFullscreen) {
                        video.webkitRequestFullscreen();
                    }
                }
            };
            
            var observer = new MutationObserver(function(mutations) {
                var videoContainer = document.querySelector('.html5-video-player');
                if (videoContainer && !videoContainer.querySelector('.custom-fullscreen-button')) {
                    videoContainer.appendChild(button);
                    observer.disconnect();
                }
            });
            
            observer.observe(document.body, { childList: true, subtree: true });
        })();
        """)

class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, rules):
        super().__init__()
        self.rules = rules

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        if self.rules.should_block(url):
            info.block(True)
        else:
            # Allow all content types
            info.setHttpHeader(b"Accept", b"*/*")

class SpotlightSearch(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spotlight Search")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search...")
        layout.addWidget(self.search_input)
        
        self.results_list = QListWidget(self)
        layout.addWidget(self.results_list)
        
        self.search_input.textChanged.connect(self.update_results)
        self.results_list.itemActivated.connect(self.open_result)
        
        self.setFixedSize(400, 500)

    def update_results(self, text):
        self.results_list.clear()
        if text:
            # Here you can implement your search logic
            # For now, we'll just add some dummy results
            self.results_list.addItems([f"Result {i} for {text}" for i in range(1, 6)])

    def open_result(self, item):
        # Here you can implement what happens when a result is selected
        print(f"Opening: {item.text()}")
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

# Add this function to handle network errors
def handle_network_error(reply):
    error = reply.error()
    if error == QNetworkReply.ProxyConnectionRefusedError:
        print("The proxy server refused the connection")
    elif error == QNetworkReply.ProxyConnectionClosedError:
        print("The proxy server closed the connection prematurely")
    elif error == QNetworkReply.ProxyNotFoundError:
        print("The proxy server was not found")
    elif error == QNetworkReply.ProxyTimeoutError:
        print("The proxy server connection timed out")
    else:
        print(f"Network error occurred: {reply.errorString()}")

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setApplicationName("Goon")
    
    # Set up global network access manager
    network_manager = QNetworkAccessManager()
    network_manager.finished.connect(handle_network_error)
    
    browser = BrowserApp()
    browser.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()