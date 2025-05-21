import os
import json
import urllib.parse # Import for URL encoding
import re # Import for regular expressions
import argparse # Import for command-line argument parsing
import sys # Import for system-specific parameters and functions
import tkinter as tk # Import tkinter for GUI elements
from tkinter import filedialog # Import filedialog for folder selection dialog

def generate_content_data(root_dir, output_file="content_data.json"):
    """
    Traverses a directory recursively, generating content data for a website
    with a tree-like (nested) JSON structure. It saves this data to a JSON file
    with absolute file:// URLs.

    The resulting folder entries and files within them are sorted:
    1. By an extracted numeric part in ascending order.
    2. If no numeric part is found, then alphabetically by their 'name'.
    Folders with numeric parts appear before those without.

    Args:
        root_dir (str): The root directory to start the traversal from.
        output_file (str, optional): The name of the output JSON file.
                                     Defaults to "content_data.json".
    """
    content_data = []

    # Normalize the root_dir path to ensure consistent slashes and handle drive letters on Windows
    normalized_root_dir = os.path.abspath(root_dir)
    # Ensure the path ends with a slash for correct URL concatenation
    if not normalized_root_dir.endswith(os.sep):
        normalized_root_dir += os.sep

    # Construct the base URL using the file:// scheme
    # For Windows paths, ensure backslashes are converted to forward slashes.
    # The format file:///C:/path/to/file is generally readable by web browsers.
    if os.name == 'nt' and normalized_root_dir[1] == ':': # Check for Windows drive letter
        # Convert C:\path to /C:/path
        path_for_url = '/' + normalized_root_dir.replace('\\', '/')
    else:
        path_for_url = normalized_root_dir.replace('\\', '/')

    base_url = f"file://{path_for_url}"
    # Ensure base_url ends with a slash if it's not empty, for proper joining with relative paths
    if not base_url.endswith('/'):
        base_url += '/'

    print(f"Generating URLs with base: {base_url}")

    # Define a custom sorting key function for files within a folder
    def file_sort_key(filename):
        # Try to find a numeric part at the beginning of the filename
        match = re.match(r'^(\d+)', filename)
        if match:
            # If it starts with a number, return a tuple:
            # (0, for numeric-starting files to come first)
            # (the integer value of the number for numeric sorting)
            # (the lowercase full filename for secondary alphabetical sorting in case of numeric ties)
            return (0, int(match.group(1)), filename.lower())
        else:
            # If it doesn't start with a number, return a tuple:
            # (1, for non-numeric-starting files to come after numeric ones)
            # (0 as a placeholder for the numeric part, as it doesn't apply)
            # (the lowercase full filename for alphabetical sorting)
            return (1, 0, filename.lower())

    # Define a custom sorting key function for top-level folders and subfolders
    def folder_sort_key_with_numeric_extract(item):
        name = item['name']
        # Try to find the first sequence of digits in the name
        match = re.search(r'\d+', name)
        if match:
            # If a number is found, return a tuple: (0 for numeric, the integer value, lowercase name)
            # This ensures numeric items come first and are sorted by their value.
            return (0, int(match.group(0)), name.lower())
        else:
            # If no number is found, return a tuple: (1 for non-numeric, 0 as a placeholder, lowercase name)
            # This ensures non-numeric items come after numeric items, and are sorted alphabetically.
            return (1, 0, name.lower())

    def traverse_directory(current_path, original_root_dir, base_file_url):
        """
        Recursively traverses a directory to build the content tree.

        Args:
            current_path (str): The current directory being traversed.
            original_root_dir (str): The initial root directory provided by the user.
            base_file_url (str): The constructed base file:// URL.

        Returns:
            dict: A dictionary representing the current folder's structure,
                  including its name, files, and nested subfolders.
        """
        folder_name = os.path.basename(current_path)

        # Special handling for the very root folder's name to be more descriptive
        if current_path == original_root_dir:
            # Use the last part of the absolute path for the root folder's name
            folder_name = os.path.basename(os.path.abspath(original_root_dir).rstrip(os.sep))
            if not folder_name: # Fallback for cases like C:\ or /
                folder_name = "Root Directory"

        current_folder_entry = {
            "name": folder_name,
            "files": [],
            "subfolders": []
        }

        # List all items (files and directories) in the current path
        try:
            items = os.listdir(current_path)
        except PermissionError:
            print(f"Warning: Permission denied to access '{current_path}'. Skipping this directory.")
            return current_folder_entry # Return an empty entry for inaccessible directories
        except FileNotFoundError:
            print(f"Warning: Directory '{current_path}' not found. Skipping.")
            return current_folder_entry

        files_in_current_dir = []
        subdirs_in_current_dir = []

        for item_name in items:
            item_path = os.path.join(current_path, item_name)
            if os.path.isfile(item_path):
                files_in_current_dir.append(item_name)
            elif os.path.isdir(item_path):
                subdirs_in_current_dir.append(item_name)

        # Process and sort relevant files within the current directory
        relevant_files = []
        for filename in files_in_current_dir:
            if filename.lower().endswith((".mp4", ".webm", ".avi", ".html", ".htm")):
                relevant_files.append(filename)

        relevant_files.sort(key=file_sort_key) # Sort files using the custom key

        for filename in relevant_files:
            file_path = os.path.join(current_path, filename)
            file_type = ""
            if filename.lower().endswith((".mp4", ".webm", ".avi")):
                file_type = "video"
            elif filename.lower().endswith((".html", ".htm")):
                file_type = "link"

            # Construct the relative path from the original root_dir
            # This ensures URLs are consistent regardless of nesting depth.
            relative_file_path = os.path.relpath(file_path, original_root_dir).replace("\\", "/")
            encoded_relative_file_path = urllib.parse.quote(relative_file_path)
            absolute_url = f"{base_file_url}{encoded_relative_file_path}"

            file_entry = {
                "type": file_type,
                "name": filename,
                "url": absolute_url
            }
            current_folder_entry["files"].append(file_entry)

        # Recursively process subfolders and add them to the current folder's entry
        subfolder_entries = []
        # Sort subdirectories by name before traversing them to ensure consistent output order
        subdirs_in_current_dir.sort(key=str.lower) # Simple alphabetical sort for directory names before recursion
        for subdir_name in subdirs_in_current_dir:
            subdir_path = os.path.join(current_path, subdir_name)
            subfolder_entry = traverse_directory(subdir_path, original_root_dir, base_file_url)
            # Only add subfolders that actually contain files or further subfolders
            if subfolder_entry["files"] or subfolder_entry["subfolders"]:
                subfolder_entries.append(subfolder_entry)

        # Sort the collected subfolder entries using the custom folder sorting key
        subfolder_entries.sort(key=folder_sort_key_with_numeric_extract)
        current_folder_entry["subfolders"] = subfolder_entries

        return current_folder_entry

    # Start the recursive traversal from the normalized root directory
    # The top-level structure will be a list containing one folder entry for the root_dir
    root_folder_data = traverse_directory(normalized_root_dir, normalized_root_dir, base_url)

    # Only add the root folder if it contains any files or subfolders
    if root_folder_data["files"] or root_folder_data["subfolders"]:
        content_data.append(root_folder_data)

    # Save the content data to a JSON file
    with open(output_file, "w") as f:
        json.dump(content_data, f, indent=4)  # Indent for readability

    print(f"Content data successfully generated and saved to {output_file}")


