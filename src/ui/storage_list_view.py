from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QFrame, QPushButton, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QPalette, QIcon, QCursor
from src.scanner import FileNode
import os

class StorageListItem(QFrame):
    def __init__(self, node: FileNode, max_size: int, parent=None):
        super().__init__(parent)
        self.node = node
        self.max_size = max_size
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("StorageListItem")
        
        # Style
        self.setStyleSheet("""
            #StorageListItem {
                background-color: #2D2D2D;
                border-radius: 6px;
                border: 1px solid #3D3D3D;
            }
            #StorageListItem:hover {
                background-color: #383838;
                border: 1px solid #505050;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # 1. Icon (Emoji for now, can be real icons later)
        icon_label = QLabel("📁" if node.is_dir else "📄")
        icon_label.setStyleSheet("font-size: 24px; background: transparent;")
        layout.addWidget(icon_label)
        
        # 2. Name & Progress Bar Container
        center_layout = QVBoxLayout()
        center_layout.setSpacing(5)
        
        # Name Row
        name_label = QLabel(node.name)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white; background: transparent;")
        center_layout.addWidget(name_label)
        
        # Progress Bar
        progress = QProgressBar()
        progress.setFixedHeight(6)
        progress.setTextVisible(False)
        
        if max_size > 0:
            percentage = int((node.size / max_size) * 100)
            progress.setValue(percentage)
        else:
            progress.setValue(0)
            
        # Color based on category (matching main theme or independent)
        color = self.get_category_color(node.category)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1A1A1A;
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        center_layout.addWidget(progress)
        
        layout.addLayout(center_layout, 1) # Stretch to fill
        
        # 3. Size Info
        size_layout = QVBoxLayout()
        size_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        size_text = self.format_size(node.size)
        size_label = QLabel(size_text)
        size_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #EEE; background: transparent;")
        size_layout.addWidget(size_label)
        
        if max_size > 0:
            percent_val = (node.size / max_size) * 100
            percent_label = QLabel(f"{percent_val:.1f}%")
            percent_label.setStyleSheet("font-size: 12px; color: #AAA; background: transparent;")
            percent_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            size_layout.addWidget(percent_label)
            
        layout.addLayout(size_layout)

    def get_category_color(self, category):
        colors = {
            "Apps": "#0078D4",      # Blue
            "Cache": "#D13438",     # Red
            "Media": "#B146C2",     # Purple
            "Development": "#00CC6A", # Green
            "Archives": "#FFB900",    # Yellow
            "System": "#737373",      # Grey
            "Unknown": "#606060"      # Dark Grey
        }
        return colors.get(category, "#606060")

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"


class StorageListView(QWidget):
    itemClicked = pyqtSignal(object) # Emits FileNode

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_node = None
        self.current_view_node = None # The folder currently displayed
        self.breadcrumbs = [] # List of nodes from root to current
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 1. Breadcrumb Bar
        self.breadcrumb_bar = QWidget()
        self.breadcrumb_bar.setStyleSheet("background-color: #252525; border-bottom: 1px solid #3D3D3D;")
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_bar)
        self.breadcrumb_layout.setContentsMargins(15, 10, 15, 10)
        self.breadcrumb_layout.setSpacing(5)
        self.breadcrumb_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.layout.addWidget(self.breadcrumb_bar)
        
        # 2. Scroll Area for List
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #202020; border: none;")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(20, 20, 20, 20)
        self.list_layout.setSpacing(10)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.list_container)
        self.layout.addWidget(self.scroll_area)

    def set_data(self, root_node: FileNode):
        self.root_node = root_node
        self.breadcrumbs = [root_node]
        self.navigate_to(root_node)

    def navigate_to(self, node: FileNode):
        self.current_view_node = node
        self.update_breadcrumbs()
        self.render_list()

    def update_breadcrumbs(self):
        # Clear existing
        for i in reversed(range(self.breadcrumb_layout.count())): 
            self.breadcrumb_layout.itemAt(i).widget().setParent(None)
            
        # Rebuild breadcrumb path based on parent references (if available) or internal tracking
        # Since node.parent is linked, we can trace back or just use our tracked list.
        # Let's use our tracked list for valid state management
        
        # For this simplified version, let's assume we clicked down.
        # But if we jump back, we need to correct the list.
        # Actually `navigate_to` is just render. We need `enter_folder` and `go_up` logic.
        
        # Simple Breadcrumb rendering:
        # Root > Subfolder > Subfolder
        
        for i, node in enumerate(self.breadcrumbs):
            btn = QPushButton(node.name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Style differently if it's the last one (current)
            if i == len(self.breadcrumbs) - 1:
                btn.setStyleSheet("""
                    border: none; 
                    color: white; 
                    font-weight: bold; 
                    font-size: 14px; 
                    background: transparent;
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        border: none; 
                        color: #AAAAAA; 
                        font-size: 14px; 
                        background: transparent; 
                    }
                    QPushButton:hover { text-decoration: underline; color: #FFF; }
                """)
            
            # Connect click
            # We need to capture the state at this index
            btn.clicked.connect(lambda checked, idx=i: self.on_breadcrumb_clicked(idx))
            
            self.breadcrumb_layout.addWidget(btn)
            
            # Add separator if not last
            if i < len(self.breadcrumbs) - 1:
                sep = QLabel(">")
                sep.setStyleSheet("color: #666; font-size: 14px;")
                self.breadcrumb_layout.addWidget(sep)
    
    def on_breadcrumb_clicked(self, index):
        # Truncate breadcrumbs up to this index
        target_node = self.breadcrumbs[index]
        self.breadcrumbs = self.breadcrumbs[:index+1]
        self.navigate_to(target_node)

    def render_list(self):
        # Clear existing list
        for i in reversed(range(self.list_layout.count())): 
            widget = self.list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                
        if not self.current_view_node:
            return
            
        # Sort children by size (descending)
        children = sorted(self.current_view_node.children, key=lambda x: x.size, reverse=True)
        
        # If empty
        if not children:
            lbl = QLabel("This folder is empty.")
            lbl.setStyleSheet("color: #777; font-size: 16px; margin-top: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.addWidget(lbl)
            return

        # Largest child size for relative bars
        max_size = children[0].size if children else 1
        
        for child in children:
            item = StorageListItem(child, max_size)
            # Custom click handling with mouseRelease or installing event filter
            # Simpler: Make the whole frame clickable by overriding mousePress in StorageListItem
            # But here we need to know what to do (enter dir or signal file)
            # We will use a transparent button overlay or just mousePressEvent in the Item class.
            
            # Let's attach a callback to the item instance? 
            # Or subclassing QFrame in StorageListItem enables mousePressEvent. 
            # We can connect a signal from the item if we added one, 
            # or just assign a function to an attribute.
            item.mousePressEvent = lambda event, n=child: self.on_item_clicked(n)
            
            self.list_layout.addWidget(item)

    def on_item_clicked(self, node: FileNode):
        if node.is_dir:
            # Enter directory
            self.breadcrumbs.append(node)
            self.navigate_to(node)
        else:
            # Is a file, emit signal for Details Panel
            self.itemClicked.emit(node)
