"""
全局样式常量
"""

COLORS = {
    "bg": "#1e1e2e",
    "surface": "#2a2a3e",
    "surface_hover": "#353550",
    "border": "#3a3a5a",
    "text": "#e0e0e0",
    "text_dim": "#888899",
    "accent": "#7c8aff",
    "accent_dim": "#5a65cc",
    "success": "#4caf88",
    "error": "#e05555",
    "warning": "#e0a040",
    "progress_bg": "#3a3a5a",
}

AGENT_COLORS = {
    "manager_plan": "#7c8aff",
    "analyst": "#4fc3f7",
    "report_reader": "#ab47bc",
    "deep_diver": "#ff7043",
    "horizontal_scanner": "#66bb6a",
    "tech_scout": "#ffa726",
    "debater": "#ef5350",
    "stock_advisor": "#26c6da",
    "gatekeeper": "#78909c",
    "manager_review": "#7c8aff",
    "manager_post_debate": "#7c8aff",
    "manager_final": "#7c8aff",
}

FONT_FAMILY = "PingFang SC, Helvetica Neue, Arial, sans-serif"

MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg']};
}}
QWidget {{
    font-family: {FONT_FAMILY};
    color: {COLORS['text']};
}}
QLineEdit {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    color: {COLORS['text']};
}}
QLineEdit:focus {{
    border-color: {COLORS['accent']};
}}
QPushButton {{
    background-color: {COLORS['accent']};
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: bold;
    color: white;
}}
QPushButton:hover {{
    background-color: {COLORS['accent_dim']};
}}
QPushButton:disabled {{
    background-color: {COLORS['border']};
    color: {COLORS['text_dim']};
}}
QProgressBar {{
    background-color: {COLORS['progress_bg']};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 4px;
}}
QTextEdit, QTextBrowser {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
    color: {COLORS['text']};
}}
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    background-color: {COLORS['surface']};
}}
QTabBar::tab {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    padding: 6px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: {COLORS['text_dim']};
}}
QTabBar::tab:selected {{
    background-color: {COLORS['bg']};
    color: {COLORS['accent']};
    border-bottom: none;
}}
QScrollBar:vertical {{
    background: {COLORS['bg']};
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 4px;
    min-height: 20px;
}}
"""
