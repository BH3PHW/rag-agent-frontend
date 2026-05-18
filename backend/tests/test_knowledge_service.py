"""
Knowledge Service 调试用例
===========================

测试覆盖：
1. 导入测试 - 验证模块可以正确导入
2. 知识库管理测试
3. 文档处理测试
4. 向量检索测试
"""

import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
BACKEND_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR / "knowledge-service"))


def test_imports():
    """测试Knowledge Service模块导入"""
    print("\n" + "="*60)
    print("测试 1: 模块导入")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    # 测试导入主模块
    try:
        from main import app
        print("✅ 成功导入 main 模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 main 模块失败: {e}")
        tests_failed += 1

    # 测试导入配置
    try:
        from config import settings
        print("✅ 成功导入 config 模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 config 模块失败: {e}")
        tests_failed += 1

    # 测试导入数据模型
    try:
        from models import KnowledgeBase, Document
        print("✅ 成功导入 models 模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 models 模块失败: {e}")
        tests_failed += 1

    # 测试导入向量存储
    try:
        from vector_store import get_vector_store
        print("✅ 成功导入 vector_store 模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 vector_store 模块失败: {e}")
        tests_failed += 1

    # 测试导入文本分块器
    try:
        from chunker import TextChunker, extract_text_from_file
        print("✅ 成功导入 chunker 模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 chunker 模块失败: {e}")
        tests_failed += 1

    print(f"\n导入测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def test_vector_store():
    """测试向量存储组件"""
    print("\n" + "="*60)
    print("测试 2: 向量存储组件")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    try:
        from vector_store import get_vector_store
        print("✅ 成功获取向量存储实例")
        tests_passed += 1

        # 测试向量存储方法
        vs = get_vector_store()
        print(f"✅ 向量存储类型: {type(vs).__name__}")

        # 检查必要的方法
        required_methods = ['add_chunks', 'similarity_search', 'delete_chunks']
        for method in required_methods:
            if hasattr(vs, method):
                print(f"✅ 包含必要方法: {method}")
                tests_passed += 1
            else:
                print(f"❌ 缺少必要方法: {method}")
                tests_failed += 1

    except Exception as e:
        print(f"❌ 向量存储测试失败: {e}")
        tests_failed += 1

    print(f"\n向量存储测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def test_chunker():
    """测试文本分块器"""
    print("\n" + "="*60)
    print("测试 3: 文本分块器")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    try:
        from chunker import TextChunker

        chunker = TextChunker()
        print("✅ 成功创建文本分块器")

        # 测试分块功能
        test_text = "这是一段测试文本。" * 100
        chunks = chunker.chunk_text(test_text, {"test": "metadata"})

        if chunks and len(chunks) > 0:
            print(f"✅ 分块成功，生成 {len(chunks)} 个块")
            tests_passed += 1
        else:
            print("❌ 分块失败")
            tests_failed += 1

        # 检查分块结构
        if chunks and len(chunks) > 0:
            first_chunk = chunks[0]
            if 'text' in first_chunk:
                print("✅ 分块包含文本内容")
                tests_passed += 1
            else:
                print("❌ 分块结构异常")
                tests_failed += 1

    except Exception as e:
        print(f"❌ 文本分块器测试失败: {e}")
        tests_failed += 1

    print(f"\n文本分块器测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def test_api_endpoints():
    """测试API端点"""
    print("\n" + "="*60)
    print("测试 4: API端点配置")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    try:
        from main import app

        # 获取所有路由
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', {'GET'})
                routes.append((methods, route.path))

        # 统计路由
        kb_routes = [r for r in routes if '/knowledge-bases' in r[1]]
        doc_routes = [r for r in routes if '/documents' in r[1]]
        retrieve_routes = [r for r in routes if '/retrieve' in r[1]]

        print(f"\n总路由数: {len(routes)}")
        print(f"知识库路由: {len(kb_routes)}")
        print(f"文档路由: {len(doc_routes)}")
        print(f"检索路由: {len(retrieve_routes)}")

        # 验证关键路由
        critical_routes = [
            '/health',
            '/api/v1/knowledge-bases',
            '/api/v1/knowledge-bases/{kb_id}/documents',
            '/api/v1/retrieve',
        ]

        existing_routes = [r[1] for r in routes]
        for route in critical_routes:
            if route in existing_routes:
                print(f"✅ 关键路由存在: {route}")
                tests_passed += 1
            else:
                print(f"❌ 关键路由缺失: {route}")
                tests_failed += 1

    except Exception as e:
        print(f"❌ API端点测试失败: {e}")
        tests_failed += 1

    print(f"\nAPI端点测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("#" + " "*10 + "Knowledge Service 测试套件" + " "*16 + "#")
    print("#"*60)

    results = {
        "imports": test_imports(),
        "vector": test_vector_store(),
        "chunker": test_chunker(),
        "endpoints": test_api_endpoints(),
    }

    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)

    all_passed = True
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name.upper():20} {status}")
        if not passed:
            all_passed = False

    print("="*60)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查上述错误")

    return all_passed


if __name__ == "__main__":
    run_all_tests()
