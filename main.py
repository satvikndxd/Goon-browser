import sys
import os
import asyncio
import threading
import json
from datetime import datetime
import speech_recognition as sr
import darkdetect
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTabWidget, QWidget, QMainWindow,
                             QAction, QToolBar, QDialog, QListWidget, QStyleFactory, QFrame, QLabel, QMessageBox,
                             QGraphicsDropShadowEffect, QSizePolicy, QScrollArea, QGridLayout, QSlider, QProgressBar,
                             QMenu, QWidgetAction, QTextEdit, QComboBox, QCheckBox, QSpinBox, QPlainTextEdit)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtCore import QUrl, Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty, QByteArray, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QPainterPath, QPixmap, QPen, QBrush, QLinearGradient, QFontDatabase, QTextCursor
from PyQt5.QtNetwork import QNetworkProxy, QNetworkProxyFactory, QNetworkAccessManager, QNetworkReply
from PyQt5.QtSvg import QSvgRenderer, QSvgWidget
from adblockparser import AdblockRules
import requests
import google.generativeai as genai
import urllib.parse
import subprocess
import base64

# Try to import browser-use for AI agent functionality
BROWSER_USE_AVAILABLE = False
try:
    from browser_use import Agent, Browser, BrowserConfig
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    BROWSER_USE_AVAILABLE = True
except ImportError:
    print("browser-use not installed. AI Agent features will be disabled.")
    print("Install with: pip install browser-use langchain-anthropic langchain-openai")

# ============================================================================
# BAUHAUS SVG ICONS - Geometric, Primary Colors (Red, Blue, Yellow, Black, White)
# ============================================================================

