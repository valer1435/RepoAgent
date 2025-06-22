import os
import jedi

class ProjectManager:
    """
    ProjectManager is a class for managing and organizing the structure of a project repository.
    
    This class automates the generation and management of documentation for a Git repository. It integrates various functionalities to detect changes, handle file operations, manage project settings, and generate summaries for modules and directories. The tool also includes a chat engine and a multi-task dispatch system to enhance user interaction and process management. Additionally, it provides utilities for handling .gitignore files and managing fake files for untracked and modified content.
    
    Args:
        repo_path (str): The path to the repository.
        project_hierarchy (str): The relative path to the project hierarchy file within the repository.
    
    Returns:
        None
    
    Raises:
        None
    
    Note:
        The project hierarchy file is expected to be a JSON file located at `repo_path/project_hierarchy/project_hierarchy.json`. This file is crucial for defining the structure of the project and guiding the documentation generation process.
    
    get_project_structure
    
    Returns the project structure as a formatted string.
    
    Args:
        None
    
    Returns:
        str: A string representing the project structure.
    
    Raises:
        None
    
    Note:
        This method walks through the directory structure and appends the names of directories and Python files to a list, which is then joined into a single string.
    
    build_path_tree
    
    Builds a path tree for references within the project.
    
    Args:
        who_reference_me (List[str]): A list of paths that reference the current item.
        reference_who (List[str]): A list of paths that are referenced by the current item.
        doc_item_path (str): The path of the current documentation item.
    
    Returns:
        str: A string representing the path tree.
    
    Raises:
        ValueError: If any of the input lists contain invalid paths.
    
    Note:
        This method constructs a tree structure from the provided paths and marks the current documentation item with a special symbol. The tree is then converted to a string representation.
    
    __init__
    
    Initializes the ProjectManager instance.
    
    Args:
        repo_path (str): The path to the repository.
        project_hierarchy (str): The relative path to the project hierarchy file within the repository.
    
    Returns:
        None
    
    Raises:
        None
    
    Note:
        The project hierarchy file is expected to be a JSON file located at `repo_path/project_hierarchy/project_hierarchy.json`. This file is crucial for defining the structure of the project and guiding the documentation generation process.
    """

    def __init__(self, repo_path, project_hierarchy):
        """
    Initializes the ProjectManager instance.
    
    Sets up the project manager with the specified repository path and project hierarchy file. This tool automates the generation and management of documentation for a Git repository, integrating functionalities to detect changes, handle file operations, manage tasks, and configure settings. It ensures efficient and accurate documentation updates, making it particularly useful for large repositories where maintaining consistent and accurate documentation can be challenging and time-consuming.
    
    Args:
        repo_path (str): The path to the repository.
        project_hierarchy (str): The relative path to the project hierarchy file within the repository.
    
    Returns:
        None
    
    Raises:
        None
    
    Note:
        The project hierarchy file is expected to be a JSON file located at `repo_path/project_hierarchy/project_hierarchy.json`. This file is crucial for defining the structure of the project and guiding the documentation generation process.
    """
        self.repo_path = repo_path
        self.project = jedi.Project(self.repo_path)
        self.project_hierarchy = os.path.join(self.repo_path, project_hierarchy, 'project_hierarchy.json')

    def get_project_structure(self):
        """
    Gets the project structure as a formatted string.
    
    This method recursively walks through the directory structure of the project, listing directories and Python files. Hidden files and directories (those starting with a dot) are ignored. It is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository, ensuring that documentation is up-to-date and accurate.
    
    Args:
        None
    
    Returns:
        str: A string representing the project structure, with directories and Python files indented to show the hierarchy.
    
    Raises:
        None
    
    Note:
        This method only includes Python files (files ending with .py) in the structure. It is particularly useful for large repositories where maintaining consistent and accurate documentation can be challenging and time-consuming. By automating the detection and listing of project files, it helps streamline the documentation process and ensures that the structure remains synchronized with the codebase.
    """

        def walk_dir(root, prefix=''):
            structure.append(prefix + os.path.basename(root))
            new_prefix = prefix + '  '
            for name in sorted(os.listdir(root)):
                if name.startswith('.'):
                    continue
                path = os.path.join(root, name)
                if os.path.isdir(path):
                    structure.append(new_prefix + name)
                    walk_dir(path, new_prefix)
                elif os.path.isfile(path) and name.endswith('.py'):
                    structure.append(new_prefix + name)
        structure = []
        walk_dir(self.repo_path)
        return '\n'.join(structure)

    def build_path_tree(self, who_reference_me, reference_who, doc_item_path):
        """
    Builds a path tree from reference lists and a document item path.
    
    This method constructs a tree structure from the paths provided in `who_reference_me` and `reference_who`, and then modifies the last part of the `doc_item_path` to include a special marker before converting the tree to a string representation. This is particularly useful for generating accurate and up-to-date documentation for a Git repository, ensuring that all references are correctly represented.
    
    Args:
        who_reference_me (List[str]): A list of paths referencing the current document item.
        reference_who (List[str]): A list of paths that the current document item references.
        doc_item_path (str): The path of the document item to be marked in the tree.
    
    Returns:
        str: A string representation of the path tree with the document item path marked.
    
    Raises:
        ValueError: If any of the input lists contain invalid paths.
    
    Note:
        The method uses `os.sep` to split the paths into parts, ensuring compatibility with different operating systems. This method is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository, integrating various functionalities to detect changes, handle file operations, manage tasks, and configure settings. The tool aims to streamline the documentation process, reducing manual effort and ensuring that documentation remains synchronized with the codebase.
    """
        from collections import defaultdict

        def tree():
            return defaultdict(tree)
        path_tree = tree()
        for path_list in [who_reference_me, reference_who]:
            for path in path_list:
                parts = path.split(os.sep)
                node = path_tree
                for part in parts:
                    node = node[part]
        parts = doc_item_path.split(os.sep)
        parts[-1] = '✳️' + parts[-1]
        node = path_tree
        for part in parts:
            node = node[part]

        def tree_to_string(tree, indent=0):
            s = ''
            for key, value in sorted(tree.items()):
                s += '    ' * indent + key + '\n'
                if isinstance(value, dict):
                    s += tree_to_string(value, indent + 1)
            return s
        return tree_to_string(path_tree)