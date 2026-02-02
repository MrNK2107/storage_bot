from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsSimpleTextItem
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QPen, QFont, QPainter
from src.scanner import FileNode

class TreemapItem(QGraphicsRectItem):
    def __init__(self, rect, node: FileNode, color: QColor, parent_item=None):
        super().__init__(rect, parent_item)
        self.node = node
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(30,30,30), 1)) # Borders
        self.setAcceptHoverEvents(True)
        
        # Add Label if space permits
        if rect.width() > 60 and rect.height() > 20:
            text = QGraphicsSimpleTextItem(node.name, self)
            font = QFont("Segoe UI", 9)
            text.setFont(font)
            text.setBrush(QBrush(QColor("white")))
            
            # Center text
            text_rect = text.boundingRect()
            text.setPos(rect.x() + 5, rect.y() + 5)
            
            # Clip if too long (basic)
            if text_rect.width() > rect.width() - 10:
                pass # TODO: Elide text

    def hoverEnterEvent(self, event):
        self.setPen(QPen(QColor("white"), 2))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(QPen(QColor(30,30,30), 1))
        super().hoverLeaveEvent(event)

class TreemapWidget(QGraphicsView):
    itemClicked = pyqtSignal(object) # Emits FileNode

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        self.root_node = None
        self.colors = {
            "Apps": QColor("#0078D4"),      # Blue
            "Cache": QColor("#D13438"),     # Red
            "Media": QColor("#B146C2"),     # Purple
            "Development": QColor("#00CC6A"), # Green
            "Archives": QColor("#FFB900"),    # Yellow
            "System": QColor("#737373"),      # Grey
            "Unknown": QColor("#606060")      # Dark Grey
        }

    def set_data(self, root_node: FileNode):
        self.root_node = root_node
        self.draw_treemap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.root_node:
            self.draw_treemap()

    def draw_treemap(self):
        self.scene.clear()
        if not self.root_node:
            return

        width = self.viewport().width()
        height = self.viewport().height()
        self.scene.setSceneRect(0, 0, width, height)
        
        # Start squarification logic
        # For simplicity in this first pass, we'll do a basic "slice and dice" or simplified approach
        # A full squarified algorithm is complex, I will implement a simpler recursive subdivide first
        # to ensure it works, then refine.
        
        self._layout_recursive(self.root_node, QRectF(0, 0, width, height))

    def _layout_recursive(self, node: FileNode, rect: QRectF):
        # Base case: too small to render
        if rect.width() < 2 or rect.height() < 2:
            return

        # If it's a file or empty dir, draw it
        if not node.children:
            color = self.colors.get(node.category, self.colors["Unknown"])
            item = TreemapItem(rect, node, color)
            self.scene.addItem(item)
            return

        # It's a directory with children.
        # 1. Draw the container (optional, maybe just background)
        # 2. Divide space for children
        
        total_size = node.size
        if total_size == 0:
            return

        # Sort children largest to smallest
        children = sorted(node.children, key=lambda x: x.size, reverse=True)
        
        # Simple Slice-and-Dice (Alternating)
        # For a better aspect ratio (squarified), we need a more complex algo.
        # Let's stick to slice-and-dice for V1 implementation speed.
        
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        
        horizontal = w > h
        
        current_x = x
        current_y = y
        
        for i, child in enumerate(children):
            ratio = child.size / total_size
            
            if horizontal:
                child_w = w * ratio
                child_rect = QRectF(current_x, y, child_w, h)
                current_x += child_w
            else:
                child_h = h * ratio
                child_rect = QRectF(x, current_y, w, child_h)
                current_y += child_h
                
            self._layout_recursive(child, child_rect)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, TreemapItem):
            self.itemClicked.emit(item.node)
        super().mousePressEvent(event)
