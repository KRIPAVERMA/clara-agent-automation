"""
file_utils.py
Utility functions for file I/O operations:
- Loading transcript text files
- Saving/loading JSON files
- Ensuring directory structures exist
"""

import os
import json
import glob


def load_transcript(file_path: str) -> str:
    """
    Load a transcript text file and return its contents as a string.

    Args:
        file_path: Absolute or relative path to the transcript .txt file.

    Returns:
        The full text content of the transcript.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def save_json(data: dict, file_path: str) -> None:
    """
    Save a dictionary as a formatted JSON file, creating parent directories
    if they do not exist.

    Args:
        data: Dictionary to serialize.
        file_path: Destination path for the JSON file.
    """
    ensure_directory(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  [saved] {file_path}")


def load_json(file_path: str) -> dict:
    """
    Load a JSON file and return its contents as a dictionary.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed dictionary from the JSON file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_directory(dir_path: str) -> None:
    """
    Create a directory (and all parent directories) if it does not already exist.

    Args:
        dir_path: Directory path to create.
    """
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)


def list_files(directory: str, extension: str = ".txt") -> list:
    """
    List all files in a directory matching a given extension.

    Args:
        directory: Directory to search.
        extension: File extension filter (default: '.txt').

    Returns:
        Sorted list of matching file paths.
    """
    pattern = os.path.join(directory, f"*{extension}")
    return sorted(glob.glob(pattern))


def save_text(content: str, file_path: str) -> None:
    """
    Save a string to a text file, creating parent directories if needed.

    Args:
        content: Text content to write.
        file_path: Destination path.
    """
    ensure_directory(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [saved] {file_path}")
