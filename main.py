import sys
import os
import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStackedWidget, QFileDialog)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette

# Import scanner (Assuming it's ready based on previous step)
from src.scanner import ScanManager, FileNode
from src.history_manager import HistoryManager

from src.ui.treemap_widget import TreemapWidget
from src.ui.storage_list_view import StorageListView
from src.ui.details_panel import DetailsPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Disk Usage Analyzer")
        self.resize(1200, 800)
        self.setup_ui_theme()
        
        # Data
        self.scan_manager = ScanManager()
        self.history_manager = HistoryManager()
        self.current_root = None

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Sidebar (Navigation/Status)
        self.setup_sidebar()

        # 2. Main Content Area (Treemap)
        self.setup_content_area()

        # 3. Detail Panel (Right side)
        self.setup_detail_panel()
        
    def setup_ui_theme(self):
        # Basic Windows 11-ish Dark Mode Palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#202020"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#191919"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#2D2D2D"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#333333"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#FF0000"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#42A5F5"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#0078D4")) # Win11 Blue
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
        self.setPalette(palette)
        
        # Global Font
        font = QFont("Segoe UI", 10)
        self.setFont(font)

    def setup_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #2D2D2D; border-right: 1px solid #3D3D3D;")
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(10, 20, 10, 20)
        
        self.btn_scan = QPushButton("Start Scan")
        self.btn_scan.setFixedHeight(40)
        self.btn_scan.setStyleSheet("""
            QPushButton {
                background-color: #0078D4; 
                color: white; 
                border-radius: 4px; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1084D9; }
        """)
        self.btn_scan.clicked.connect(self.select_folder)
        
        layout.addWidget(self.btn_scan)
        layout.addStretch()
        
        self.main_layout.addWidget(self.sidebar)

    def setup_content_area(self):
        self.content_area = QWidget()
        layout = QVBoxLayout(self.content_area)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header (Overlay or separate?)
        # For simple structure, keep header at top
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(20, 20, 20, 10)
        
        self.header_label = QLabel("Ready to Scan")
        self.header_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.insights_label = QLabel("")
        self.insights_label.setStyleSheet("font-size: 14px; color: #CCCCCC; margin-top: 5px;")
        self.insights_label.setWordWrap(True)
        self.insights_label.hide()

        header_layout.addWidget(self.header_label)
        header_layout.addWidget(self.insights_label)
        layout.addWidget(header_container)
        
        # Stacked Widget to switch between Placeholder and Treemap
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Page 0: Placeholder
        self.page_placeholder = QLabel("Select a folder to begin analysis.")
        self.page_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_placeholder.setStyleSheet("color: #AAAAAA; font-size: 16px;")
        self.stack.addWidget(self.page_placeholder)
        
        # Page 1: Treemap
        # Page 1: Treemap / List View
        self.storage_view = StorageListView()
        self.storage_view.itemClicked.connect(self.on_treemap_clicked)
        self.stack.addWidget(self.storage_view)
        
        self.main_layout.addWidget(self.content_area, 1)

    def setup_detail_panel(self):
        self.detail_panel = DetailsPanel()
        self.detail_panel.setFixedWidth(300)
        self.detail_panel.setStyleSheet("background-color: #252525; border-left: 1px solid #3D3D3D;")
        self.detail_panel.hide()
        self.main_layout.addWidget(self.detail_panel)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.header_label.setText(f"Scanning: {folder}...")
            self.insights_label.hide()
            self.btn_scan.setEnabled(False)
            self.stack.setCurrentIndex(0)
            self.page_placeholder.setText("Scanning... This process utilizes optimized multi-threading.")
            self.scan_manager.start_scan(folder, self.on_scan_finished)

    def on_scan_finished(self, root_node):
        self.current_root = root_node
        self.btn_scan.setEnabled(True)
        self.header_label.setText(f"Scan Complete: {root_node.path}")
        
        # Save History & Get Insights
        self.history_manager.save_scan(root_node.path, root_node)
        insights = self.history_manager.get_insights(root_node.path, root_node)
        
        if insights:
            self.show_insights(insights)
        else:
            self.insights_label.setText("First scan recorded. Insights will appear on future scans.")
            self.insights_label.show()

        # Show Treemap
        self.stack.setCurrentIndex(1)
        self.storage_view.set_data(root_node)

    def show_insights(self, insights):
        diff = insights['size_diff']
        diff_str = self.format_size(abs(diff))
        direction = "increased" if diff > 0 else "decreased"
        color = "#ff6b6b" if diff > 0 else "#51cf66" # Red for increase, Green for decrease
        
        prev_date = datetime.datetime.fromtimestamp(insights['previous_timestamp']).strftime('%Y-%m-%d %H:%M')
        
        msg = f"Storage {direction} by <span style='color:{color}; font-weight:bold'>{diff_str}</span> since {prev_date}."
        
        if insights['top_changes']:
            msg += "<br>Top changes: "
            changes_str = []
            for name, change in insights['top_changes']:
                change_fmt = self.format_size(change)
                sign = "+" if change > 0 else ""
                changes_str.append(f"{name} ({sign}{change_fmt})")
            msg += ", ".join(changes_str)
            
        self.insights_label.setText(msg)
        self.insights_label.show()

    def on_treemap_clicked(self, node):
        self.detail_panel.show()
        self.detail_panel.update_selection(node)

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(size) < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
