import os
import send2trash
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
                             QPushButton, QLabel, QMessageBox, QHBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QIcon

class RecommendationView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.lbl_header = QLabel("Smart Cleanup Recommendations")
        self.lbl_header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(self.lbl_header)

        # Explanation
        lbl_info = QLabel("Review items below. Checked items will be moved to the Recycle Bin.")
        lbl_info.setStyleSheet("color: #AAAAAA; margin-bottom: 5px;")
        self.layout.addWidget(lbl_info)

        # Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Item", "Reason", "Size", "Path"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 100)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #252525;
                border: 1px solid #3D3D3D;
            }
            QTreeWidget::item {
                padding: 5px;
            }
        """)
        self.layout.addWidget(self.tree)

        # Action Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setEnabled(False) # Only enabled if we have logic to re-run analysis
        
        self.btn_delete = QPushButton("Move Selected to Recycle Bin")
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #e03131; 
                color: white; 
                font-weight: bold; 
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #fa5252; }
        """)
        self.btn_delete.clicked.connect(self.delete_selected)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_delete)
        
        self.layout.addLayout(btn_layout)

    def set_data(self, suggestions, duplicates):
        self.tree.clear()
        
        # 1. Add Suggestions
        for category, nodes in suggestions.items():
            if not nodes:
                continue
                
            cat_item = QTreeWidgetItem(self.tree)
            cat_item.setText(0, category)
            cat_item.setExpanded(True)
            cat_item.setForeground(0, QBrush(QColor("#4DABF7"))) # Blueish header
            
            for node in nodes:
                item = QTreeWidgetItem(cat_item)
                item.setText(0, node.name)
                item.setText(1, category)
                item.setText(2, self.format_size(node.size))
                item.setText(3, node.path)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Unchecked)
                # Store full path in data
                item.setData(0, Qt.ItemDataRole.UserRole, node.path)

        # 2. Add Duplicates
        if duplicates:
            dup_root = QTreeWidgetItem(self.tree)
            dup_root.setText(0, "Duplicate Files")
            dup_root.setExpanded(True)
            dup_root.setForeground(0, QBrush(QColor("#FF922B"))) # Orange header
            
            for group in duplicates:
                group_item = QTreeWidgetItem(dup_root)
                # Using size for group item
                size_str = self.format_size(group[0].size)
                group_item.setText(0, f"Duplicate Group ({len(group)} files)")
                group_item.setText(2, size_str)
                group_item.setExpanded(True)
                
                # Mark all as unchecked by default
                for node in group:
                    item = QTreeWidgetItem(group_item)
                    item.setText(0, node.name)
                    item.setText(1, "Exact Duplicate")
                    item.setText(2, size_str)
                    item.setText(3, node.path)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(0, Qt.CheckState.Unchecked)
                    item.setData(0, Qt.ItemDataRole.UserRole, node.path)

    def delete_selected(self):
        # Gather items
        items_to_delete = []
        
        iterator = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.IteratorFlag.Checked)
        while iterator.value():
            item = iterator.value()
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path:
                items_to_delete.append((item, path))
            iterator += 1
            
        if not items_to_delete:
            QMessageBox.information(self, "No Selection", "Please check items to remove.")
            return

        # Confirm
        count = len(items_to_delete)
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     f"Are you sure you want to move {count} items to the Recycle Bin?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            success_count = 0
            errors = []
            
            for item, path in items_to_delete:
                try:
                    send2trash.send2trash(path)
                    # Remove from tree
                    parent = item.parent()
                    if parent:
                        parent.removeChild(item)
                    else:
                        # Should not happen for leaf nodes in our structure
                        pass
                    success_count += 1
                except Exception as e:
                    errors.append(f"{os.path.basename(path)}: {str(e)}")
            
            msg = f"Successfully moved {success_count} items to Recycle Bin."
            if errors:
                msg += f"\n\nErrors ({len(errors)}):\n" + "\n".join(errors[:5])
                if len(errors) > 5: msg += "\n..."
                
            QMessageBox.information(self, "Cleanup Result", msg)

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

# Import needed for iterator
from PyQt6.QtWidgets import QTreeWidgetItemIterator
