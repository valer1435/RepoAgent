# Utils Module
## Overview
The `Utils` module is a collection of utility classes and functions designed to support the automation of documentation generation and management for a Git repository. It includes tools for updating and removing docstrings, checking files against `.gitignore` patterns, and managing temporary files and modifications in the repository. These utilities are essential for ensuring that the documentation remains accurate and up-to-date, while also maintaining the integrity of the repository's file structure.

## Purpose
The primary purpose of the `Utils` module is to provide a set of robust and efficient tools that facilitate the automated generation and management of documentation within a Git environment. Specifically, the module:

- **Updates and Removes Docstrings**: Provides functions to update and remove docstrings from code, ensuring that the documentation is consistent and accurate.
- **Checks Gitignore Patterns**: Offers a utility class to check files and folders against `.gitignore` patterns, helping to identify which files should be ignored during the documentation process.
- **Manages Temporary Files**: Includes functions to create, delete, and recover temporary files, ensuring that the repository remains clean and that modifications are tracked accurately.

These utilities are designed to work seamlessly within the project's workflow, enhancing the overall efficiency and reliability of the documentation management process.