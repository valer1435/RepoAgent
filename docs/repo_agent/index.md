# Repository Agent

## Overview
The Repository Agent is a tool designed to automate the generation and management of documentation for Python projects. It utilizes large language models (LLMs) to create comprehensive summaries and maintain up-to-date documentation across various modules within a repository.

This module includes several key components:

- **Change Detection**: The `ChangeDetector` class identifies changes in the repository, such as added or modified files, and retrieves differences using Git commands.
  
- **Documentation Generation**: The `ChatEngine` class manages the process of generating documentation for Python projects by interacting with LLMs to create detailed summaries and maintain up-to-date documentation.

- **Metadata Management**: The `DocMetaInfo` classes handle metadata related to documentation items, including their types, statuses, and relationships within the project hierarchy.
  
- **File Handling**: The `FileHandler` class manages file operations such as reading, writing, and parsing Python files for code information and structure generation.

- **Logging**: The `log.py` module configures logging to ensure that all actions taken by the Repository Agent are recorded and traceable.

- **Main Execution**: The `main.py` script orchestrates the overall process of documentation generation, including initialization, task management, and cleanup operations.

## Purpose
The primary purpose of the Repository Agent is to streamline the documentation generation process for Python projects. It automates the detection of changes in the repository, generates comprehensive summaries using LLMs, and manages metadata to ensure that all components are correctly documented. This tool aims to reduce manual effort and improve consistency across all modules within a project.