if __name__ == "__main__":
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="Generate content data for a website with sorted entries and a tree structure.")

    # Add the --root_dir argument (optional, as GUI will be fallback)
    parser.add_argument('--root_dir', type=str,
                        help="The root directory to traverse (e.g., /path/to/your/content).")

    # Parse the command-line arguments
    args = parser.parse_args()

    root_directory = None

    # Check if --root_dir was provided
    if args.root_dir:
        root_directory = args.root_dir
        print(f"Using root directory from command-line argument: {root_directory}")
    else:
        # If no --root_dir argument, open a GUI folder selection dialog
        print("No --root_dir argument provided. Opening folder selection dialog...")
        # Create a Tkinter root window, but hide it to prevent a blank window from appearing
        root = tk.Tk()
        root.withdraw()
        root_directory = filedialog.askdirectory(title="Select Root Directory for Content Generation")
        root.destroy() # Destroy the Tkinter root window after selection

        if not root_directory:
            print("No directory selected. Exiting.")
            sys.exit(0) # Exit gracefully if user cancels the dialog
        else:
            print(f"Selected root directory via GUI: {root_directory}")


    # Ensure the directory exists
    if not os.path.exists(root_directory):
        print(f"Error: The directory '{root_directory}' does not exist.")
        sys.exit(1) # Exit with an error code
    else:
        # Generate and save the content data
        generate_content_data(root_directory)