class BauhausSVG:
    """Bauhaus-style SVG icons using geometric shapes and primary colors"""

    # Color Palette - Bauhaus Primary Colors
    RED = "#E63946"      # Vibrant Red
    BLUE = "#1D3557"     # Deep Blue
    YELLOW = "#F4D35E"   # Golden Yellow
    BLACK = "#0D1B2A"    # Near Black
    WHITE = "#FFFFFF"    # Pure White
    LIGHT_GRAY = "#F8F9FA"

    @staticmethod
    def home():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <rect x="8" y="32" width="48" height="28" fill="#1D3557" rx="2"/>
            <polygon points="32,8 4,36 60,36" fill="#E63946"/>
            <rect x="26" y="42" width="12" height="18" fill="#F4D35E"/>
            <circle cx="34" cy="52" r="1.5" fill="#0D1B2A"/>
        </svg>'''

    @staticmethod
    def new_tab():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <rect x="8" y="8" width="48" height="48" fill="#1D3557" rx="4"/>
            <rect x="28" y="18" width="8" height="28" fill="#F4D35E"/>
            <rect x="18" y="28" width="28" height="8" fill="#F4D35E"/>
            <circle cx="32" cy="32" r="6" fill="#E63946"/>
        </svg>'''

    @staticmethod
    def close_tab():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="24" fill="#E63946"/>
            <rect x="20" y="29" width="24" height="6" fill="#FFFFFF" transform="rotate(45 32 32)"/>
            <rect x="20" y="29" width="24" height="6" fill="#FFFFFF" transform="rotate(-45 32 32)"/>
        </svg>'''

    @staticmethod
    def voice_search():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#F4D35E"/>
            <rect x="26" y="14" width="12" height="24" fill="#1D3557" rx="6"/>
            <path d="M20 32 Q20 48 32 48 Q44 48 44 32" stroke="#1D3557" stroke-width="4" fill="none"/>
            <rect x="30" y="48" width="4" height="8" fill="#1D3557"/>
            <rect x="24" y="54" width="16" height="4" fill="#1D3557" rx="2"/>
        </svg>'''

    @staticmethod
    def fullscreen():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <rect x="8" y="8" width="48" height="48" fill="#1D3557" rx="4"/>
            <polygon points="12,12 28,12 12,28" fill="#F4D35E"/>
            <polygon points="52,12 36,12 52,28" fill="#F4D35E"/>
            <polygon points="12,52 28,52 12,36" fill="#F4D35E"/>
            <polygon points="52,52 36,52 52,36" fill="#F4D35E"/>
        </svg>'''

    @staticmethod
    def dark_mode():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#0D1B2A"/>
            <path d="M32 8 A24 24 0 0 1 32 56 A16 16 0 0 0 32 8" fill="#F4D35E"/>
            <circle cx="44" cy="20" r="2" fill="#FFFFFF"/>
            <circle cx="48" cy="32" r="1.5" fill="#FFFFFF"/>
            <circle cx="44" cy="44" r="2" fill="#FFFFFF"/>
        </svg>'''

    @staticmethod
    def light_mode():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#F4D35E"/>
            <circle cx="32" cy="32" r="14" fill="#E63946"/>
            <g fill="#0D1B2A">
                <rect x="30" y="4" width="4" height="10"/>
                <rect x="30" y="50" width="4" height="10"/>
                <rect x="4" y="30" width="10" height="4"/>
                <rect x="50" y="30" width="10" height="4"/>
            </g>
        </svg>'''

    @staticmethod
    def vpn_on():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#1D3557"/>
            <path d="M32 12 L32 32 L46 44" stroke="#F4D35E" stroke-width="4" fill="none" stroke-linecap="round"/>
            <circle cx="32" cy="32" r="4" fill="#E63946"/>
            <circle cx="32" cy="12" r="4" fill="#E63946"/>
            <circle cx="46" cy="44" r="4" fill="#E63946"/>
            <circle cx="18" cy="44" r="4" fill="#F4D35E"/>
            <path d="M32 32 L18 44" stroke="#F4D35E" stroke-width="4" fill="none" stroke-linecap="round"/>
        </svg>'''

    @staticmethod
    def vpn_off():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#E63946" opacity="0.3"/>
            <circle cx="32" cy="32" r="20" stroke="#1D3557" stroke-width="4" fill="none" stroke-dasharray="8 4"/>
            <rect x="8" y="30" width="48" height="4" fill="#E63946" transform="rotate(45 32 32)"/>
        </svg>'''

    @staticmethod
    def zoom_in():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="28" cy="28" r="20" fill="#1D3557"/>
            <circle cx="28" cy="28" r="14" fill="#FFFFFF"/>
            <rect x="22" y="26" width="12" height="4" fill="#1D3557"/>
            <rect x="26" y="22" width="4" height="12" fill="#1D3557"/>
            <rect x="42" y="42" width="16" height="8" fill="#F4D35E" transform="rotate(45 50 46)" rx="2"/>
        </svg>'''

    @staticmethod
    def zoom_out():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="28" cy="28" r="20" fill="#1D3557"/>
            <circle cx="28" cy="28" r="14" fill="#FFFFFF"/>
            <rect x="22" y="26" width="12" height="4" fill="#1D3557"/>
            <rect x="42" y="42" width="16" height="8" fill="#F4D35E" transform="rotate(45 50 46)" rx="2"/>
        </svg>'''

    @staticmethod
    def back():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#1D3557"/>
            <polygon points="38,18 22,32 38,46" fill="#F4D35E"/>
            <rect x="26" y="28" width="16" height="8" fill="#F4D35E"/>
        </svg>'''

    @staticmethod
    def forward():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#1D3557"/>
            <polygon points="26,18 42,32 26,46" fill="#F4D35E"/>
            <rect x="22" y="28" width="16" height="8" fill="#F4D35E"/>
        </svg>'''

    @staticmethod
    def refresh():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#F4D35E"/>
            <path d="M32 16 A16 16 0 1 1 16 32" stroke="#1D3557" stroke-width="6" fill="none" stroke-linecap="round"/>
            <polygon points="32,8 40,20 24,20" fill="#1D3557"/>
        </svg>'''

    @staticmethod
    def stop():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#E63946"/>
            <rect x="20" y="20" width="24" height="24" fill="#FFFFFF" rx="2"/>
        </svg>'''

    @staticmethod
    def bookmark():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <polygon points="16,8 48,8 48,56 32,44 16,56" fill="#1D3557"/>
            <rect x="22" y="16" width="20" height="4" fill="#F4D35E"/>
            <rect x="22" y="24" width="14" height="4" fill="#F4D35E"/>
        </svg>'''

    @staticmethod
    def bookmark_filled():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <polygon points="16,8 48,8 48,56 32,44 16,56" fill="#E63946"/>
            <circle cx="32" cy="24" r="8" fill="#F4D35E"/>
        </svg>'''

    @staticmethod
    def settings():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#1D3557"/>
            <circle cx="32" cy="32" r="12" fill="#F4D35E"/>
            <circle cx="32" cy="32" r="6" fill="#1D3557"/>
            <g fill="#E63946">
                <rect x="30" y="4" width="4" height="10"/>
                <rect x="30" y="50" width="4" height="10"/>
                <rect x="4" y="30" width="10" height="4"/>
                <rect x="50" y="30" width="10" height="4"/>
                <rect x="10" y="10" width="10" height="4" transform="rotate(45 15 12)"/>
                <rect x="44" y="50" width="10" height="4" transform="rotate(45 49 52)"/>
                <rect x="44" y="10" width="10" height="4" transform="rotate(-45 49 12)"/>
                <rect x="10" y="50" width="10" height="4" transform="rotate(-45 15 52)"/>
            </g>
        </svg>'''

    @staticmethod
    def history():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="36" cy="32" r="24" fill="#F4D35E"/>
            <circle cx="36" cy="32" r="18" fill="#FFFFFF"/>
            <rect x="34" y="18" width="4" height="16" fill="#1D3557"/>
            <rect x="34" y="30" width="12" height="4" fill="#1D3557"/>
            <path d="M8 24 L16 32 L8 40" stroke="#E63946" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M16 32 L8 32 Q4 32 4 36 L4 48" stroke="#E63946" stroke-width="4" fill="none" stroke-linecap="round"/>
        </svg>'''

    @staticmethod
    def download():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <rect x="8" y="8" width="48" height="48" fill="#1D3557" rx="4"/>
            <rect x="28" y="14" width="8" height="24" fill="#F4D35E"/>
            <polygon points="32,50 18,34 46,34" fill="#F4D35E"/>
            <rect x="16" y="52" width="32" height="4" fill="#E63946" rx="2"/>
        </svg>'''

    @staticmethod
    def search():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="28" cy="28" r="18" fill="#F4D35E"/>
            <circle cx="28" cy="28" r="12" fill="#FFFFFF"/>
            <rect x="40" y="38" width="18" height="8" fill="#1D3557" transform="rotate(45 49 42)" rx="2"/>
        </svg>'''

    @staticmethod
    def menu():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <rect x="8" y="8" width="48" height="48" fill="#1D3557" rx="4"/>
            <rect x="16" y="18" width="32" height="6" fill="#F4D35E" rx="2"/>
            <rect x="16" y="29" width="32" height="6" fill="#E63946" rx="2"/>
            <rect x="16" y="40" width="32" height="6" fill="#F4D35E" rx="2"/>
        </svg>'''

    @staticmethod
    def ad_block_on():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#1D3557"/>
            <rect x="18" y="18" width="28" height="28" fill="#E63946" rx="4"/>
            <text x="32" y="40" font-family="Arial Black" font-size="20" fill="#FFFFFF" text-anchor="middle">AD</text>
            <circle cx="32" cy="32" r="26" stroke="#F4D35E" stroke-width="4" fill="none"/>
            <rect x="8" y="30" width="48" height="4" fill="#F4D35E" transform="rotate(45 32 32)"/>
        </svg>'''

    @staticmethod
    def ad_block_off():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#F8F9FA"/>
            <rect x="18" y="18" width="28" height="28" fill="#1D3557" opacity="0.3" rx="4"/>
            <text x="32" y="40" font-family="Arial Black" font-size="20" fill="#1D3557" opacity="0.5" text-anchor="middle">AD</text>
        </svg>'''

    @staticmethod
    def incognito():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#0D1B2A"/>
            <ellipse cx="32" cy="36" rx="24" ry="8" fill="#F4D35E"/>
            <circle cx="22" cy="30" r="10" fill="#FFFFFF"/>
            <circle cx="42" cy="30" r="10" fill="#FFFFFF"/>
            <circle cx="22" cy="30" r="5" fill="#0D1B2A"/>
            <circle cx="42" cy="30" r="5" fill="#0D1B2A"/>
            <rect x="32" y="26" width="8" height="4" fill="#FFFFFF" transform="rotate(-15 36 28)"/>
        </svg>'''

    @staticmethod
    def print_page():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <rect x="8" y="20" width="48" height="28" fill="#1D3557" rx="4"/>
            <rect x="14" y="8" width="36" height="16" fill="#F4D35E"/>
            <rect x="14" y="44" width="36" height="16" fill="#FFFFFF"/>
            <rect x="18" y="48" width="28" height="3" fill="#1D3557"/>
            <rect x="18" y="54" width="20" height="3" fill="#1D3557"/>
            <circle cx="48" cy="32" r="4" fill="#E63946"/>
        </svg>'''

    @staticmethod
    def share():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="48" cy="16" r="10" fill="#E63946"/>
            <circle cx="16" cy="32" r="10" fill="#F4D35E"/>
            <circle cx="48" cy="48" r="10" fill="#1D3557"/>
            <line x1="24" y1="28" x2="40" y2="20" stroke="#0D1B2A" stroke-width="4"/>
            <line x1="24" y1="36" x2="40" y2="44" stroke="#0D1B2A" stroke-width="4"/>
        </svg>'''

    @staticmethod
    def screenshot():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <rect x="8" y="14" width="48" height="36" fill="#1D3557" rx="4"/>
            <circle cx="32" cy="32" r="12" fill="#F4D35E"/>
            <circle cx="32" cy="32" r="8" fill="#FFFFFF"/>
            <circle cx="32" cy="32" r="4" fill="#E63946"/>
            <circle cx="48" cy="20" r="4" fill="#E63946"/>
        </svg>'''

    @staticmethod
    def dev_tools():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <rect x="8" y="8" width="48" height="48" fill="#0D1B2A" rx="4"/>
            <text x="14" y="28" font-family="monospace" font-size="12" fill="#F4D35E">&lt;/&gt;</text>
            <rect x="14" y="34" width="24" height="3" fill="#E63946"/>
            <rect x="14" y="40" width="32" height="3" fill="#F4D35E"/>
            <rect x="14" y="46" width="18" height="3" fill="#FFFFFF"/>
        </svg>'''

    @staticmethod
    def extensions():
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <rect x="8" y="24" width="24" height="32" fill="#1D3557" rx="2"/>
            <rect x="32" y="24" width="24" height="32" fill="#F4D35E" rx="2"/>
            <circle cx="32" cy="16" r="12" fill="#E63946"/>
        </svg>'''

    @staticmethod
    def ai_agent():
        """AI Agent icon - Robot/AI brain design"""
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#1D3557"/>
            <rect x="18" y="20" width="28" height="24" fill="#F4D35E" rx="4"/>
            <circle cx="26" cy="30" r="4" fill="#1D3557"/>
            <circle cx="38" cy="30" r="4" fill="#1D3557"/>
            <rect x="24" y="38" width="16" height="4" fill="#1D3557" rx="2"/>
            <rect x="14" y="26" width="4" height="12" fill="#E63946" rx="2"/>
            <rect x="46" y="26" width="4" height="12" fill="#E63946" rx="2"/>
            <rect x="28" y="12" width="8" height="8" fill="#E63946"/>
            <circle cx="32" cy="10" r="4" fill="#F4D35E"/>
            <rect x="26" y="44" width="12" height="6" fill="#E63946" rx="2"/>
            <rect x="22" y="50" width="6" height="8" fill="#1D3557" rx="2"/>
            <rect x="36" y="50" width="6" height="8" fill="#1D3557" rx="2"/>
        </svg>'''

    @staticmethod
    def ai_agent_running():
        """AI Agent icon when running - Animated style"""
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#E63946"/>
            <rect x="18" y="20" width="28" height="24" fill="#F4D35E" rx="4"/>
            <circle cx="26" cy="30" r="4" fill="#1D3557">
                <animate attributeName="r" values="3;5;3" dur="0.5s" repeatCount="indefinite"/>
            </circle>
            <circle cx="38" cy="30" r="4" fill="#1D3557">
                <animate attributeName="r" values="5;3;5" dur="0.5s" repeatCount="indefinite"/>
            </circle>
            <rect x="24" y="38" width="16" height="4" fill="#1D3557" rx="2"/>
            <rect x="14" y="26" width="4" height="12" fill="#FFFFFF" rx="2"/>
            <rect x="46" y="26" width="4" height="12" fill="#FFFFFF" rx="2"/>
            <rect x="28" y="12" width="8" height="8" fill="#FFFFFF"/>
            <circle cx="32" cy="10" r="4" fill="#F4D35E"/>
        </svg>'''

    @staticmethod
    def ai_thinking():
        """AI thinking/processing icon"""
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#F4D35E"/>
            <circle cx="20" cy="32" r="6" fill="#1D3557"/>
            <circle cx="32" cy="32" r="6" fill="#E63946"/>
            <circle cx="44" cy="32" r="6" fill="#1D3557"/>
        </svg>'''

    @staticmethod
    def ai_success():
        """AI task completed successfully"""
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#27AE60"/>
            <polyline points="20,32 28,40 44,24" stroke="#FFFFFF" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>'''

    @staticmethod
    def ai_error():
        """AI task failed"""
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#E63946"/>
            <rect x="28" y="16" width="8" height="24" fill="#FFFFFF" rx="2"/>
            <circle cx="32" cy="48" r="4" fill="#FFFFFF"/>
        </svg>'''


def svg_to_icon(svg_string, size=32):
    """Convert SVG string to QIcon"""
    svg_bytes = QByteArray(svg_string.encode('utf-8'))
    renderer = QSvgRenderer(svg_bytes)

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def svg_to_pixmap(svg_string, size=32):
    """Convert SVG string to QPixmap"""
    svg_bytes = QByteArray(svg_string.encode('utf-8'))
    renderer = QSvgRenderer(svg_bytes)

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return pixmap


# ============================================================================
# BAUHAUS STYLED WIDGETS
# ============================================================================

class BauhausColors:
    """Bauhaus Design System Colors"""
    RED = "#E63946"
    BLUE = "#1D3557"
    YELLOW = "#F4D35E"
    BLACK = "#0D1B2A"
    WHITE = "#FFFFFF"
    LIGHT_BG = "#F8F9FA"
    DARK_BG = "#0D1B2A"
    ACCENT = "#457B9D"  # Secondary blue


class BauhausButton(QPushButton):
    """Bauhaus-styled geometric button"""
    def __init__(self, svg_string=None, text="", parent=None, primary=False, size=40):
        super().__init__(text, parent)
        self.svg_string = svg_string
        self.is_primary = primary
        self.btn_size = size
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)

        if svg_string:
            self.setIcon(svg_to_icon(svg_string, size - 8))
            self.setIconSize(QSize(size - 8, size - 8))

        self.apply_style()

    def apply_style(self):
        if self.is_primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BauhausColors.RED};
                    border: none;
                    border-radius: {self.btn_size // 2}px;
                }}
                QPushButton:hover {{
                    background-color: {BauhausColors.YELLOW};
                }}
                QPushButton:pressed {{
                    background-color: {BauhausColors.BLUE};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: {self.btn_size // 2}px;
                }}
                QPushButton:hover {{
                    background-color: rgba(29, 53, 87, 0.1);
                }}
                QPushButton:pressed {{
                    background-color: rgba(29, 53, 87, 0.2);
                }}
            """)


class BauhausURLBar(QLineEdit):
    """Bauhaus-styled URL input bar"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Search or enter URL...")
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BauhausColors.WHITE};
                border: 3px solid {BauhausColors.BLUE};
                border-radius: 24px;
                padding: 12px 20px;
                font-size: 14px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                color: {BauhausColors.BLACK};
                selection-background-color: {BauhausColors.YELLOW};
            }}
            QLineEdit:focus {{
                border-color: {BauhausColors.RED};
            }}
        """)


class BauhausTabWidget(QTabWidget):
    """Bauhaus-styled tab widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {BauhausColors.WHITE};
            }}
            QTabWidget::tab-bar {{
                left: 0px;
            }}
            QTabBar {{
                background-color: {BauhausColors.LIGHT_BG};
            }}
            QTabBar::tab {{
                background-color: {BauhausColors.WHITE};
                border: none;
                border-bottom: 4px solid transparent;
                padding: 12px 20px;
                margin-right: 2px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
                font-weight: 500;
                color: {BauhausColors.BLACK};
                min-width: 120px;
            }}
            QTabBar::tab:selected {{
                background-color: {BauhausColors.WHITE};
                border-bottom: 4px solid {BauhausColors.RED};
                color: {BauhausColors.BLUE};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {BauhausColors.LIGHT_BG};
                border-bottom: 4px solid {BauhausColors.YELLOW};
            }}
            QTabBar::close-button {{
                image: none;
                background: {BauhausColors.RED};
                border-radius: 8px;
                width: 16px;
                height: 16px;
                margin: 4px;
            }}
            QTabBar::close-button:hover {{
                background: {BauhausColors.BLUE};
            }}
        """)


class BauhausSidebar(QWidget):
    """Bauhaus-styled sidebar with geometric accents"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(60)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(12)

        # Geometric accent at top
        accent = QLabel()
        accent.setFixedSize(44, 8)
        accent.setStyleSheet(f"background-color: {BauhausColors.RED}; border-radius: 4px;")
        layout.addWidget(accent, alignment=Qt.AlignCenter)

        layout.addSpacing(20)

        # Sidebar buttons will be added by the main app
        self.button_layout = QVBoxLayout()
        self.button_layout.setSpacing(8)
        layout.addLayout(self.button_layout)

        layout.addStretch()

        # Bottom geometric accent
        bottom_accent = QLabel()
        bottom_accent.setFixedSize(20, 20)
        bottom_accent.setStyleSheet(f"""
            background-color: {BauhausColors.YELLOW};
            border-radius: 10px;
        """)
        layout.addWidget(bottom_accent, alignment=Qt.AlignCenter)

        self.setStyleSheet(f"""
            BauhausSidebar {{
                background-color: {BauhausColors.BLUE};
                border-radius: 0px;
            }}
        """)

    def add_button(self, svg_string, callback, tooltip=""):
        btn = BauhausButton(svg_string, size=44)
        btn.clicked.connect(callback)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 22px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.3);
            }}
        """)
        self.button_layout.addWidget(btn, alignment=Qt.AlignCenter)
        return btn


class BauhausStatusIndicator(QWidget):
    """Bauhaus-styled status indicator (circle)"""
    def __init__(self, color=None, size=12, parent=None):
        super().__init__(parent)
        self.color = color or BauhausColors.YELLOW
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(self.color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())

    def set_color(self, color):
        self.color = color
        self.update()


# ============================================================================
# WEB VIEW
# ============================================================================

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


# ============================================================================
# SPOTLIGHT SEARCH DIALOG - BAUHAUS STYLE
# ============================================================================

class SpotlightSearch(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser = parent
        self.setWindowTitle("Quick Search")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Container with shadow
        container = QWidget()
        container.setObjectName("spotlightContainer")
        container.setStyleSheet(f"""
            #spotlightContainer {{
                background-color: {BauhausColors.WHITE};
                border: 4px solid {BauhausColors.BLUE};
                border-radius: 16px;
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(16)

        # Geometric header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        red_circle = QLabel()
        red_circle.setFixedSize(24, 24)
        red_circle.setStyleSheet(f"background-color: {BauhausColors.RED}; border-radius: 12px;")

        yellow_square = QLabel()
        yellow_square.setFixedSize(24, 24)
        yellow_square.setStyleSheet(f"background-color: {BauhausColors.YELLOW}; border-radius: 4px;")

        blue_triangle = QLabel()
        blue_triangle.setFixedSize(24, 24)
        blue_triangle.setStyleSheet(f"background-color: {BauhausColors.BLUE};")

        title = QLabel("QUICK SEARCH")
        title.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 3px;
            color: {BauhausColors.BLUE};
        """)

        header_layout.addWidget(red_circle)
        header_layout.addWidget(yellow_square)
        header_layout.addWidget(blue_triangle)
        header_layout.addSpacing(16)
        header_layout.addWidget(title)
        header_layout.addStretch()

        container_layout.addWidget(header)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BauhausColors.LIGHT_BG};
                border: 3px solid {BauhausColors.BLUE};
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 16px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                color: {BauhausColors.BLACK};
            }}
            QLineEdit:focus {{
                border-color: {BauhausColors.RED};
            }}
        """)
        container_layout.addWidget(self.search_input)

        # Results list
        self.results_list = QListWidget()
        self.results_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {BauhausColors.LIGHT_BG};
                border: none;
                border-radius: 12px;
                padding: 8px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
            }}
            QListWidget::item {{
                background-color: {BauhausColors.WHITE};
                border-left: 4px solid transparent;
                padding: 12px 16px;
                margin: 4px 0;
                border-radius: 8px;
            }}
            QListWidget::item:selected {{
                background-color: {BauhausColors.YELLOW};
                border-left: 4px solid {BauhausColors.RED};
                color: {BauhausColors.BLACK};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {BauhausColors.LIGHT_BG};
                border-left: 4px solid {BauhausColors.BLUE};
            }}
        """)
        container_layout.addWidget(self.results_list)

        # Quick actions
        actions_label = QLabel("QUICK ACTIONS")
        actions_label.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
            color: {BauhausColors.ACCENT};
            margin-top: 8px;
        """)
        container_layout.addWidget(actions_label)

        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        quick_actions = [
            ("New Tab", BauhausColors.BLUE),
            ("Dark Mode", BauhausColors.BLACK),
            ("History", BauhausColors.YELLOW),
            ("Settings", BauhausColors.RED),
        ]

        for text, color in quick_actions:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: {BauhausColors.WHITE if color != BauhausColors.YELLOW else BauhausColors.BLACK};
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    font-size: 12px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                }}
            """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, t=text: self.handle_quick_action(t))
            actions_layout.addWidget(btn)

        container_layout.addWidget(actions_widget)

        main_layout.addWidget(container)

        # Connections
        self.search_input.textChanged.connect(self.update_results)
        self.search_input.returnPressed.connect(self.perform_search)
        self.results_list.itemActivated.connect(self.open_result)

        self.setFixedSize(500, 450)

        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 10)
        container.setGraphicsEffect(shadow)

    def handle_quick_action(self, action):
        if action == "New Tab" and self.browser:
            self.browser.add_new_tab()
        elif action == "Dark Mode" and self.browser:
            self.browser.toggle_dark_mode()
        elif action == "History" and self.browser:
            self.browser.add_new_tab("chrome://history")
        elif action == "Settings" and self.browser:
            self.browser.show_settings()
        self.close()

    def update_results(self, text):
        self.results_list.clear()
        if text:
            suggestions = [
                f"🔍 Search Google for: {text}",
                f"🦆 Search DuckDuckGo for: {text}",
                f"📺 Search YouTube for: {text}",
                f"🌐 Go to: {text}.com",
                f"📚 Search Wikipedia for: {text}",
            ]
            self.results_list.addItems(suggestions)

    def perform_search(self):
        text = self.search_input.text()
        if text and self.browser:
            self.browser.url_input.setText(text)
            self.browser.load_url()
            self.close()

    def open_result(self, item):
        text = item.text()
        if self.browser:
            if "Google" in text:
                query = self.search_input.text()
                self.browser.add_new_tab(f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}")
            elif "DuckDuckGo" in text:
                query = self.search_input.text()
                self.browser.add_new_tab(f"https://duckduckgo.com/?q={urllib.parse.quote_plus(query)}")
            elif "YouTube" in text:
                query = self.search_input.text()
                self.browser.add_new_tab(f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}")
            elif "Go to" in text:
                query = self.search_input.text()
                url = query if query.startswith(('http://', 'https://')) else f"https://{query}.com"
                self.browser.add_new_tab(url)
            elif "Wikipedia" in text:
                query = self.search_input.text()
                self.browser.add_new_tab(f"https://en.wikipedia.org/wiki/Special:Search?search={urllib.parse.quote_plus(query)}")
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


# ============================================================================
# SETTINGS DIALOG - BAUHAUS STYLE
# ============================================================================

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser = parent
        self.setWindowTitle("Settings")
        self.setFixedSize(600, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QLabel("SETTINGS")
        header.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 4px;
            color: {BauhausColors.BLUE};
        """)
        layout.addWidget(header)

        # Geometric divider
        divider = QWidget()
        divider.setFixedHeight(8)
        divider_layout = QHBoxLayout(divider)
        divider_layout.setContentsMargins(0, 0, 0, 0)
        divider_layout.setSpacing(4)

        for color in [BauhausColors.RED, BauhausColors.YELLOW, BauhausColors.BLUE]:
            segment = QLabel()
            segment.setFixedHeight(8)
            segment.setStyleSheet(f"background-color: {color};")
            divider_layout.addWidget(segment)

        layout.addWidget(divider)

        # Settings content would go here
        content = QLabel("Settings options will appear here.\n\nComing soon:\n• Privacy settings\n• Search engine selection\n• Appearance customization\n• Extensions management")
        content.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            color: {BauhausColors.BLACK};
            padding: 20px;
            background-color: {BauhausColors.LIGHT_BG};
            border-radius: 12px;
        """)
        content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(content)

        layout.addStretch()

        # Close button
        close_btn = QPushButton("CLOSE")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BauhausColors.BLUE};
                color: {BauhausColors.WHITE};
                border: none;
                border-radius: 8px;
                padding: 12px 32px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background-color: {BauhausColors.RED};
            }}
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        self.setStyleSheet(f"""
            SettingsDialog {{
                background-color: {BauhausColors.WHITE};
            }}
        """)


# ============================================================================
# AI AGENT WORKER THREAD
# ============================================================================

class AIAgentWorker(QObject):
    """Worker class for running AI Agent tasks in a separate thread"""
    progress = pyqtSignal(str)  # Emits progress messages
    step_completed = pyqtSignal(str, str)  # Emits step description and result
    finished = pyqtSignal(str, bool)  # Emits final result and success status
    screenshot = pyqtSignal(str)  # Emits screenshot path

    def __init__(self, task, llm_provider="anthropic", api_key=None, headless=True, max_steps=25):
        super().__init__()
        self.task = task
        self.llm_provider = llm_provider
        self.api_key = api_key
        self.headless = headless
        self.max_steps = max_steps
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        """Execute the AI agent task"""
        if not BROWSER_USE_AVAILABLE:
            self.finished.emit("browser-use library not installed. Please run: pip install browser-use langchain-anthropic langchain-openai", False)
            return

        try:
            # Set API key in environment if provided
            if self.api_key:
                if self.llm_provider == "anthropic":
                    os.environ["ANTHROPIC_API_KEY"] = self.api_key
                elif self.llm_provider == "openai":
                    os.environ["OPENAI_API_KEY"] = self.api_key

            self.progress.emit("🤖 Initializing AI Agent...")

            # Create LLM based on provider
            if self.llm_provider == "anthropic":
                llm = ChatAnthropic(model="claude-sonnet-4-20250514")
            else:
                llm = ChatOpenAI(model="gpt-4o")

            self.progress.emit("🌐 Starting browser...")

            # Create browser configuration
            browser_config = BrowserConfig(
                headless=self.headless,
            )

            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Run the agent
                result = loop.run_until_complete(self._run_agent(llm, browser_config))
                self.finished.emit(result, True)
            finally:
                loop.close()

        except Exception as e:
            self.finished.emit(f"Error: {str(e)}", False)

    async def _run_agent(self, llm, browser_config):
        """Async method to run the agent"""
        self.progress.emit("🧠 Creating AI Agent...")

        browser = Browser(config=browser_config)

        agent = Agent(
            task=self.task,
            llm=llm,
            browser=browser,
        )

        self.progress.emit(f"📋 Task: {self.task}")
        self.progress.emit("🚀 Starting execution...")

        # Custom callback to capture steps
        step_count = 0

        try:
            result = await agent.run(max_steps=self.max_steps)

            # Format the result
            if hasattr(result, 'final_result'):
                return f"✅ Task completed!\n\nResult:\n{result.final_result()}"
            else:
                return f"✅ Task completed!\n\nResult:\n{str(result)}"

        except Exception as e:
            return f"❌ Agent error: {str(e)}"
        finally:
            await browser.close()


class AIAgentThread(QThread):
    """Thread wrapper for AI Agent Worker"""
    progress = pyqtSignal(str)
    step_completed = pyqtSignal(str, str)
    finished_signal = pyqtSignal(str, bool)
    screenshot = pyqtSignal(str)

    def __init__(self, task, llm_provider="anthropic", api_key=None, headless=True, max_steps=25):
        super().__init__()
        self.worker = AIAgentWorker(task, llm_provider, api_key, headless, max_steps)
        self.worker.progress.connect(self.progress.emit)
        self.worker.step_completed.connect(self.step_completed.emit)
        self.worker.finished.connect(self.finished_signal.emit)
        self.worker.screenshot.connect(self.screenshot.emit)

    def run(self):
        self.worker.run()

    def stop(self):
        self.worker.stop()


# ============================================================================
# AI AGENT DIALOG - BAUHAUS STYLE
# ============================================================================

class AIAgentDialog(QDialog):
    """Dialog for AI Agent task input and progress display"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser = parent
        self.agent_thread = None
        self.setWindowTitle("AI Agent - Browse for You")
        self.setMinimumSize(700, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header with Bauhaus styling
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # AI Agent icon
        icon_label = QLabel()
        icon_pixmap = svg_to_pixmap(BauhausSVG.ai_agent(), 48)
        icon_label.setPixmap(icon_pixmap)
        header_layout.addWidget(icon_label)

        # Title
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(16, 0, 0, 0)
        title_layout.setSpacing(4)

        title = QLabel("AI AGENT")
        title.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 4px;
            color: {BauhausColors.BLUE};
        """)
        title_layout.addWidget(title)

        subtitle = QLabel("Let AI browse the web for you")
        subtitle.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 13px;
            color: {BauhausColors.ACCENT};
        """)
        title_layout.addWidget(subtitle)

        header_layout.addWidget(title_widget)
        header_layout.addStretch()

        layout.addWidget(header_widget)

        # Geometric divider
        divider = QWidget()
        divider.setFixedHeight(8)
        divider_layout = QHBoxLayout(divider)
        divider_layout.setContentsMargins(0, 0, 0, 0)
        divider_layout.setSpacing(4)

        for color in [BauhausColors.RED, BauhausColors.YELLOW, BauhausColors.BLUE]:
            segment = QLabel()
            segment.setFixedHeight(8)
            segment.setStyleSheet(f"background-color: {color};")
            divider_layout.addWidget(segment)

        layout.addWidget(divider)

        # Task input area
        task_label = QLabel("TASK DESCRIPTION")
        task_label.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 2px;
            color: {BauhausColors.BLUE};
            margin-top: 8px;
        """)
        layout.addWidget(task_label)

        self.task_input = QTextEdit()
        self.task_input.setPlaceholderText(
            "Describe what you want the AI to do...\n\n"
            "Examples:\n"
            "• Go to Amazon, search for mechanical keyboards under $50, and list the top 3 results\n"
            "• Navigate to GitHub and find the most starred Python repositories\n"
            "• Go to Wikipedia and summarize the article about Bauhaus architecture\n"
            "• Search for flights from NYC to London on Google Flights and find the cheapest option"
        )
        self.task_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BauhausColors.LIGHT_BG};
                border: 3px solid {BauhausColors.BLUE};
                border-radius: 12px;
                padding: 16px;
                font-size: 14px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                color: {BauhausColors.BLACK};
            }}
            QTextEdit:focus {{
                border-color: {BauhausColors.RED};
            }}
        """)
        self.task_input.setMinimumHeight(120)
        layout.addWidget(self.task_input)

        # Settings row
        settings_widget = QWidget()
        settings_layout = QHBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(16)

        # LLM Provider
        provider_label = QLabel("AI Provider:")
        provider_label.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 13px;
            color: {BauhausColors.BLACK};
        """)
        settings_layout.addWidget(provider_label)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Anthropic (Claude)", "OpenAI (GPT-4)"])
        self.provider_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {BauhausColors.WHITE};
                border: 2px solid {BauhausColors.BLUE};
                border-radius: 8px;
                padding: 8px 16px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
                min-width: 150px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid {BauhausColors.BLUE};
            }}
        """)
        settings_layout.addWidget(self.provider_combo)

        # Headless checkbox
        self.headless_checkbox = QCheckBox("Run headless (invisible browser)")
        self.headless_checkbox.setChecked(False)
        self.headless_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
                color: {BauhausColors.BLACK};
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid {BauhausColors.BLUE};
            }}
            QCheckBox::indicator:checked {{
                background-color: {BauhausColors.RED};
                border-color: {BauhausColors.RED};
            }}
        """)
        settings_layout.addWidget(self.headless_checkbox)

        # Max steps
        steps_label = QLabel("Max steps:")
        steps_label.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 13px;
            color: {BauhausColors.BLACK};
        """)
        settings_layout.addWidget(steps_label)

        self.max_steps_spin = QSpinBox()
        self.max_steps_spin.setRange(5, 100)
        self.max_steps_spin.setValue(25)
        self.max_steps_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {BauhausColors.WHITE};
                border: 2px solid {BauhausColors.BLUE};
                border-radius: 8px;
                padding: 8px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
                min-width: 70px;
            }}
        """)
        settings_layout.addWidget(self.max_steps_spin)

        settings_layout.addStretch()
        layout.addWidget(settings_widget)

        # API Key input
        api_key_widget = QWidget()
        api_key_layout = QHBoxLayout(api_key_widget)
        api_key_layout.setContentsMargins(0, 0, 0, 0)
        api_key_layout.setSpacing(12)

        api_label = QLabel("API Key:")
        api_label.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 13px;
            color: {BauhausColors.BLACK};
        """)
        api_key_layout.addWidget(api_label)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API key (or set ANTHROPIC_API_KEY/OPENAI_API_KEY env var)")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BauhausColors.WHITE};
                border: 2px solid {BauhausColors.BLUE};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
            }}
            QLineEdit:focus {{
                border-color: {BauhausColors.RED};
            }}
        """)
        api_key_layout.addWidget(self.api_key_input)

        layout.addWidget(api_key_widget)

        # Progress/Output area
        output_label = QLabel("OUTPUT")
        output_label.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 2px;
            color: {BauhausColors.BLUE};
            margin-top: 8px;
        """)
        layout.addWidget(output_label)

        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Agent output will appear here...")
        self.output_text.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {BauhausColors.BLACK};
                border: 3px solid {BauhausColors.BLUE};
                border-radius: 12px;
                padding: 16px;
                font-size: 13px;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                color: {BauhausColors.YELLOW};
            }}
        """)
        layout.addWidget(self.output_text)

        # Status indicator
        self.status_widget = QWidget()
        status_layout = QHBoxLayout(self.status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.status_indicator = BauhausStatusIndicator(BauhausColors.ACCENT, 12)
        status_layout.addWidget(self.status_indicator)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 13px;
            color: {BauhausColors.ACCENT};
            margin-left: 8px;
        """)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        layout.addWidget(self.status_widget)

        # Buttons
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(12)

        # Example tasks button
        examples_btn = QPushButton("📋 Examples")
        examples_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BauhausColors.YELLOW};
                color: {BauhausColors.BLACK};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #E5C54E;
            }}
        """)
        examples_btn.clicked.connect(self.show_examples)
        button_layout.addWidget(examples_btn)

        # Clear button
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BauhausColors.LIGHT_BG};
                color: {BauhausColors.BLACK};
                border: 2px solid {BauhausColors.BLUE};
                border-radius: 8px;
                padding: 12px 24px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {BauhausColors.BLUE};
                color: {BauhausColors.WHITE};
            }}
        """)
        clear_btn.clicked.connect(self.clear_output)
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        # Stop button
        self.stop_btn = QPushButton("⬛ Stop")
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BauhausColors.RED};
                color: {BauhausColors.WHITE};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #C82333;
            }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
            }}
        """)
        self.stop_btn.clicked.connect(self.stop_agent)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        # Run button
        self.run_btn = QPushButton("▶️ RUN AGENT")
        self.run_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BauhausColors.BLUE};
                color: {BauhausColors.WHITE};
                border: none;
                border-radius: 8px;
                padding: 12px 32px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background-color: {BauhausColors.RED};
            }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
            }}
        """)
        self.run_btn.clicked.connect(self.run_agent)
        button_layout.addWidget(self.run_btn)

        layout.addWidget(button_widget)

        # Set dialog style
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BauhausColors.WHITE};
            }}
        """)

    def show_examples(self):
        """Show example tasks"""
        examples = [
            "Go to Amazon, search for 'mechanical keyboard' under $100, and list the top 5 results with prices",
            "Navigate to GitHub trending and find the top 3 Python repositories from this week",
            "Go to Hacker News and summarize the top 5 stories",
            "Search Google for 'best pizza in New York' and list the top 3 rated restaurants",
            "Go to Wikipedia and give me a brief summary of the Bauhaus art movement",
            "Navigate to YouTube and find the most viewed video this month",
            "Go to Reddit r/programming and tell me what the top 3 posts are about",
            "Search for flights from San Francisco to Tokyo on Google Flights and find the cheapest option",
        ]

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {BauhausColors.WHITE};
                border: 3px solid {BauhausColors.BLUE};
                border-radius: 8px;
                padding: 8px;
            }}
            QMenu::item {{
                padding: 10px 16px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 12px;
                color: {BauhausColors.BLACK};
            }}
            QMenu::item:selected {{
                background-color: {BauhausColors.YELLOW};
            }}
        """)

        for example in examples:
            action = menu.addAction(example[:60] + "..." if len(example) > 60 else example)
            action.setData(example)

        action = menu.exec_(QtWidgets.QCursor.pos())
        if action:
            self.task_input.setText(action.data())

    def clear_output(self):
        """Clear the output text"""
        self.output_text.clear()
        self.status_label.setText("Ready")
        self.status_indicator.set_color(BauhausColors.ACCENT)

    def run_agent(self):
        """Start the AI agent"""
        task = self.task_input.toPlainText().strip()

        if not task:
            QMessageBox.warning(self, "No Task", "Please enter a task description.")
            return

        if not BROWSER_USE_AVAILABLE:
            QMessageBox.critical(
                self,
                "Missing Dependencies",
                "browser-use library is not installed.\n\n"
                "Please install it with:\n"
                "pip install browser-use langchain-anthropic langchain-openai playwright\n"
                "playwright install"
            )
            return

        # Get settings
        provider = "anthropic" if self.provider_combo.currentIndex() == 0 else "openai"
        api_key = self.api_key_input.text().strip() or None
        headless = self.headless_checkbox.isChecked()
        max_steps = self.max_steps_spin.value()

        # Check for API key
        env_key = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
        if not api_key and not os.environ.get(env_key):
            QMessageBox.warning(
                self,
                "API Key Required",
                f"Please enter your {provider.title()} API key or set the {env_key} environment variable."
            )
            return

        # Update UI state
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.task_input.setEnabled(False)
        self.status_label.setText("Running...")
        self.status_indicator.set_color(BauhausColors.YELLOW)

        self.output_text.clear()
        self.append_output(f"{'='*60}")
        self.append_output(f"🤖 AI AGENT TASK")
        self.append_output(f"{'='*60}")
        self.append_output(f"Task: {task}")
        self.append_output(f"Provider: {provider.title()}")
        self.append_output(f"Headless: {headless}")
        self.append_output(f"Max Steps: {max_steps}")
        self.append_output(f"{'='*60}\n")

        # Create and start the agent thread
        self.agent_thread = AIAgentThread(task, provider, api_key, headless, max_steps)
        self.agent_thread.progress.connect(self.on_progress)
        self.agent_thread.finished_signal.connect(self.on_finished)
        self.agent_thread.start()

    def stop_agent(self):
        """Stop the running agent"""
        if self.agent_thread:
            self.agent_thread.stop()
            self.append_output("\n⚠️ Stopping agent...")

    def on_progress(self, message):
        """Handle progress updates"""
        self.append_output(message)

    def on_finished(self, result, success):
        """Handle agent completion"""
        self.append_output(f"\n{'='*60}")
        self.append_output(result)
        self.append_output(f"{'='*60}")

        # Update UI state
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.task_input.setEnabled(True)

        if success:
            self.status_label.setText("Completed")
            self.status_indicator.set_color("#27AE60")  # Green
        else:
            self.status_label.setText("Failed")
            self.status_indicator.set_color(BauhausColors.RED)

        self.agent_thread = None

    def append_output(self, text):
        """Append text to output area"""
        self.output_text.appendPlainText(text)
        # Scroll to bottom
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        """Handle dialog close"""
        if self.agent_thread and self.agent_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Agent Running",
                "An agent is still running. Stop it and close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.stop_agent()
                self.agent_thread.wait(5000)  # Wait up to 5 seconds
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# ============================================================================
# AD BLOCK INTERCEPTOR
# ============================================================================

class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, rules):
        super().__init__()
        self.rules = rules

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        if self.rules.should_block(url):
            info.block(True)
        else:
            info.setHttpHeader(b"Accept", b"*/*")


# ============================================================================
# MAIN BROWSER APPLICATION - BAUHAUS DESIGN
# ============================================================================

class BrowserApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize settings
        self.vpn_enabled = False
        self.ad_block_enabled = True
        self.proxy = QNetworkProxy()
        self.dark_mode = False

        self.setWindowTitle('Comet Browser')
        self.setMinimumSize(1200, 800)
        self.showMaximized()

        # Load ad-blocking rules first
        self.load_adblock_rules()

        # Setup UI
        self.setup_ui()

        # Add initial tab
        self.add_new_tab()

        # Setup spotlight search
        self.spotlight_search = SpotlightSearch(self)

        # Apply initial theme
        self.apply_theme()

    def setup_ui(self):
        """Setup the main Bauhaus-styled UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Sidebar
        self.sidebar = BauhausSidebar()
        self.setup_sidebar()
        main_layout.addWidget(self.sidebar)

        # Main content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top toolbar
        self.setup_toolbar(content_layout)

        # Tab widget
        self.tab_widget = BauhausTabWidget()
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.update_url_bar)
        content_layout.addWidget(self.tab_widget)

        # Bottom status bar
        self.setup_status_bar(content_layout)

        main_layout.addWidget(content_widget)

    def setup_sidebar(self):
        """Setup sidebar buttons"""
        # Home
        self.sidebar.add_button(BauhausSVG.home(), self.go_home, "Home")

        # New tab
        self.sidebar.add_button(BauhausSVG.new_tab(), self.add_new_tab, "New Tab")

        # Bookmarks
        self.sidebar.add_button(BauhausSVG.bookmark(), self.show_bookmarks, "Bookmarks")

        # History
        self.sidebar.add_button(BauhausSVG.history(), self.show_history, "History")

        # Downloads
        self.sidebar.add_button(BauhausSVG.download(), self.show_downloads, "Downloads")

        # Spacer
        spacer = QWidget()
        spacer.setFixedHeight(20)
        self.sidebar.button_layout.addWidget(spacer)

        # VPN
        self.vpn_btn = self.sidebar.add_button(BauhausSVG.vpn_off(), self.toggle_vpn, "VPN")

        # Ad Block
        self.ad_block_btn = self.sidebar.add_button(BauhausSVG.ad_block_on(), self.toggle_ad_block, "Ad Blocker")

        # Dark Mode
        self.dark_mode_btn = self.sidebar.add_button(BauhausSVG.dark_mode(), self.toggle_dark_mode, "Dark Mode")

        # Spacer
        spacer2 = QWidget()
        spacer2.setFixedHeight(20)
        self.sidebar.button_layout.addWidget(spacer2)

        # AI Agent - Prominent placement
        self.ai_agent_btn = self.sidebar.add_button(BauhausSVG.ai_agent(), self.show_ai_agent, "AI Agent")
        # Make AI Agent button stand out with a special style
        self.ai_agent_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BauhausColors.YELLOW};
                border: none;
                border-radius: 22px;
            }}
            QPushButton:hover {{
                background-color: {BauhausColors.RED};
            }}
            QPushButton:pressed {{
                background-color: {BauhausColors.WHITE};
            }}
        """)

        # Settings
        self.sidebar.add_button(BauhausSVG.settings(), self.show_settings, "Settings")

    def setup_toolbar(self, parent_layout):
        """Setup the top toolbar with navigation and URL bar"""
        toolbar = QWidget()
        toolbar.setFixedHeight(72)
        toolbar.setStyleSheet(f"background-color: {BauhausColors.LIGHT_BG};")

        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        toolbar_layout.setSpacing(12)

        # Navigation buttons
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(8)

        # Back button
        self.back_btn = BauhausButton(BauhausSVG.back(), size=44)
        self.back_btn.setToolTip("Back")
        self.back_btn.clicked.connect(self.go_back)
        nav_layout.addWidget(self.back_btn)

        # Forward button
        self.forward_btn = BauhausButton(BauhausSVG.forward(), size=44)
        self.forward_btn.setToolTip("Forward")
        self.forward_btn.clicked.connect(self.go_forward)
        nav_layout.addWidget(self.forward_btn)

        # Refresh button
        self.refresh_btn = BauhausButton(BauhausSVG.refresh(), size=44)
        self.refresh_btn.setToolTip("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_page)
        nav_layout.addWidget(self.refresh_btn)

        toolbar_layout.addWidget(nav_widget)

        # URL bar
        self.url_input = BauhausURLBar()
        self.url_input.returnPressed.connect(self.load_url)
        toolbar_layout.addWidget(self.url_input)

        # Action buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        # Voice search
        self.voice_btn = BauhausButton(BauhausSVG.voice_search(), size=44)
        self.voice_btn.setToolTip("Voice Search")
        self.voice_btn.clicked.connect(self.voice_search)
        actions_layout.addWidget(self.voice_btn)

        # Search button
        search_btn = BauhausButton(BauhausSVG.search(), size=44)
        search_btn.setToolTip("Search")
        search_btn.clicked.connect(self.load_url)
        actions_layout.addWidget(search_btn)

        # Zoom controls
        zoom_in_btn = BauhausButton(BauhausSVG.zoom_in(), size=44)
        zoom_in_btn.setToolTip("Zoom In")
        zoom_in_btn.clicked.connect(self.zoom_in)
        actions_layout.addWidget(zoom_in_btn)

        zoom_out_btn = BauhausButton(BauhausSVG.zoom_out(), size=44)
        zoom_out_btn.setToolTip("Zoom Out")
        zoom_out_btn.clicked.connect(self.zoom_out)
        actions_layout.addWidget(zoom_out_btn)

        # Fullscreen
        fullscreen_btn = BauhausButton(BauhausSVG.fullscreen(), size=44)
        fullscreen_btn.setToolTip("Fullscreen")
        fullscreen_btn.clicked.connect(self.toggle_full_screen)
        actions_layout.addWidget(fullscreen_btn)

        # Screenshot
        screenshot_btn = BauhausButton(BauhausSVG.screenshot(), size=44)
        screenshot_btn.setToolTip("Screenshot")
        screenshot_btn.clicked.connect(self.take_screenshot)
        actions_layout.addWidget(screenshot_btn)

        # Dev tools
        dev_btn = BauhausButton(BauhausSVG.dev_tools(), size=44)
        dev_btn.setToolTip("Developer Tools")
        dev_btn.clicked.connect(self.open_dev_tools)
        actions_layout.addWidget(dev_btn)

        # AI Agent button in toolbar (prominent)
        ai_btn = BauhausButton(BauhausSVG.ai_agent(), size=44)
        ai_btn.setToolTip("AI Agent - Let AI browse for you")
        ai_btn.clicked.connect(self.show_ai_agent)
        ai_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BauhausColors.YELLOW};
                border: 2px solid {BauhausColors.BLUE};
                border-radius: 22px;
            }}
            QPushButton:hover {{
                background-color: {BauhausColors.RED};
                border-color: {BauhausColors.RED};
            }}
        """)
        actions_layout.addWidget(ai_btn)

        # Menu
        menu_btn = BauhausButton(BauhausSVG.menu(), size=44)
        menu_btn.setToolTip("Menu")
        menu_btn.clicked.connect(self.show_menu)
        actions_layout.addWidget(menu_btn)

        toolbar_layout.addWidget(actions_widget)

        parent_layout.addWidget(toolbar)

    def setup_status_bar(self, parent_layout):
        """Setup bottom status bar"""
        status_bar = QWidget()
        status_bar.setFixedHeight(32)
        status_bar.setStyleSheet(f"""
            background-color: {BauhausColors.BLUE};
        """)

        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(16, 4, 16, 4)

        # VPN indicator
        self.vpn_indicator = BauhausStatusIndicator(BauhausColors.RED, 10)
        status_layout.addWidget(self.vpn_indicator)

        vpn_label = QLabel("VPN")
        vpn_label.setStyleSheet(f"""
            color: {BauhausColors.WHITE};
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        status_layout.addWidget(vpn_label)

        status_layout.addSpacing(16)

        # Ad block indicator
        self.ad_block_indicator = BauhausStatusIndicator(BauhausColors.YELLOW, 10)
        status_layout.addWidget(self.ad_block_indicator)

        ad_label = QLabel("AD BLOCK")
        ad_label.setStyleSheet(f"""
            color: {BauhausColors.WHITE};
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        status_layout.addWidget(ad_label)

        status_layout.addStretch()

        # Status text
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"""
            color: {BauhausColors.WHITE};
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 11px;
        """)
        status_layout.addWidget(self.status_label)

        # Bauhaus geometric accent
        for color in [BauhausColors.RED, BauhausColors.YELLOW, BauhausColors.WHITE]:
            accent = QLabel()
            accent.setFixedSize(8, 8)
            accent.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            status_layout.addWidget(accent)

        parent_layout.addWidget(status_bar)

    def apply_theme(self):
        """Apply light or dark theme"""
        if self.dark_mode:
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {BauhausColors.DARK_BG};
                }}
                QWidget {{
                    color: {BauhausColors.WHITE};
                }}
            """)
            self.sidebar.setStyleSheet(f"""
                BauhausSidebar {{
                    background-color: #0A1425;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {BauhausColors.WHITE};
                }}
            """)
            self.sidebar.setStyleSheet(f"""
                BauhausSidebar {{
                    background-color: {BauhausColors.BLUE};
                }}
            """)

    def current_web_view(self):
        return self.tab_widget.currentWidget()

    def add_new_tab(self, url=None):
        if url is None:
            url = QUrl("https://duckduckgo.com/")
        elif isinstance(url, str):
            url = QUrl(url)
        elif isinstance(url, bool):  # Handle signal with bool parameter
            url = QUrl("https://duckduckgo.com/")
        elif not isinstance(url, QUrl):
            url = QUrl("https://duckduckgo.com/")

        web_view = WebView(self)
        web_view.setPage(QWebEnginePage(self.web_profile, web_view))
        web_view.load(url)
        web_view.loadFinished.connect(lambda ok, view=web_view: self.on_load_finished(ok, view))
        web_view.loadStarted.connect(lambda: self.status_label.setText("Loading..."))
        web_view.loadFinished.connect(lambda: self.status_label.setText("Ready"))
        web_view.titleChanged.connect(lambda title, view=web_view: self.update_tab_title(view, title))

        # Apply VPN settings if enabled
        if self.vpn_enabled:
            proxy_factory = CustomProxyFactory(self.proxy)
            web_view.page().profile().setProxyFactory(proxy_factory)

        # Create tab icon
        tab_icon = svg_to_icon(BauhausSVG.new_tab(), 16)
        index = self.tab_widget.addTab(web_view, tab_icon, "New Tab")
        self.tab_widget.setCurrentIndex(index)

        # Configure web view settings
        settings = web_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.AllowGeolocationOnInsecureOrigins, True)

        return web_view

    def update_tab_title(self, view, title):
        index = self.tab_widget.indexOf(view)
        if index >= 0:
            # Truncate title if too long
            display_title = title[:25] + "..." if len(title) > 25 else title
            self.tab_widget.setTabText(index, display_title)

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
        else:
            self.close()

    def load_url(self):
        query = self.url_input.text()
        if not query.startswith(('http://', 'https://')):
            if '.' in query and ' ' not in query:
                query = 'https://' + query
            else:
                query = f'https://duckduckgo.com/?q={urllib.parse.quote_plus(query)}'

        current_view = self.current_web_view()
        if current_view:
            current_view.setUrl(QUrl(query))

    def update_url_bar(self):
        current_view = self.current_web_view()
        if current_view:
            self.url_input.setText(current_view.url().toString())

    def go_back(self):
        current_view = self.current_web_view()
        if current_view:
            current_view.back()

    def go_forward(self):
        current_view = self.current_web_view()
        if current_view:
            current_view.forward()

    def refresh_page(self):
        current_view = self.current_web_view()
        if current_view:
            current_view.reload()

    def go_home(self):
        current_view = self.current_web_view()
        if current_view:
            current_view.setUrl(QUrl("https://duckduckgo.com/"))

    def voice_search(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                self.speak("Listening... How can I help you?")
                self.status_label.setText("Listening...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                self.status_label.setText("Processing...")

            try:
                query = recognizer.recognize_google(audio)
                print(f"You said: {query}")
                self.process_voice_command(query)
            except sr.UnknownValueError:
                self.speak("I'm sorry, I couldn't understand that. Please try again.")
                self.status_label.setText("Ready")
            except sr.RequestError as e:
                self.speak("I'm having trouble connecting to the speech recognition service.")
                self.status_label.setText("Ready")
        except Exception as e:
            self.speak("An error occurred. Please try again.")
            self.status_label.setText("Ready")
            print(f"An error occurred: {e}")

    def process_voice_command(self, query):
        query_lower = query.lower()
        if "search for" in query_lower:
            search_term = query.replace("search for", "").strip()
            self.speak(f"Searching for {search_term}")
            self.perform_search(search_term)
        elif "open" in query_lower:
            website = query.replace("open", "").strip()
            self.speak(f"Opening {website}")
            self.open_website(website)
        elif "play" in query_lower:
            video = query.replace("play", "").strip()
            self.speak(f"Playing {video} on YouTube")
            self.search_and_play_youtube(video)
        elif "what's the time" in query_lower or "what is the time" in query_lower:
            current_time = QtCore.QTime.currentTime().toString("hh:mm AP")
            self.speak(f"The current time is {current_time}")
        elif "close tab" in query_lower:
            self.speak("Closing the current tab")
            self.close_current_tab()
        elif "new tab" in query_lower:
            self.speak("Opening a new tab")
            self.add_new_tab()
        elif "dark mode" in query_lower:
            self.speak("Toggling dark mode")
            self.toggle_dark_mode()
        elif "vpn" in query_lower:
            self.speak("Toggling VPN")
            self.toggle_vpn()
        else:
            self.speak("Performing a web search for your query")
            self.perform_search(query)
        self.status_label.setText("Ready")

    def speak(self, text):
        try:
            subprocess.run(["say", text], check=False)
        except:
            print(f"Speech: {text}")

    def open_website(self, website):
        if not website.startswith('http'):
            website = 'https://' + website
        self.add_new_tab(website)

    def close_current_tab(self):
        current_index = self.tab_widget.currentIndex()
        self.close_tab(current_index)

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
        self.apply_theme()

        # Update button icon
        if self.dark_mode:
            self.dark_mode_btn.setIcon(svg_to_icon(BauhausSVG.light_mode(), 36))
        else:
            self.dark_mode_btn.setIcon(svg_to_icon(BauhausSVG.dark_mode(), 36))

        # Apply dark mode to all web views
        for i in range(self.tab_widget.count()):
            web_view = self.tab_widget.widget(i)
            self.apply_dark_mode_to_web_view(web_view)

    def apply_dark_mode_to_web_view(self, web_view):
        js = f"""
        (function() {{
            function applyDarkMode(node) {{
                if (node.nodeType === Node.ELEMENT_NODE) {{
                    node.style.setProperty('background-color', '{("#181818" if self.dark_mode else "")}', 'important');
                    node.style.setProperty('color', '{("#FFFFFF" if self.dark_mode else "")}', 'important');

                    if (node.tagName === 'A') {{
                        node.style.setProperty('color', '{("#3EA6FF" if self.dark_mode else "")}', 'important');
                    }}
                }}

                for (let child of node.childNodes) {{
                    applyDarkMode(child);
                }}
            }}

            document.documentElement.style.colorScheme = '{("dark" if self.dark_mode else "light")}';
            if ({'true' if self.dark_mode else 'false'}) {{
                applyDarkMode(document.body);
            }} else {{
                location.reload();
            }}
        }})();
        """
        web_view.page().runJavaScript(js)

    def toggle_vpn(self):
        self.vpn_enabled = not self.vpn_enabled
        if self.vpn_enabled:
            self.enable_vpn()
        else:
            self.disable_vpn()

    def enable_vpn(self):
        self.proxy.setType(QNetworkProxy.HttpProxy)
        self.proxy.setHostName("203.30.189.169")
        self.proxy.setPort(80)

        proxy_factory = CustomProxyFactory(self.proxy)
        QNetworkProxyFactory.setApplicationProxyFactory(proxy_factory)

        for i in range(self.tab_widget.count()):
            web_view = self.tab_widget.widget(i)
            web_view.page().profile().setProxyFactory(proxy_factory)

        self.vpn_btn.setIcon(svg_to_icon(BauhausSVG.vpn_on(), 36))
        self.vpn_indicator.set_color(BauhausColors.YELLOW)
        self.status_label.setText("VPN Enabled")
        print("VPN enabled")

    def disable_vpn(self):
        QNetworkProxyFactory.setUseSystemConfiguration(True)

        for i in range(self.tab_widget.count()):
            web_view = self.tab_widget.widget(i)
            web_view.page().profile().setProxyFactory(None)

        self.vpn_btn.setIcon(svg_to_icon(BauhausSVG.vpn_off(), 36))
        self.vpn_indicator.set_color(BauhausColors.RED)
        self.status_label.setText("VPN Disabled")
        print("VPN disabled")

    def toggle_ad_block(self):
        self.ad_block_enabled = not self.ad_block_enabled
        if self.ad_block_enabled:
            self.ad_block_btn.setIcon(svg_to_icon(BauhausSVG.ad_block_on(), 36))
            self.ad_block_indicator.set_color(BauhausColors.YELLOW)
            self.status_label.setText("Ad Blocker Enabled")
        else:
            self.ad_block_btn.setIcon(svg_to_icon(BauhausSVG.ad_block_off(), 36))
            self.ad_block_indicator.set_color(BauhausColors.RED)
            self.status_label.setText("Ad Blocker Disabled")

    def load_adblock_rules(self):
        try:
            easylist_url = "https://easylist.to/easylist/easylist.txt"
            response = requests.get(easylist_url, timeout=10)
            rules = AdblockRules(response.text.splitlines())

            self.web_profile = QWebEngineProfile("AdBlockProfile", self)
            self.web_profile.setUrlRequestInterceptor(AdBlockInterceptor(rules))

            # Configure profile settings
            self.web_profile.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            self.web_profile.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
            self.web_profile.settings().setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
            self.web_profile.settings().setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
            self.web_profile.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
            self.web_profile.settings().setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
            self.web_profile.settings().setAttribute(QWebEngineSettings.AllowGeolocationOnInsecureOrigins, True)
        except Exception as e:
            print(f"Failed to load ad block rules: {e}")
            self.web_profile = QWebEngineProfile.defaultProfile()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_D and event.modifiers() == Qt.ShiftModifier:
            self.show_spotlight_search()
        elif event.key() == Qt.Key_A and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self.show_ai_agent()  # Ctrl+Shift+A for AI Agent
        elif event.key() == Qt.Key_T and event.modifiers() == Qt.ControlModifier:
            self.add_new_tab()
        elif event.key() == Qt.Key_W and event.modifiers() == Qt.ControlModifier:
            self.close_current_tab()
        elif event.key() == Qt.Key_L and event.modifiers() == Qt.ControlModifier:
            self.url_input.setFocus()
            self.url_input.selectAll()
        elif event.key() == Qt.Key_R and event.modifiers() == Qt.ControlModifier:
            self.refresh_page()
        elif event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            self.show_find_dialog()
        else:
            super().keyPressEvent(event)

    def show_spotlight_search(self):
        screen_geometry = QtWidgets.QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.spotlight_search.width()) // 2
        y = (screen_geometry.height() - self.spotlight_search.height()) // 2
        self.spotlight_search.move(x, y)

        self.spotlight_search.search_input.clear()
        self.spotlight_search.results_list.clear()
        self.spotlight_search.show()

        QTimer.singleShot(100, self.spotlight_search.search_input.setFocus)

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
                .custom-fullscreen-button {
                    position: absolute;
                    bottom: 60px;
                    right: 12px;
                    width: 40px;
                    height: 40px;
                    background-color: #E63946;
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    cursor: pointer;
                    z-index: 1000;
                    border-radius: 8px;
                    font-size: 20px;
                    font-weight: bold;
                }
                .custom-fullscreen-button:hover {
                    background-color: #F4D35E;
                    color: #1D3557;
                }
            `;
            document.head.appendChild(style);

            var button = document.createElement('div');
            button.className = 'custom-fullscreen-button';
            button.innerHTML = '⛶';
            button.title = 'Fullscreen';
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
                }
            });

            observer.observe(document.body, { childList: true, subtree: true });
        })();
        """)

    def show_bookmarks(self):
        self.add_new_tab("chrome://bookmarks")

    def show_history(self):
        self.add_new_tab("chrome://history")

    def show_downloads(self):
        self.add_new_tab("chrome://downloads")

    def show_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec_()

    def show_ai_agent(self):
        """Show the AI Agent dialog"""
        ai_dialog = AIAgentDialog(self)
        ai_dialog.exec_()

    def take_screenshot(self):
        current_view = self.current_web_view()
        if current_view:
            pixmap = current_view.grab()
            timestamp = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
            filename = f"screenshot_{timestamp}.png"
            pixmap.save(filename)
            self.status_label.setText(f"Screenshot saved: {filename}")

    def open_dev_tools(self):
        current_view = self.current_web_view()
        if current_view:
            # Open developer tools in a new window
            current_view.page().setDevToolsPage(QWebEnginePage(self.web_profile))
            dev_view = WebView()
            dev_view.setPage(current_view.page().devToolsPage())
            dev_view.setWindowTitle("Developer Tools - Comet Browser")
            dev_view.resize(1000, 600)
            dev_view.show()

    def show_find_dialog(self):
        current_view = self.current_web_view()
        if current_view:
            text, ok = QtWidgets.QInputDialog.getText(self, "Find", "Search for:")
            if ok and text:
                current_view.findText(text)

    def show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {BauhausColors.WHITE};
                border: 3px solid {BauhausColors.BLUE};
                border-radius: 8px;
                padding: 8px;
            }}
            QMenu::item {{
                padding: 10px 20px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
                color: {BauhausColors.BLACK};
            }}
            QMenu::item:selected {{
                background-color: {BauhausColors.YELLOW};
                color: {BauhausColors.BLACK};
            }}
            QMenu::separator {{
                height: 2px;
                background-color: {BauhausColors.BLUE};
                margin: 8px 0;
            }}
        """)

        # Add menu items
        menu.addAction("New Tab (Ctrl+T)", self.add_new_tab)
        menu.addAction("New Window", lambda: None)  # Placeholder
        menu.addAction("New Incognito Window", lambda: None)  # Placeholder
        menu.addSeparator()
        menu.addAction("History (Ctrl+H)", self.show_history)
        menu.addAction("Downloads (Ctrl+J)", self.show_downloads)
        menu.addAction("Bookmarks (Ctrl+B)", self.show_bookmarks)
        menu.addSeparator()
        menu.addAction("Zoom In (Ctrl++)", self.zoom_in)
        menu.addAction("Zoom Out (Ctrl+-)", self.zoom_out)
        menu.addAction("Fullscreen (F11)", self.toggle_full_screen)
        menu.addSeparator()
        menu.addAction("Find (Ctrl+F)", self.show_find_dialog)
        menu.addAction("Print", self.print_page)
        menu.addAction("Screenshot", self.take_screenshot)
        menu.addSeparator()
        menu.addAction("Developer Tools (F12)", self.open_dev_tools)
        menu.addAction("Settings", self.show_settings)
        menu.addSeparator()
        menu.addAction("🤖 AI Agent - Browse for You", self.show_ai_agent)
        menu.addSeparator()
        menu.addAction("About Comet Browser", self.show_about)
        menu.addAction("Quit (Ctrl+Q)", self.close)

        # Position menu
        menu.exec_(QtWidgets.QCursor.pos())

    def print_page(self):
        current_view = self.current_web_view()
        if current_view:
            # Print functionality
            from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                current_view.page().print(printer, lambda success: print(f"Print {'succeeded' if success else 'failed'}"))

    def show_about(self):
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About Comet Browser")
        about_dialog.setFixedSize(400, 300)

        layout = QVBoxLayout(about_dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Logo area with Bauhaus design
        logo_widget = QWidget()
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(8)

        for color in [BauhausColors.RED, BauhausColors.YELLOW, BauhausColors.BLUE]:
            shape = QLabel()
            shape.setFixedSize(40, 40)
            shape.setStyleSheet(f"background-color: {color}; border-radius: {20 if color == BauhausColors.RED else 4}px;")
            logo_layout.addWidget(shape)

        logo_layout.addStretch()
        layout.addWidget(logo_widget)

        title = QLabel("COMET BROWSER")
        title.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 4px;
            color: {BauhausColors.BLUE};
        """)
        layout.addWidget(title)

        version = QLabel("Version 2.0 - Bauhaus Edition")
        version.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            color: {BauhausColors.ACCENT};
        """)
        layout.addWidget(version)

        description = QLabel("A modern web browser with Bauhaus-inspired design.\nBuilt with PyQt5 and love for geometric aesthetics.")
        description.setStyleSheet(f"""
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 13px;
            color: {BauhausColors.BLACK};
            line-height: 1.5;
        """)
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addStretch()

        close_btn = QPushButton("CLOSE")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BauhausColors.BLUE};
                color: {BauhausColors.WHITE};
                border: none;
                border-radius: 8px;
                padding: 12px 32px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background-color: {BauhausColors.RED};
            }}
        """)
        close_btn.clicked.connect(about_dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        about_dialog.setStyleSheet(f"background-color: {BauhausColors.WHITE};")
        about_dialog.exec_()


# ============================================================================
# NETWORK ERROR HANDLER
# ============================================================================

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
    elif error != QNetworkReply.NoError:
        print(f"Network error occurred: {reply.errorString()}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setApplicationName("Comet Browser")
    app.setOrganizationName("Comet")

    # Set application-wide font
    font = QFont("Helvetica Neue", 12)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)

    # Set up global network access manager
    network_manager = QNetworkAccessManager()
    network_manager.finished.connect(handle_network_error)

    browser = BrowserApp()
    browser.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
