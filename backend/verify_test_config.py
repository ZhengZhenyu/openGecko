#!/usr/bin/env python3
"""
Pytest 配置验证脚本

运行这个脚本来验证 pytest 测试框架的所有配置是否正确设置。

使用方法：
    python verify_test_config.py

返回值：
    0 - 所有检查通过
    1 - 有检查失败
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
import importlib.util


# 颜色输出支持
class Colors:
    """终端颜色代码"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(message: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✓{Colors.END} {message}")


def print_error(message: str):
    """打印错误消息"""
    print(f"{Colors.RED}✗{Colors.END} {message}")


def print_warning(message: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")


def print_info(message: str):
    """打印信息消息"""
    print(f"{Colors.BLUE}ℹ{Colors.END} {message}")


def print_header(message: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{message}{Colors.END}")


class TestConfigValidator:
    """测试配置验证器"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.passed_checks = 0
        self.failed_checks = 0
        self.warnings = 0

    def check_file_exists(self, file_path: Path, description: str) -> bool:
        """检查文件是否存在"""
        if file_path.exists():
            print_success(f"{description}: {file_path.name}")
            self.passed_checks += 1
            return True
        else:
            print_error(f"{description}: {file_path.name} 不存在")
            self.failed_checks += 1
            return False

    def check_pytest_ini(self) -> bool:
        """检查 pytest.ini 配置"""
        print_header("1. 检查 pytest.ini 配置")

        pytest_ini = self.project_root / "pytest.ini"
        if not self.check_file_exists(pytest_ini, "pytest.ini 文件"):
            return False

        content = pytest_ini.read_text()

        # 检查必需的配置项
        checks = [
            ("testpaths", "测试目录配置"),
            ("python_files", "测试文件模式"),
            ("python_classes", "测试类模式"),
            ("python_functions", "测试函数模式"),
            ("asyncio_mode", "异步测试模式"),
            ("asyncio_default_fixture_loop_scope", "异步 fixture 作用域"),
            ("--cov=app", "覆盖率配置"),
            ("--cov-report=", "覆盖率报告"),
            ("--cov-branch", "分支覆盖率"),
            ("fail_under = 80", "最低覆盖率要求 (80%)"),
        ]

        for config_key, description in checks:
            if config_key in content:
                print_success(f"{description}: 已配置")
                self.passed_checks += 1
            else:
                print_error(f"{description}: 未配置")
                self.failed_checks += 1

        return True

    def check_pyproject_toml(self) -> bool:
        """检查 pyproject.toml 配置"""
        print_header("2. 检查 pyproject.toml 配置")

        pyproject = self.project_root / "pyproject.toml"
        if not self.check_file_exists(pyproject, "pyproject.toml 文件"):
            return False

        content = pyproject.read_text()

        # 检查必需的配置项
        checks = [
            ("[tool.pytest.ini_options]", "pytest 配置节"),
            ("asyncio_mode", "异步测试模式"),
            ("asyncio_default_fixture_loop_scope", "异步 fixture 作用域"),
            ("[tool.coverage.run]", "覆盖率运行配置"),
            ("[tool.coverage.report]", "覆盖率报告配置"),
            ("fail_under = 80", "最低覆盖率要求 (80%)"),
        ]

        for config_key, description in checks:
            if config_key in content:
                print_success(f"{description}: 已配置")
                self.passed_checks += 1
            else:
                print_error(f"{description}: 未配置")
                self.failed_checks += 1

        return True

    def check_dependencies(self) -> bool:
        """检查测试依赖是否安装"""
        print_header("3. 检查测试依赖")

        required_packages = [
            ("pytest", "Pytest 测试框架"),
            ("pytest_asyncio", "pytest-asyncio 异步测试支持"),
            ("pytest_cov", "pytest-cov 覆盖率插件"),
            ("fastapi.testclient", "FastAPI TestClient"),
            ("sqlalchemy", "SQLAlchemy ORM"),
        ]

        for package_name, description in required_packages:
            try:
                spec = importlib.util.find_spec(package_name)
                if spec is not None:
                    print_success(f"{description}: 已安装")
                    self.passed_checks += 1
                else:
                    print_error(f"{description}: 未安装")
                    self.failed_checks += 1
            except (ImportError, ModuleNotFoundError):
                print_error(f"{description}: 未安装")
                self.failed_checks += 1

        return True

    def check_conftest(self) -> bool:
        """检查 conftest.py 文件和 fixtures"""
        print_header("4. 检查 conftest.py 和 fixtures")

        conftest = self.project_root / "tests" / "conftest.py"
        if not self.check_file_exists(conftest, "conftest.py 文件"):
            return False

        content = conftest.read_text()

        # 检查必需的 fixtures
        required_fixtures = [
            ("test_db_file", "临时数据库文件 fixture"),
            ("test_engine", "数据库引擎 fixture"),
            ("db_session", "数据库会话 fixture"),
            ("client", "FastAPI TestClient fixture"),
            ("test_user", "测试用户 fixture"),
            ("test_superuser", "超级用户 fixture"),
            ("test_community", "测试社区 fixture"),
            ("auth_headers", "认证头 fixture"),
            ("superuser_auth_headers", "超级用户认证头 fixture"),
            ("user_token", "用户 token fixture"),
            ("superuser_token", "超级用户 token fixture"),
        ]

        for fixture_name, description in required_fixtures:
            if f"def {fixture_name}" in content:
                print_success(f"{description}: 已定义")
                self.passed_checks += 1
            else:
                print_error(f"{description}: 未定义")
                self.failed_checks += 1

        return True

    def check_test_directory(self) -> bool:
        """检查测试目录结构"""
        print_header("5. 检查测试目录结构")

        tests_dir = self.project_root / "tests"
        if not tests_dir.exists():
            print_error("tests 目录不存在")
            self.failed_checks += 1
            return False

        print_success("tests 目录存在")
        self.passed_checks += 1

        # 检查测试文件
        test_files = list(tests_dir.glob("test_*.py"))
        if test_files:
            print_success(f"找到 {len(test_files)} 个测试文件")
            self.passed_checks += 1

            for test_file in test_files[:5]:  # 只显示前 5 个
                print_info(f"  - {test_file.name}")

            if len(test_files) > 5:
                print_info(f"  ... 还有 {len(test_files) - 5} 个测试文件")
        else:
            print_warning("没有找到测试文件 (test_*.py)")
            self.warnings += 1

        return True

    def check_pytest_markers(self) -> bool:
        """检查 pytest 标记配置"""
        print_header("6. 检查 pytest 标记配置")

        pytest_ini = self.project_root / "pytest.ini"
        if not pytest_ini.exists():
            print_error("pytest.ini 不存在，无法检查标记")
            self.failed_checks += 1
            return False

        content = pytest_ini.read_text()

        # 检查标记定义
        expected_markers = [
            "slow",
            "integration",
            "unit",
            "api",
            "auth",
            "community",
            "content",
            "publish",
            "analytics",
        ]

        markers_section = "markers =" in content or "[markers]" in content
        if not markers_section:
            print_warning("未找到标记配置节")
            self.warnings += 1
            return False

        for marker in expected_markers:
            if marker in content:
                print_success(f"标记 '{marker}': 已定义")
                self.passed_checks += 1
            else:
                print_warning(f"标记 '{marker}': 未定义（可选）")
                self.warnings += 1

        return True

    def check_coverage_config(self) -> bool:
        """检查覆盖率配置"""
        print_header("7. 检查覆盖率配置")

        pytest_ini = self.project_root / "pytest.ini"
        if not pytest_ini.exists():
            print_error("pytest.ini 不存在")
            self.failed_checks += 1
            return False

        content = pytest_ini.read_text()

        # 检查覆盖率配置
        checks = [
            ("[coverage:run]", "覆盖率运行配置节"),
            ("source = app", "覆盖率源目录"),
            ("omit =", "覆盖率排除配置"),
            ("[coverage:report]", "覆盖率报告配置节"),
            ("fail_under = 80", "最低覆盖率要求 (80%)"),
            ("show_missing = True", "显示未覆盖行"),
            ("[coverage:html]", "HTML 报告配置节"),
            ("directory = htmlcov", "HTML 报告目录"),
        ]

        for config_key, description in checks:
            if config_key in content:
                print_success(f"{description}: 已配置")
                self.passed_checks += 1
            else:
                print_error(f"{description}: 未配置")
                self.failed_checks += 1

        return True

    def check_asyncio_config(self) -> bool:
        """检查 pytest-asyncio 配置"""
        print_header("8. 检查 pytest-asyncio 配置")

        pytest_ini = self.project_root / "pytest.ini"
        if not pytest_ini.exists():
            print_error("pytest.ini 不存在")
            self.failed_checks += 1
            return False

        content = pytest_ini.read_text()

        # 检查 asyncio 配置
        if "asyncio_mode" in content:
            if "asyncio_mode = auto" in content:
                print_success("asyncio_mode: 设置为 auto (推荐)")
                self.passed_checks += 1
            else:
                print_warning("asyncio_mode: 已设置但不是 auto")
                self.warnings += 1
        else:
            print_error("asyncio_mode: 未配置")
            self.failed_checks += 1

        if "asyncio_default_fixture_loop_scope" in content:
            if "asyncio_default_fixture_loop_scope = function" in content:
                print_success("asyncio_default_fixture_loop_scope: 设置为 function")
                self.passed_checks += 1
            else:
                print_warning("asyncio_default_fixture_loop_scope: 已设置但不是 function")
                self.warnings += 1
        else:
            print_error("asyncio_default_fixture_loop_scope: 未配置")
            self.failed_checks += 1

        return True

    def check_requirements_dev(self) -> bool:
        """检查 requirements-dev.txt"""
        print_header("9. 检查 requirements-dev.txt")

        req_dev = self.project_root / "requirements-dev.txt"
        if not self.check_file_exists(req_dev, "requirements-dev.txt 文件"):
            return False

        content = req_dev.read_text()

        # 检查必需的依赖
        required_deps = [
            ("pytest", "Pytest"),
            ("pytest-asyncio", "pytest-asyncio"),
            ("pytest-cov", "pytest-cov"),
        ]

        for dep_name, description in required_deps:
            if dep_name in content:
                print_success(f"{description}: 已列出")
                self.passed_checks += 1
            else:
                print_error(f"{description}: 未列出")
                self.failed_checks += 1

        return True

    def run_simple_test(self) -> bool:
        """尝试运行一个简单的测试"""
        print_header("10. 运行简单测试验证")

        try:
            import subprocess
            result = subprocess.run(
                ["python", "-m", "pytest", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                print_success(f"pytest 可以正常运行: {version}")
                self.passed_checks += 1
                return True
            else:
                print_error("pytest 运行失败")
                self.failed_checks += 1
                return False
        except Exception as e:
            print_error(f"无法运行 pytest: {e}")
            self.failed_checks += 1
            return False

    def print_summary(self):
        """打印总结"""
        print_header("验证总结")

        total_checks = self.passed_checks + self.failed_checks
        pass_rate = (self.passed_checks / total_checks * 100) if total_checks > 0 else 0

        print(f"\n通过的检查: {Colors.GREEN}{self.passed_checks}{Colors.END}")
        print(f"失败的检查: {Colors.RED}{self.failed_checks}{Colors.END}")
        print(f"警告: {Colors.YELLOW}{self.warnings}{Colors.END}")
        print(f"通过率: {Colors.BOLD}{pass_rate:.1f}%{Colors.END}\n")

        if self.failed_checks == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ 所有配置检查通过！{Colors.END}")
            print(f"\n{Colors.BLUE}可以开始运行测试了：{Colors.END}")
            print(f"  cd backend")
            print(f"  pytest")
            return 0
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ 有 {self.failed_checks} 个配置问题需要解决{Colors.END}")
            print(f"\n{Colors.BLUE}请检查上述失败的项目并修复配置。{Colors.END}")
            return 1

    def run_all_checks(self) -> int:
        """运行所有检查"""
        print(f"{Colors.BOLD}{'=' * 70}{Colors.END}")
        print(f"{Colors.BOLD}Pytest 测试配置验证{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 70}{Colors.END}")

        # 运行所有检查
        self.check_pytest_ini()
        self.check_pyproject_toml()
        self.check_dependencies()
        self.check_conftest()
        self.check_test_directory()
        self.check_pytest_markers()
        self.check_coverage_config()
        self.check_asyncio_config()
        self.check_requirements_dev()
        self.run_simple_test()

        # 打印总结
        return self.print_summary()


def main():
    """主函数"""
    validator = TestConfigValidator()
    exit_code = validator.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
