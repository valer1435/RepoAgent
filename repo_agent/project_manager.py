import os
import jedi

class ProjectManager:
    def __init__(self, repo_path, project_hierarchy):
        self.repo_path = repo_path
        self.project = jedi.Project(self.repo_path)
        self.project_hierarchy = os.path.join(self.repo_path, project_hierarchy, 'project_hierarchy.json')

    def get_project_structure(self):

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
