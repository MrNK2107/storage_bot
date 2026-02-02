from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PyQt6.QtGui import QPainter, QColor, QFont, QPen
from PyQt6.QtCore import Qt

class StorageBreakdownChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        # Create Chart elements
        self.series = QPieSeries()
        self.series.setHoleSize(0.4) 
        self.series.setPieSize(0.7)

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle("Storage Composition")
        self.chart.setTitleFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        self.chart.legend().setFont(QFont("Segoe UI", 9))
        self.chart.setBackgroundRoundness(0)
        self.chart.setMargins(0,0,0,0)
        self.chart.setBackgroundVisible(False) # Let parent background show

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Transparent background for the view
        self.chart_view.setStyleSheet("background: transparent;")
        
        self.layout().addWidget(self.chart_view)

        # Category Colors
        self.colors = {
            "Apps": QColor("#FF6B6B"),       # Red
            "Cache": QColor("#FCC2D7"),      # Pink
            "Media": QColor("#4DABF7"),      # Blue
            "Development": QColor("#51CF66"),# Green
            "Archives": QColor("#FF922B"),   # Orange
            "Downloads": QColor("#F06595"),  # Pinkia
            "Unknown": QColor("#868E96")     # Gray
        }

    def update_data(self, root_node):
        self.series.clear()
        
        totals = {cat: 0 for cat in self.colors.keys()}
        
        # Traverse and sum
        self._sum_recursive(root_node, totals)
        
        total_size = root_node.size or 1 # Avoid div by zero
        
        for cat, size in totals.items():
            if size > 0:
                percentage = (size / total_size) * 100
                if percentage < 1: 
                    continue # Skip tiny slices
                
                slice_ = self.series.append(f"{cat} ({percentage:.1f}%)", size)
                slice_.setBrush(self.colors.get(cat, QColor("#868E96")))
                slice_.setLabelVisible(True)
                slice_.setLabelColor(QColor("white"))
                
                # Explode the biggest slice slice
                # if percentage > 50:
                #    slice_.setExploded(True)
                #    slice_.setExplodeDistanceFactor(0.1)

    def _sum_recursive(self, node, totals):
        if not node.is_dir:
            if node.category in totals:
                totals[node.category] += node.size
        else:
            for child in node.children:
                self._sum_recursive(child, totals)
