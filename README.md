# Filesystem to Web Catalogue

## What it does:
Allows to specify folder that will be parsed to json maintaining a tree structure of subfolders and files with specified extensions. Later on it can be fed to the index.html to quickly view organized and filtered tree view.

Some extensions are currently hardcoded in structure_composer.py and can be changed

## How to run:
1. Run the python structure_composer.py and select the desired folder in the File Dialogue.
2. Output will be a content_data.json file
3. Open index.html file and load this file from the provided dialog
