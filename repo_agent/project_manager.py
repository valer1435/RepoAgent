import os
import jedi

class ProjectManager:
    """Manages the project structure and hierarchy within a repository.

Sets up the project manager by initializing the repository path and project hierarchy file path, which is essential for the Repository Agent to analyze and document the Python project effectively.

Args:
    repo_path (str): The root directory of the repository.
    project_hierarchy (str): The subdirectory within the repository where the project hierarchy JSON file is located.

Returns:
    None

Raises:
    ValueError: If the provided repository path or project hierarchy is invalid.

Note:
    See also: Repository Agent Documentation Generator for more details on how this class fits into the overall framework.


Generates a string representation of the project's directory structure.

This function recursively walks through the directory tree, listing directories and Python files (ending in ".py") under their respective directories. Hidden files and directories starting with "." are ignored.

Args:
    None

Returns:
    str: The project structure as a string, where directories are indented and files ending in ".py" are listed under their respective directories.

Raises:
    None


Constructs a nested dictionary representing the directory tree from given paths.

This function builds a detailed directory tree structure based on input paths to reference and document project components within the Repository Agent framework. It supports code analysis and change detection features by generating comprehensive directory structures for documentation purposes.

Args:
    who_reference_me (list of str): Paths that reference the project manager.
    reference_who (list of str): Paths referenced by the project manager.
    doc_item_path (str): Path to the documentation item, with a star added before the last part.

Returns:
    str: A string representation of the nested dictionary tree.

Notes:
    See also: Repository Agent Documentation Generator for more details on how this function fits into the overall framework.
"""

    def __init__(self, repo_path, project_hierarchy):
        """Initialize the ProjectManager instance.

Sets up the project manager by initializing the repository path and project hierarchy file path. This is crucial for the Repository Agent to analyze and document the Python project effectively, ensuring that all necessary files are created or updated as needed.

Args:  
    repo_path (str): The root directory of the repository.  
    project_hierarchy (str): The subdirectory within the repository where the project hierarchy JSON file is located.  

Returns:  
    None  

Raises:  
    ValueError: If the provided repository path or project hierarchy is invalid.  

Note:  
    See also: jedi.Project, os.path.join.
"""
        self.repo_path = repo_path
        self.project = jedi.Project(self.repo_path)
        self.project_hierarchy = os.path.join(self.repo_path, project_hierarchy, 'project_hierarchy.json')

    def get_project_structure(self):
        """Returns the project structure by recursively walking through the directory tree.

This function generates a string representation of the project's directory structure, where directories are indented and Python files (ending in ".py") are listed under their respective directories. Hidden files and directories starting with "." are ignored. The Repository Agent uses this information to manage and document the project hierarchy effectively.

Args:
    None

Returns:
    str: The project structure as a string, where directories are indented and files ending in ".py" are listed under their respective directories.

Raises:
    None

Note:
    Hidden files and directories starting with "." are not included in the output.
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
        """Builds a nested dictionary representing a directory tree from given paths.

This function constructs a detailed directory structure based on the input paths, which are used to reference and document project components within the Repository Agent framework. It supports the tool's code analysis and change detection features by generating comprehensive directory structures for documentation purposes.

Args:  
    who_reference_me (list of str): Paths that reference the project manager.  
    reference_who (list of str): Paths referenced by the project manager.  
    doc_item_path (str): Path to the documentation item, with a star added before the last part.

Returns:  
    str: A string representation of the nested dictionary tree.

Notes:  
    This function is integral to the Repository Agent's ability to manage and document complex Python projects efficiently.
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
if __name__ == '__main__':
    project_manager = ProjectManager(repo_path='', project_hierarchy='')
    print(project_manager.get_project_structure())