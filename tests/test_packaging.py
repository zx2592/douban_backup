"""确保根目录的每个模块都登记进了 pyproject 的 py-modules。

模块平铺在仓库根目录，打包时是逐个列出的（自动发现会把 tests 也当成包）。
新增模块时很容易忘了这一步：源码运行和测试都照常通过，只有装完 wheel
再跑控制台命令才会炸 ModuleNotFoundError——CI 的 package job 正是这么
红的。这里在离线测试里就把它拦住。

不用 tomllib：CI 矩阵含 Python 3.8，那时还没有这个模块。
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# 不参与打包的根目录脚本（目前没有，留着说明意图）。
NOT_PACKAGED = set()


def declared_py_modules():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"^py-modules\s*=\s*\[(.*?)\]", text, re.S | re.M)
    assert match, "pyproject.toml 里找不到 py-modules"
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def source_modules():
    return {
        path.stem
        for path in REPO_ROOT.glob("*.py")
        if not path.stem.startswith("_")
    } - NOT_PACKAGED


class PackagingTests(unittest.TestCase):
    def test_every_root_module_is_packaged(self):
        missing = sorted(source_modules() - declared_py_modules())
        self.assertEqual(
            missing,
            [],
            f"这些模块没写进 pyproject.toml 的 py-modules，装成 wheel 后会缺失: {missing}",
        )

    def test_no_stale_entries(self):
        stale = sorted(declared_py_modules() - source_modules())
        self.assertEqual(
            stale, [], f"py-modules 里列了不存在的模块: {stale}"
        )


if __name__ == "__main__":
    unittest.main()
