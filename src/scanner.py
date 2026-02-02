import os
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool

@dataclass
class FileNode:
    name: str
    path: str
    size: int
    is_dir: bool
    category: str = "Unknown"
    children: List['FileNode'] = field(default_factory=list)
    parent: Optional['FileNode'] = None

    def add_child(self, child: 'FileNode'):
        self.children.append(child)
        child.parent = self

class ScanSignals(QObject):
    progress = pyqtSignal(str)  # Currently scanning path
    finished = pyqtSignal(object) # Returns FileNode root
    error = pyqtSignal(str)

class ScannerWorker(QRunnable):
    def __init__(self, root_path: str):
        super().__init__()
        self.root_path = root_path
        self.signals = ScanSignals()
        self.stop_requested = False

    def run(self):
        try:
            root_node = self._scan_recursive(self.root_path)
            self.signals.finished.emit(root_node)
        except Exception as e:
            self.signals.error.emit(str(e))

    def _scan_recursive(self, path: str) -> FileNode:
        if self.stop_requested:
            return None
        
        # self.signals.progress.emit(path) # Too frequent updates kill perf, handled in UI via timer or throttled

        name = os.path.basename(path) or path
        node = FileNode(name=name, path=path, size=0, is_dir=True, category=self._categorize_folder(path))

        try:
            with os.scandir(path) as it:
                for entry in it:
                    if self.stop_requested:
                        break
                    
                    try:
                        if entry.is_file(follow_symlinks=False):
                            size = entry.stat().st_size
                            cat = self._categorize_file(entry.name)
                            child = FileNode(name=entry.name, path=entry.path, size=size, is_dir=False, category=cat)
                            node.add_child(child)
                            node.size += size
                        elif entry.is_dir(follow_symlinks=False):
                            # Skip some heavy/recursive folders for safety/perf (optional, can refine later)
                            if entry.name in ['$RECYCLE.BIN', 'System Volume Information']:
                                continue
                                
                            child = self._scan_recursive(entry.path)
                            if child:
                                node.add_child(child)
                                node.size += child.size
                    except PermissionError:
                        continue # Skip unreadable
                    except OSError:
                        continue
        except PermissionError:
            pass # Skip unreadable dirs

        return node

    def _categorize_file(self, filename: str) -> str:
        lower = filename.lower()
        if lower.endswith(('.exe', '.dll', '.msi', '.bat', '.cmd')):
            return "Apps"
        if lower.endswith(('.log', '.tmp', '.cache', '.chk', '.dmp')):
            return "Cache"
        if lower.endswith(('.mp4', '.mov', '.mp3', '.wav', '.jpg', '.png', '.gif')):
            return "Media"
        if lower.endswith(('.py', '.js', '.ts', '.css', '.html', '.java', '.cpp', '.c', '.h', '.json', '.xml', '.md')):
            return "Development"
        if lower.endswith(('.zip', '.rar', '.7z', '.tar', '.gz', '.iso')):
            return "Archives"
        return "Unknown"

    def _categorize_folder(self, path: str) -> str:
        name = os.path.basename(path).lower()
        if name in ['node_modules', 'venv', '.git', 'build', 'dist', '__pycache__']:
            return "Development"
        if name in ['temp', 'tmp', 'cache', 'logs']:
            return "Cache"
        return "Folder"

class ScanManager:
    def __init__(self):
        self.threadpool = QThreadPool()
        print(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

    def start_scan(self, path: str, on_finish, on_progress=None):
        worker = ScannerWorker(path)
        worker.signals.finished.connect(on_finish)
        if on_progress:
            worker.signals.progress.connect(on_progress)
        self.threadpool.start(worker)
