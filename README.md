# Disk Usage Analyzer (Storage Bot)

A modern, fast, and feature-rich disk usage analyzer and cleanup tool built with Python and PyQt6. Storage Bot helps you visualize disk space, track usage over time, and intelligently clean up clutter.

## Features

### 🔍 Deep Analysis
-   **Fast Scanning**: Utilizes optimized multi-threading to quickly scan directories and huge drives.
-   **Visual Analytics**: Beautiful interactive charts visualize your storage breakdown by category (Apps, Media, Development, etc.).
-   **Drive Detection**: Automatically detects and lists all available drives (C:, D:, etc.) for one-click scanning.

### 🧠 Smart Cleanup
-   **Intelligent Suggestions**: Automatically identifies:
    -   **Abandoned Cache**: Old cache files unused for >14 days.
    -   **Installer Residue**: Setup files (.exe, .msi) left in Downloads.
    -   **Ghost Folders**: Empty directories cluttering your system.
    -   **Oversized Files**: massive media or archives taking up space.
-   **Duplicate Finder**: Detects exact duplicate files efficiently using size grouping and partial hashing.
-   **Safe Deletion**: Integrated with the system Recycle Bin—files are never permanently deleted without your final review.

### 📈 History & Insights
-   **Storage Trends**: Tracks your storage usage over time.
-   **Smart Insights**: Tells you exactly how much space you've used or freed since your last scan (e.g., "+2GB since Yesterday").

## Requirements

-   Python 3.8+
-   PyQt6
-   PyQt6-Charts
-   send2trash

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/MrNK2107/storage_bot.git
    cd storage_bot
    ```

2.  Install the required dependencies:
    ```bash
    pip install PyQt6 PyQt6-Charts send2trash
    ```

## Usage

Run the application using Python:

```bash
python main.py
```

1.  **Select a Drive/Folder**: Click a drive in the sidebar or select a custom folder.
2.  **View Analytics**: See the donut chart and treemap visualization of your files.
3.  **Check Recommendations**: Click "Cleanup Recommendations" to review and safely remove junk files.

## Project Structure

-   `main.py`: Application entry point and UI orchestration.
-   `src/scanner.py`: Background workers for scanning, analysis, and duplicate detection.
-   `src/history_manager.py`: Manages local storage history and insights generation.
-   `src/ui/`:
    -   `chart_widget.py`: Visual analytics components.
    -   `recommendation_view.py`: Interactive cleanup list.
    -   `treemap_widget.py`: Visualization logic.

## License

[MIT License](LICENSE)
