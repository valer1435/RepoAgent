import os
import unittest

from git import Repo

from repo_agent.change_detector import ChangeDetector


class TestChangeDetector(unittest.TestCase):
    """
    Detects changes in a git repository, specifically focusing on Python and Markdown files.

    This class provides methods to identify staged, unstaged, and modified files
    within a Git repository. It's designed for use in testing or automation where
    tracking file changes is necessary.
    """

    @classmethod
    def setUpClass(cls):
        """
        Sets up the test repository for testing.

        """

        # 定义测试仓库的路径
        cls.test_repo_path = os.path.join(os.path.dirname(__file__), "test_repo")

        # 如果测试仓库文件夹不存在，则创建它
        if not os.path.exists(cls.test_repo_path):
            os.makedirs(cls.test_repo_path)

        # 初始化 Git 仓库
        cls.repo = Repo.init(cls.test_repo_path)

        # 配置 Git 用户信息
        cls.repo.git.config("user.email", "ci@example.com")
        cls.repo.git.config("user.name", "CI User")

        # 创建一些测试文件
        with open(os.path.join(cls.test_repo_path, "test_file.py"), "w") as f:
            f.write('print("Hello, Python")')

        with open(os.path.join(cls.test_repo_path, "test_file.md"), "w") as f:
            f.write("# Hello, Markdown")

        # 模拟 Git 操作：添加和提交文件
        cls.repo.git.add(A=True)
        cls.repo.git.commit("-m", "Initial commit")

    def test_get_staged_pys(self):
        """
        Tests that a newly created and staged Python file is correctly identified as staged.

        This test creates a new Python file, stages it using git add, and then
        uses ChangeDetector to verify that the new file is included in the list
        of staged Python files.

        Args:
            None

        Returns:
            None


        """

        # 创建一个新的 Python 文件并暂存
        new_py_file = os.path.join(self.test_repo_path, "new_test_file.py")
        with open(new_py_file, "w") as f:
            f.write('print("New Python File")')
        self.repo.git.add(new_py_file)

        # 使用 ChangeDetector 检查暂存文件
        change_detector = ChangeDetector(self.test_repo_path)
        staged_files = change_detector.get_staged_pys()

        # 断言新文件在暂存文件列表中
        self.assertIn(
            "new_test_file.py", [os.path.basename(path) for path in staged_files]
        )

        print(f"\ntest_get_staged_pys: Staged Python files: {staged_files}")

    def test_get_unstaged_mds(self):
        """
        Tests that a modified Markdown file is correctly identified as unstaged and appears in the list of files to be staged.

        This test creates a modified Markdown file, then uses ChangeDetector to
        identify it as an unstaged file. It asserts that the modified file is
        present in the list of unstaged files returned by get_to_be_staged_files().

        Args:
            None

        Returns:
            None


        """

        # 修改一个 Markdown 文件但不暂存
        md_file = os.path.join(self.test_repo_path, "test_file.md")
        with open(md_file, "a") as f:
            f.write("\nAdditional Markdown content")

        # 使用 ChangeDetector 获取未暂存的 Markdown 文件
        change_detector = ChangeDetector(self.test_repo_path)
        unstaged_files = change_detector.get_to_be_staged_files()

        # 断言修改的文件在未暂存文件列表中
        self.assertIn(
            "test_file.md", [os.path.basename(path) for path in unstaged_files]
        )

        print(f"\ntest_get_unstaged_mds: Unstaged Markdown files: {unstaged_files}")

    def test_add_unstaged_mds(self):
        """
        Verifies that running `add_unstaged_files` correctly stages previously unstaged Markdown files, leaving no remaining unstaged Markdown files.

        This method adds all unstaged markdown files in the repository and
        asserts that there are no remaining unstaged markdown files after the add operation.

        Args:
            None

        Returns:
            None


        """

        # 确保有一个未暂存的 Markdown 文件
        self.test_get_unstaged_mds()

        # 使用 ChangeDetector 添加未暂存的 Markdown 文件
        change_detector = ChangeDetector(self.test_repo_path)
        change_detector.add_unstaged_files()

        # 检查文件是否被暂存
        unstaged_files_after_add = change_detector.get_to_be_staged_files()

        # 断言暂存操作后没有未暂存的 Markdown 文件
        self.assertEqual(len(unstaged_files_after_add), 0)

        remaining_unstaged_files = len(unstaged_files_after_add)
        print(
            f"\ntest_add_unstaged_mds: Number of remaining unstaged Markdown files after add: {remaining_unstaged_files}"
        )

    @classmethod
    def tearDownClass(cls):
        """
        Cleans up any resources used by the test suite after all tests have completed.

        Args:
            cls: The class being torn down.

        Returns:
            None

        """

        # 清理测试仓库
        cls.repo.close()
        os.system("rm -rf " + cls.test_repo_path)


if __name__ == "__main__":
    unittest.main()
