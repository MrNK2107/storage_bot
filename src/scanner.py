import os
import time
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool

@dataclass
class FileNode:
    name: str
    path: str
    size: int
    is_dir: bool
    modified: float = 0.0
    category: str = "Unknown"
    children: List['FileNode'] = field(default_factory=list)
    parent: Optional['FileNode'] = None

    def add_child(self, child: 'FileNode'):
        self.children.append(child)
        child.parent = self

class ScanSignals(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(object) # Returns FileNode root
    error = pyqtSignal(str)

class AnalysisSignals(QObject):
    finished = pyqtSignal(dict, list) # suggestions, duplicates
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
        
        name = os.path.basename(path) or path
        # Directory modified time isn't critical for our logic, but we can capture it
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0.0
            
        node = FileNode(name=name, path=path, size=0, is_dir=True, modified=mtime, category=self._categorize_folder(path))

        try:
            with os.scandir(path) as it:
                for entry in it:
                    if self.stop_requested:
                        break
                    
                    try:
                        if entry.is_file(follow_symlinks=False):
                            stat = entry.stat()
                            size = stat.st_size
                            mtime = stat.st_mtime
                            cat = self._categorize_file(entry.name)
                            child = FileNode(name=entry.name, path=entry.path, size=size, is_dir=False, modified=mtime, category=cat)
                            node.add_child(child)
                            node.size += size
                        elif entry.is_dir(follow_symlinks=False):
                            if entry.name in ['$RECYCLE.BIN', 'System Volume Information']:
                                continue
                                
                            child = self._scan_recursive(entry.path)
                            if child:
                                node.add_child(child)
                                node.size += child.size
                    except PermissionError:
                        continue 
                    except OSError:
                        continue
        except PermissionError:
            pass 

        return node

    def _categorize_file(self, filename: str) -> str:
        lower = filename.lower()
        if lower.endswith(('.exe', '.dll', '.msi', '.bat', '.cmd', '.dmg', '.pkg')):
            return "Apps"
        if lower.endswith(('.log', '.tmp', '.cache', '.chk', '.dmp')):
            return "Cache"
        if lower.endswith(('.mp4', '.mov', '.mp3', '.wav', '.jpg', '.png', '.gif', '.mkv', '.avi', '.flac')):
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
        if name == 'downloads':
            return "Downloads"
        return "Folder"

class AnalysisWorker(QRunnable):
    def __init__(self, root_node: FileNode):
        super().__init__()
        self.root_node = root_node
        self.signals = AnalysisSignals()

    def run(self):
        try:
            suggestions = self.get_cleanup_suggestions(self.root_node)
            duplicates = self.find_duplicates(self.root_node)
            self.signals.finished.emit(suggestions, duplicates)
        except Exception as e:
            self.signals.error.emit(str(e))

    def get_cleanup_suggestions(self, node: FileNode) -> Dict[str, List[FileNode]]:
        suggestions = {
            "Abandoned Cache": [],
            "Oversized Media/Archives": [],
            "Installer Residue": [],
            "Ghost Folders": []
        }
        
        now = time.time()
        
        def traverse(n: FileNode):
            if n.is_dir:
                if n.size == 0 and not n.children:
                    suggestions["Ghost Folders"].append(n)
                
                # Check for "Downloads" folder context for installer residue
                is_downloads = n.name.lower() == "downloads"
                
                for child in n.children:
                    # Pass context if currently in Downloads or child is in Downloads
                    traverse_recursive(child, in_downloads=is_downloads)
            else:
                # File checks
                self._check_file(n, now, False, suggestions)

        def traverse_recursive(n: FileNode, in_downloads: bool):
            if n.is_dir:
                if n.size == 0 and not n.children:
                    suggestions["Ghost Folders"].append(n)
                
                current_is_downloads = in_downloads or (n.name.lower() == "downloads")
                for child in n.children:
                    traverse_recursive(child, current_is_downloads)
            else:
                self._check_file(n, now, in_downloads, suggestions)

        traverse_recursive(node, False)
        return suggestions

    def _check_file(self, n: FileNode, now: float, in_downloads: bool, suggestions: Dict):
        # Abandoned Cache
        if n.category == "Cache":
            if (now - n.modified) > (14 * 86400): # 14 days
                suggestions["Abandoned Cache"].append(n)
        
        # Oversized Media/Archives
        if n.category in ["Media", "Archives"]:
            if n.size > (1024 * 1024 * 1024): # 1GB
                suggestions["Oversized Media/Archives"].append(n)
        
        # Installer Residue
        if in_downloads:
            if n.name.lower().endswith(('.exe', '.msi', '.dmg', '.pkg')):
                suggestions["Installer Residue"].append(n)

    def find_duplicates(self, root: FileNode) -> List[List[FileNode]]:
        size_map: Dict[int, List[FileNode]] = {}
        
        def traverse(n: FileNode):
            if n.is_dir:
                for child in n.children:
                    traverse(child)
            else:
                if n.size > 0:
                    if n.size not in size_map:
                        size_map[n.size] = []
                    size_map[n.size].append(n)
        
        traverse(root)
        
        # Filter potential duplicates (same size)
        potential_groups = [group for group in size_map.values() if len(group) > 1]
        
        confirmed_duplicates = []
        
        for group in potential_groups:
            hash_map = {}
            for node in group:
                try:
                    partial_hash = self._get_partial_hash(node.path)
                    if partial_hash:
                        if partial_hash not in hash_map:
                            hash_map[partial_hash] = []
                        hash_map[partial_hash].append(node)
                except Exception:
                    continue
            
            for hash_group in hash_map.values():
                if len(hash_group) > 1:
                    confirmed_duplicates.append(hash_group)
                    
        return confirmed_duplicates

    def _get_partial_hash(self, path: str) -> str:
        try:
            with open(path, 'rb') as f:
                chunk = f.read(1024)
                return hashlib.md5(chunk).hexdigest()
        except OSError:
            return ""

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

    def start_analysis(self, root_node: FileNode, on_finish):
        worker = AnalysisWorker(root_node)
        worker.signals.finished.connect(on_finish)
        self.threadpool.start(worker)
