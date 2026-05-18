# 后端测试指南

## 环境准备

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 启动 API Gateway
cd api-gateway
uvicorn main:app --reload --port 8080

# 或使用 Docker 启动所有服务
docker-compose up -d
```

## 测试脚本使用

### 运行所有后端测试

```bash
cd backend/tests

# 运行所有测试
python -m pytest -v

# 运行特定测试文件
python -m pytest test_api_gateway.py -v
python -m pytest test_chat_service.py -v
python -m pytest test_user_service.py -v
python -m pytest test_knowledge_service.py -v
```

### 调试服务

```bash
# 启动服务调试器
python debug_services.py
```

## API 测试

### API Gateway 端点测试

```bash
# 测试认证
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@company.com", "password": "password123"}'

# 测试聊天
curl -X POST http://localhost:8080/api/v1/chat/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message": "你好"}'
```

### 流式聊天测试

```bash
curl -X POST http://localhost:8080/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message": "详细介绍你们的AI客服"}'
```

## 测试覆盖

- 用户认证 (JWT)
- 企业管理
- 聊天服务 (RAG + LLM)
- 知识库管理
- 流式输出 (SSE)
- API 限流
- 安全防护
