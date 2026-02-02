import json
import os
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class HistoryManager:
    def __init__(self, storage_file: str = "storage_history.json"):
        # Store history in a user_data folder or local relative path
        self.storage_path = os.path.join(os.getcwd(), "user_data", storage_file)
        self.history: Dict = {}
        self._load_history()

    def _load_history(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.history = json.load(f)
            except json.JSONDecodeError:
                self.history = {}
        else:
            self.history = {}

    def _save_history(self):
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.history, f, indent=4)

    def save_scan(self, path: str, root_node, retention_days: int = 30):
        """
        Saves the summary of a scan for a specific path.
        """
        # Normalize path to ensure consistency
        norm_path = os.path.normpath(path)
        
        timestamp = time.time()
        
        # Extract immediate children sizes for granular comparison
        children_stats = {}
        for child in root_node.children:
            children_stats[child.name] = child.size

        scan_entry = {
            "timestamp": timestamp,
            "total_size": root_node.size,
            "children": children_stats
        }

        if norm_path not in self.history:
            self.history[norm_path] = []
        
        self.history[norm_path].append(scan_entry)
        
        # Prune old entries
        cutoff_time = timestamp - (retention_days * 86400)
        self.history[norm_path] = [
            entry for entry in self.history[norm_path] 
            if entry["timestamp"] > cutoff_time
        ]
        
        # Sort by timestamp just in case
        self.history[norm_path].sort(key=lambda x: x["timestamp"])
        
        self._save_history()

    def get_insights(self, path: str, current_root_node) -> Optional[Dict]:
        """
        Compares the current scan with the most recent *previous* scan.
        Returns a dictionary of insights or None if no previous history.
        """
        norm_path = os.path.normpath(path)
        
        if norm_path not in self.history or len(self.history[norm_path]) < 2:
            return None
            
        # Get the second to last entry (the one before the one we just saved)
        # Assuming save_scan is called BEFORE get_insights. 
        # Actually strategy: usually we want to compare against what was there BEFORE this current scan.
        # But if we just saved the current scan, valid history has at least 2 entries.
        
        # Let's rely on the list. The last entry is current. The one before is previous.
        latest_entry = self.history[norm_path][-1]
        previous_entry = self.history[norm_path][-2]
        
        time_diff = latest_entry["timestamp"] - previous_entry["timestamp"]
        size_diff = latest_entry["total_size"] - previous_entry["total_size"]
        
        # Find biggest contributors to change
        current_children = latest_entry["children"]
        prev_children = previous_entry["children"]
        
        child_changes = []
        all_child_names = set(current_children.keys()) | set(prev_children.keys())
        
        for name in all_child_names:
            curr_size = current_children.get(name, 0)
            prev_size = prev_children.get(name, 0)
            diff = curr_size - prev_size
            if diff != 0:
                child_changes.append((name, diff))
        
        # Sort by absolute change magnitude (descending)
        child_changes.sort(key=lambda x: abs(x[1]), reverse=True)
        
        return {
            "previous_timestamp": previous_entry["timestamp"],
            "size_diff": size_diff,
            "top_changes": child_changes[:3] # Top 3 changes
        }

    def format_size(self, size):
        # Helper to format size for insights text
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(size) < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"
