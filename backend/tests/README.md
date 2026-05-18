"""
后端服务测试用例执行指南
=========================

本文档说明了如何运行后端服务的测试用例

## 测试文件列表

1. `debug_services.py` - 通用服务调试器
   - 可以测试所有后端微服务
   - 检查模块导入、配置文件、数据库模型

2. `test_api_gateway.py` - API Gateway 测试
   - 模块导入测试
   - API路由配置测试
   - 中间件配置测试

3. `test_user_service.py` - 用户服务测试
   - 认证功能测试（密码哈希、JWT Token）
   - 数据模型测试
   - API端点测试

4. `test_chat_service.py` - 聊天服务测试
   - RAG组件测试
   - SSE流式输出测试
   - API端点测试

5. `test_knowledge_service.py` - 知识库服务测试
   - 向量存储组件测试
   - 文本分块器测试
   - API端点测试

## 环境准备

### 1. 安装Python依赖

建议使用虚拟环境：

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装核心依赖
pip install fastapi
pip install uvicorn
pip install sqlalchemy
pip install pydantic
pip install pydantic-settings
pip install python-jose
pip install passlib
pip install bcrypt
pip install httpx
pip install redis
pip install python-multipart
```

### 2. 使用Docker安装依赖（推荐）

```bash
# 在Docker容器中运行
docker-compose run --rm api-gateway bash
```

## 运行测试

### 方式一：使用调试脚本测试所有服务

```bash
cd backend/tests
python3 debug_services.py all
```

### 方式二：测试单个服务

```bash
# 测试API Gateway
python3 debug_services.py api-gateway

# 测试用户服务
python3 debug_services.py user-service

# 测试聊天服务
python3 debug_services.py chat-service

# 测试知识库服务
python3 debug_services.py knowledge-service
```

### 方式三：运行详细测试

```bash
# 测试API Gateway详细功能
python3 test_api_gateway.py

# 测试用户服务详细功能
python3 test_user_service.py

# 测试聊天服务详细功能
python3 test_chat_service.py

# 测试知识库服务详细功能
python3 test_knowledge_service.py
```

## 测试结果解读

### 成功结果示例

```
============================================================
测试 1: 模块导入
============================================================
✅ 成功导入 main 模块
✅ 成功导入 config 模块
✅ 成功导入 security 模块
✅ 成功导入 redis_client 模块

导入测试结果: ✅ 4 通过, ❌ 0 失败
```

### 失败结果示例

```
============================================================
测试 1: 模块导入
============================================================
❌ 导入 main 模块失败: No module named 'fastapi'

导入测试结果: ✅ 0 通过, ❌ 4 失败
```

失败原因：
- `No module named 'fastapi'` - 需要安装FastAPI
- `No module named 'sqlalchemy'` - 需要安装SQLAlchemy
- `No module named 'pydantic'` - 需要安装Pydantic

## 常见问题

### Q1: 测试显示"No module named 'xxx'"

**A:** 这是因为依赖未安装。请运行：

```bash
pip install fastapi uvicorn sqlalchemy pydantic
```

### Q2: 测试配置文件读取失败

**A:** 检查配置文件是否存在：

```bash
ls -la backend/api-gateway/
```

### Q3: 数据库连接失败

**A:** 确保PostgreSQL和Redis服务正在运行：

```bash
# 使用Docker启动数据库
docker-compose up -d postgres redis

# 或者本地启动
pg_ctl -D /usr/local/var/postgres start
redis-server
```

## 持续集成

在CI/CD流程中运行测试：

```yaml
# .github/workflows/test.yml 示例
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install fastapi uvicorn sqlalchemy pydantic
          pip install -r backend/requirements.txt

      - name: Run tests
        run: |
          cd backend/tests
          python3 debug_services.py all
```

## 测试覆盖范围

| 服务 | 测试项 | 状态 |
|------|--------|------|
| API Gateway | 模块导入 | ✅ |
| API Gateway | 路由配置 | ✅ |
| API Gateway | 中间件 | ✅ |
| User Service | 认证功能 | ✅ |
| User Service | 数据模型 | ✅ |
| Chat Service | RAG组件 | ✅ |
| Chat Service | SSE流式 | ✅ |
| Knowledge Service | 向量存储 | ✅ |
| Knowledge Service | 文本分块 | ✅ |

## 添加新测试

如需添加新的测试用例：

1. 在 `tests/` 目录下创建新文件
2. 遵循命名规范：`test_<服务名>.py`
3. 包含测试函数：
   - `test_imports()` - 模块导入测试
   - `test_<功能>()` - 功能测试
   - `run_all_tests()` - 运行所有测试

4. 在测试文件开头添加说明：

```python
"""
<服务名> 测试用例
================

测试覆盖：
1. ...
2. ...
"""
```

## 联系方式

如有问题，请联系开发团队或提交Issue。

作者：RAG客服系统开发团队
版本：1.0.0
更新日期：2026-05-18
"""

# 使用说明示例
if __name__ == "__main__":
    print(__doc__)
