import os
import jedi


class ProjectManager:
    """
    Manages and analyzes a software project's structure and dependencies."""

    def __init__(self, repo_path, project_hierarchy):
        """
        Initializes a project workspace, loading the repository and defining the location of its hierarchy file.

            Args:
                repo_path: The path to the repository.
                project_hierarchy: The relative path within the repository to the
                    project hierarchy JSON file.

            Returns:
                None
        """

        self.repo_path = repo_path
        self.project = jedi.Project(self.repo_path)
        self.project_hierarchy = os.path.join(
            self.repo_path, project_hierarchy, "project_hierarchy.json"
        )

    def get_project_structure(self):
        """
        Generates a navigable, text-based representation of the repository’s file system, highlighting Python files and their organization.

            This method recursively walks through the repository path, listing directories and Python files,
            excluding hidden files/directories (those starting with '.'). The output is formatted with indentation
            to represent the hierarchy.

            Args:
                None

            Returns:
                str: A string containing the project structure, with each line representing a file or directory.
        """

        def walk_dir(root, prefix=""):
            structure.append(prefix + os.path.basename(root))
            new_prefix = prefix + "  "
            for name in sorted(os.listdir(root)):
                if name.startswith("."):
                    continue
                path = os.path.join(root, name)
                if os.path.isdir(path):
                    structure.append(new_prefix + name)
                    walk_dir(path, new_prefix)
                elif os.path.isfile(path) and name.endswith(".py"):
                    structure.append(new_prefix + name)

        structure = []
        walk_dir(self.repo_path)
        return "\n".join(structure)

    def build_path_tree(self, who_reference_me, reference_who, doc_item_path):
        """
        Constructs a hierarchical string representation of file paths, marking the target documentation item for emphasis. This structure visualizes relationships between files and their dependencies within the repository.

            This method constructs a nested dictionary representing the paths
            provided and then converts it into a human-readable string format.
            The last part of `doc_item_path` is marked with '✳️'.

            Args:
                who_reference_me: A list of file paths.
                reference_who: A list of file paths.
                doc_item_path: The path to the documentation item.

            Returns:
                str: A string representation of the constructed path tree.
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
        parts[-1] = "✳️" + parts[-1]
        node = path_tree
        for part in parts:
            node = node[part]

        def tree_to_string(tree, indent=0):
            s = ""
            for key, value in sorted(tree.items()):
                s += "    " * indent + key + "\n"
                if isinstance(value, dict):
                    s += tree_to_string(value, indent + 1)
            return s

        return tree_to_string(path_tree)
