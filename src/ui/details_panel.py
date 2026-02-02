import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, 
                             QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
from src.scanner import FileNode
import send2trash

class DetailsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.node = None
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Title / Filename
        self.lbl_name = QLabel("Select a file")
        self.lbl_name.setWordWrap(True)
        self.lbl_name.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        self.layout.addWidget(self.lbl_name)

        # Path
        self.lbl_path = QLabel("")
        self.lbl_path.setWordWrap(True)
        self.lbl_path.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        self.layout.addWidget(self.lbl_path)

        # Size
        self.lbl_size = QLabel("")
        self.lbl_size.setStyleSheet("font-size: 16px; font-weight: bold; color: #0078D4;")
        self.layout.addWidget(self.lbl_size)
        
        # Category Badge
        self.lbl_category = QLabel("")
        self.lbl_category.setStyleSheet("""
            background-color: #333; 
            color: #DDD; 
            padding: 4px 8px; 
            border-radius: 4px;
            font-size: 12px;
        """)
        self.lbl_category.hide()
        self.layout.addWidget(self.lbl_category)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #444;")
        self.layout.addWidget(line)

        # Analysis Text
        self.lbl_analysis = QLabel("")
        self.lbl_analysis.setWordWrap(True)
        self.lbl_analysis.setStyleSheet("font-size: 13px; color: #DDD;")
        self.layout.addWidget(self.lbl_analysis)

        self.layout.addStretch()

        # Actions
        self.btn_open = QPushButton("Open in Explorer")
        self.btn_open.clicked.connect(self.open_in_explorer)
        self.style_button(self.btn_open, "#333", "#EEE")
        self.layout.addWidget(self.btn_open)

        self.btn_delete = QPushButton("Delete to Recycle Bin")
        self.btn_delete.clicked.connect(self.delete_file)
        self.style_button(self.btn_delete, "#D13438", "white") # Red
        self.layout.addWidget(self.btn_delete)
        
        # Hide actions initially
        self.btn_open.hide()
        self.btn_delete.hide()

    def style_button(self, btn, bg, text_color):
        btn.setFixedHeight(36)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {text_color};
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {bg}AA; /* Slight opacity change */
            }}
        """)

    def update_selection(self, node: FileNode):
        self.node = node
        self.lbl_name.setText(node.name)
        self.lbl_path.setText(node.path)
        self.lbl_size.setText(self.format_size(node.size))
        
        self.lbl_category.setText(node.category)
        self.lbl_category.show()
        
        # Analysis Logic
        if node.category == "Cache":
            self.lbl_analysis.setText(
                "This appears to be temporary cache data. "
                "It is usually safe to delete and will regenerate if needed."
            )
            self.btn_delete.setText("Safe Cleanup (Recycle Bin)")
            self.btn_delete.setStyleSheet(self.btn_delete.styleSheet().replace("#D13438", "#107C10")) # Green for safe
        elif node.category == "System":
            self.lbl_analysis.setText(
                "These are system files. Deleting them may crash your computer. "
                "<b>Do not delete unless you know what you are doing.</b>"
            )
            self.btn_delete.setText("Delete (Caution)")
            self.btn_delete.setStyleSheet(self.btn_delete.styleSheet().replace("#107C10", "#D13438")) # Red
        else:
            self.lbl_analysis.setText(f"This is a {node.category} item.")
            self.btn_delete.setText("Delete to Recycle Bin")
            self.btn_delete.setStyleSheet(self.btn_delete.styleSheet().replace("#107C10", "#D13438"))

        self.btn_open.show()
        self.btn_delete.show()

    def open_in_explorer(self):
        if self.node:
            folder_path = self.node.path if self.node.is_dir else os.path.dirname(self.node.path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))

    def delete_file(self):
        if not self.node:
            return
            
        confirm = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to move '{self.node.name}' to the Recycle Bin?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                send2trash.send2trash(self.node.path)
                QMessageBox.information(self, "Deleted", "Item moved to Recycle Bin.")
                # TODO: Trigger refresh or remove from tree
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete: {str(e)}")

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"
