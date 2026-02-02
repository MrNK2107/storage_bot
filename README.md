# Disk Usage Analyzer (Storage Bot)

A modern, fast, and interactive disk usage analyzer built with Python and PyQt6. This tool helps you visualize and manage your disk space by scanning directories and displaying their usage in a clear, interactive interface.

## Features

-   **Fast Scanning**: Utilizes optimized multi-threading to quickly scan directories and analyze disk usage.
-   **Interactive Visualization**: View your disk usage in a structured list/treemap view.
-   **Details Panel**: Get detailed information about selected files and folders.
-   **Modern UI**: Features a sleek, dark-themed interface designed for Windows 11.
-   **Cross-Platform**: Built with PyQt6, capable of running on Windows, macOS, and Linux (though optimized for Windows).

## Requirements

-   Python 3.8+
-   PyQt6

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/MrNK2107/storage_bot.git
    cd storage_bot
    ```

2.  Install the required dependencies:
    ```bash
    pip install PyQt6
    ```

## Usage

Run the application using Python:

```bash
python main.py
```

1.  Click "Start Scan" in the sidebar.
2.  Select a folder to analyze.
3.  Wait for the scan to complete.
4.  Navigate through the file structure and view details in the panel.

## Project Structure

-   `main.py`: Entry point of the application. Handles the main window and UI setup.
-   `src/scanner.py`: Logic for scanning the file system.
-   `src/ui/`: Contains UI components:
    -   `treemap_widget.py`: Widget for treemap visualization.
    -   `storage_list_view.py`: Widget for list-based visualization.
    -   `details_panel.py`: Panel for displaying file/folder details.

## License

[MIT License](LICENSE)
