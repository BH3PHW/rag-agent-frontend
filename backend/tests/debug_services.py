"""
后端服务调试脚本
==================

使用方法：
    python3 debug_services.py [服务名]

示例：
    python3 debug_services.py api-gateway  # 测试API Gateway
    python3 debug_services.py all          # 测试所有服务
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# 添加backend目录到Python路径
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))


class ServiceTester:
    """后端服务测试器"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.service_dir = BACKEND_DIR / service_name

    def test_imports(self) -> dict:
        """测试模块导入是否成功"""
        print(f"\n{'='*60}")
        print(f"测试 {self.service_name} - 模块导入检查")
        print('='*60)

        results = {
            "service": self.service_name,
            "imports": [],
            "errors": [],
            "success": True
        }

        try:
            # 测试导入主模块
            print(f"\n[1/3] 导入主模块...")
            module = __import__(self.service_name, fromlist=['main'])
            results["imports"].append({
                "module": f"{self.service_name}.main",
                "status": "success"
            })
            print(f"  ✅ 成功")

        except ImportError as e:
            results["errors"].append(f"ImportError: {str(e)}")
            results["success"] = False
            print(f"  ❌ 导入失败: {e}")

        except SyntaxError as e:
            results["errors"].append(f"SyntaxError: {str(e)}")
            results["success"] = False
            print(f"  ❌ 语法错误: {e}")

        except Exception as e:
            results["errors"].append(f"Error: {str(e)}")
            results["success"] = False
            print(f"  ❌ 其他错误: {e}")

        return results

    def test_config(self) -> dict:
        """测试配置文件"""
        print(f"\n[2/3] 测试配置文件...")
        results = {
            "config_file": None,
            "exists": False,
            "readable": False,
            "success": True
        }

        config_file = self.service_dir / "config.py"
        results["config_file"] = str(config_file)

        if config_file.exists():
            results["exists"] = True
            print(f"  ✅ 配置文件存在")

            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                    if content:
                        results["readable"] = True
                        print(f"  ✅ 配置文件可读")
            except Exception as e:
                results["success"] = False
                print(f"  ❌ 无法读取配置文件: {e}")
        else:
            results["success"] = False
            print(f"  ❌ 配置文件不存在")

        return results

    def test_database_models(self) -> dict:
        """测试数据库模型"""
        print(f"\n[3/3] 测试数据库模型...")
        results = {
            "models_file": None,
            "exists": False,
            "importable": False,
            "success": True
        }

        models_file = self.service_dir / "models.py"
        results["models_file"] = str(models_file)

        if models_file.exists():
            results["exists"] = True
            print(f"  ✅ models.py 存在")

            try:
                # 尝试导入模型
                import importlib.util
                spec = importlib.util.spec_from_file_location("models", models_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules['test_models'] = module
                    spec.loader.exec_module(module)
                    results["importable"] = True
                    print(f"  ✅ 模型可导入")
            except Exception as e:
                results["success"] = False
                print(f"  ⚠️  模型导入失败(可能是正常配置问题): {e}")
        else:
            print(f"  ℹ️  无 models.py 文件(可能不需要)")

        return results

    def run_all_tests(self) -> dict:
        """运行所有测试"""
        print(f"\n{'#'*60}")
        print(f"# 开始测试服务: {self.service_name}")
        print(f"# 服务目录: {self.service_dir}")
        print(f"{'#'*60}")

        results = {
            "service": self.service_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "import_test": None,
            "config_test": None,
            "models_test": None,
            "overall_success": True
        }

        # 测试导入
        results["import_test"] = self.test_imports()
        if not results["import_test"]["success"]:
            results["overall_success"] = False

        # 测试配置
        results["config_test"] = self.test_config()

        # 测试模型
        results["models_test"] = self.test_database_models()

        return results


def test_all_services():
    """测试所有后端服务"""
    services = [
        "api-gateway",
        "user-service",
        "chat-service",
        "knowledge-service",
        "alert-service",
        "channel-service"
    ]

    all_results = []

    print(f"\n{'='*60}")
    print(f"后端服务全面测试")
    print(f"{'='*60}\n")

    for service in services:
        service_dir = BACKEND_DIR / service
        if service_dir.exists():
            tester = ServiceTester(service)
            result = tester.run_all_tests()
            all_results.append(result)
        else:
            print(f"\n⚠️  服务目录不存在: {service}")

    # 汇总报告
    print(f"\n\n{'='*60}")
    print(f"测试汇总报告")
    print(f"{'='*60}")

    success_count = sum(1 for r in all_results if r["overall_success"])
    print(f"\n总服务数: {len(all_results)}")
    print(f"成功: {success_count}")
    print(f"失败: {len(all_results) - success_count}")

    for result in all_results:
        status = "✅" if result["overall_success"] else "❌"
        print(f"\n{status} {result['service']}")

    return all_results


def main():
    """主函数"""
    if len(sys.argv) > 1:
        service_name = sys.argv[1]

        if service_name == "all":
            test_all_services()
        else:
            tester = ServiceTester(service_name)
            tester.run_all_tests()
    else:
        print(__doc__)
        print("\n可用服务:")
        for d in BACKEND_DIR.iterdir():
            if d.is_dir() and (d / "main.py").exists():
                print(f"  - {d.name}")
        print("\n示例命令:")
        print("  python3 debug_services.py api-gateway")
        print("  python3 debug_services.py all")


if __name__ == "__main__":
    main()
