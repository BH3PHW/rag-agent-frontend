# 第4章：微服务通信与API网关

> 🎯 **学习目标**：理解微服务架构下的服务通信机制与API网关设计
> 💡 **工程化思维**：服务解耦、统一入口、限流保护
> 💡 **产品化思维**：高可用、性能优化、用户体验

---

## 12.1 为什么需要API网关？

### 12.1.1 微服务通信挑战

**产品化思维**：微服务架构的问题与解决方案

```
微服务架构问题：
┌─────────────────────────────────────────┐
│  1. 客户端复杂度 - 前端要对接多个后端    │
│  2. 跨域问题 - 不同服务域名不同          │
│  3. 认证分散 - 每个服务都要验证Token    │
│  4. 协议差异 - 各服务API格式不统一      │
│  5. 性能问题 - 客户端直连，延迟高        │
└─────────────────────────────────────────┘
         ↓
      API Gateway
         ↓
┌─────────────────────────────────────────┐
│  ✅ 统一入口 - 前端只需对接一个网关      │
│  ✅ 跨域解决 - 网关统一处理CORS          │
│  ✅ 认证统一 - Token验证在网关完成      │
│  ✅ 协议统一 - 统一的API规范            │
│  ✅ 性能优化 - 内网通信，延迟更低        │
└─────────────────────────────────────────┘
```

### 12.1.2 API网关核心职责

| 职责 | 说明 |
|------|------|
| **路由转发** | 将请求路由到对应的微服务 |
| **统一认证** | JWT Token验证和解析 |
| **限流保护** | 防止恶意请求影响系统 |
| **企业隔离** | 确保企业数据安全访问 |
| **日志监控** | 记录请求日志，便于分析 |

---

## 12.2 系统架构

### 12.2.1 服务拓扑

```
客户端请求流程：

Browser/APP
    ↓ HTTPS
API Gateway (8000)
    ↓ HTTP (内网)
    ├──→ User Service (8001)      # 用户认证、企业管理
    ├──→ Chat Service (8002)      # 智能对话、RAG检索
    ├──→ Knowledge Service (8003) # 知识库、文档管理
    ├──→ Alert Service (8004)     # 告警通知
    └──→ Channel Service (8005)   # 多渠道接入
```

### 12.2.2 网关配置

**工程化实现**：灵活的服务路由配置

```python
# 服务URL配置
SERVICES = {
    "user": "http://user-service:8001",
    "chat": "http://chat-service:8002",
    "knowledge": "http://knowledge-service:8003",
    "alert": "http://alert-service:8004",
    "channel": "http://channel-service:8005"
}

# 白名单路径（不需要认证）
WHITELIST_PATHS = {
    "/",              # 根路径
    "/health",        # 健康检查
    "/docs",          # API文档
    "/openapi.json"   # OpenAPI规范
}
```

---

## 12.3 请求转发核心实现

### 12.3.1 代理函数设计

**工程化实现**：统一的请求转发逻辑

```python
async def proxy_request(
    service: str,
    path: str,
    method: str = "GET",
    params: dict = None,
    json_data: dict = None,
    headers: dict = None
) -> dict:
    """
    核心请求转发函数

    产品化思维：
    - 统一错误处理
    - 超时保护
    - 日志记录
    """
    # 1. 拼接目标URL
    url = f"{SERVICES[service]}{path}"

    # 2. 使用异步HTTP客户端，设置30秒超时
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 3. 根据HTTP方法执行请求
            if method == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=json_data, params=params, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=json_data, params=params, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, params=params, headers=headers)

            # 4. 检查HTTP错误
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            # 后端服务返回错误状态码
            logger.error(f"HTTP error from {service}: {e.response.status_code}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.text
            )
        except httpx.RequestError as e:
            # 后端服务不可达
            logger.error(f"Service {service} unavailable: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Service {service} unavailable"
            )
```

### 12.3.2 流式响应处理

**产品化思维**：SSE流式输出的透明转发

```python
@app.post("/api/v1/chat/stream")
async def stream_chat_message(request: Request):
    """
    流式聊天 - 透明转发SSE响应

    产品化：打字机效果，提升用户体验
    """
    try:
        body = await request.json()
        message = body.get("message")
        enterprise_id = body.get("enterpriseId")

        # 转发到Chat Service
        async with httpx.AsyncClient(timeout=120.0) as client:
            chat_response = await client.post(
                f"{SERVICES['chat']}/api/v1/chat/stream",
                json={"message": message, "enterprise_id": enterprise_id},
                headers={"Authorization": request.headers.get("Authorization")}
            )

            # 透明转发SSE流
            return StreamingResponse(
                chat_response.aiter_text(),  # 流式迭代响应文本
                media_type="text/event-stream",
                headers={"X-Accel-Buffering": "no"}  # 禁用nginx缓冲
            )

    except Exception as e:
        logger.error(f"Stream chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 12.4 安全中间件

### 12.4.1 限流保护

**工程化设计**：基于Redis的分布式限流

```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    限流中间件

    规则：
    - 每个IP每分钟最多100次请求
    - 白名单路径跳过限流
    """
    path = request.url.path

    # 白名单直接放行
    if path in WHITELIST_PATHS:
        return await call_next(request)

    # 非API路径直接通过
    if not path.startswith("/api/"):
        return await call_next(request)

    # 获取客户端IP
    client_ip = request.client.host if request.client else "unknown"

    # 构建限流Redis键
    rate_key = f"rate:{client_ip}:{int(time.time() / 60)}"

    try:
        # 增加请求计数
        request_count = await redis_manager.incr(rate_key)

        # 首次请求设置60秒过期
        if request_count == 1:
            await redis_manager.expire(rate_key, 60)

        # 超过100次触发限流
        if request_count > 100:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )

    except Exception as e:
        logger.error(f"Rate limit error: {e}")
        # Redis出错时不影响请求

    return await call_next(request)
```

### 12.4.2 企业访问验证

**产品化思维**：数据安全的最后防线

```python
async def validate_enterprise_request(
    request: Request,
    enterprise_id: str
) -> str:
    """
    验证企业访问权限

    确保Token中的企业ID与请求目标一致
    防止跨企业数据访问
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    # 从Token中提取企业ID
    token_enterprise_id = extract_enterprise_id_from_token(token)
    if not token_enterprise_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 验证企业ID匹配
    if token_enterprise_id != enterprise_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied: enterprise mismatch"
        )

    return enterprise_id
```

---

## 12.5 微服务健康检查

### 12.5.1 网关健康检查

```python
@app.get("/health")
async def health_check():
    """
    健康检查端点

    用于：
    1. Kubernetes/负载均衡器检测服务状态
    2. 监控告警
    3. 运维人员检查
    """
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 12.5.2 下游服务健康检查

**工程化实践**：主动检测下游服务可用性

```python
async def check_services_health():
    """检查所有下游服务健康状态"""
    results = {}

    for service_name, service_url in SERVICES.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_url}/health")
                results[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                }
        except Exception:
            results[service_name] = {"status": "unreachable"}

    return results
```

---

## 12.6 日志与监控

### 12.6.1 请求日志

**工程化设计**：结构化日志便于分析

```python
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()

    # 记录请求
    logger.info(f"Request: {request.method} {request.url.path}")

    response = await call_next(request)

    # 记录响应
    duration = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Duration: {duration:.3f}s"
    )

    return response
```

### 12.6.2 性能指标

```python
class MetricsCollector:
    """性能指标收集"""

    def record_request(
        service: str,
        method: str,
        status_code: int,
        duration: float
    ):
        """记录请求指标"""
        metric = {
            "service": service,
            "method": method,
            "status": status_code,
            "duration": duration,
            "timestamp": time.time()
        }

        # 可以发送到Prometheus/InfluxDB等时序数据库
        send_to_prometheus(metric)

    def get_service_stats(service: str) -> dict:
        """获取服务统计"""
        return {
            "requests_total": get_total_requests(service),
            "requests_success": get_success_requests(service),
            "requests_failed": get_failed_requests(service),
            "avg_duration": get_avg_duration(service),
            "p99_duration": get_p99_duration(service)
        }
```

---

## 12.7 工程化最佳实践

### 12.7.1 错误处理策略

**产品化思维**：给用户友好的错误信息

```python
async def proxy_request(...):
    try:
        # 业务逻辑
    except httpx.HTTPStatusError as e:
        # 保留后端返回的错误信息
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text
        )
    except httpx.RequestError as e:
        # 服务不可用时，给出明确提示
        raise HTTPException(
            status_code=503,
            detail=f"服务 {service} 暂时不可用，请稍后再试"
        )
    except Exception as e:
        # 未知错误，记录并给用户通用提示
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请联系技术支持"
        )
```

### 12.7.2 超时配置

```python
# 不同场景使用不同超时时间
TIMEOUTS = {
    "default": 30.0,        # 普通API请求
    "long_running": 120.0,  # 流式响应、大文件上传
    "health_check": 5.0,   # 健康检查
    "quick": 10.0          # 简单查询
}

async def proxy_request_with_timeout(
    service: str,
    path: str,
    timeout: float = 30.0
):
    """带超时控制的请求转发"""
    async with httpx.AsyncClient(timeout=timeout) as client:
        # ...
```

---

## 12.8 产品化优化

### 12.8.1 API版本管理

```python
# API版本控制
API_VERSIONS = {
    "v1": {
        "prefix": "/api/v1",
        "status": "stable",
        "deprecation_date": None
    },
    "v2": {
        "prefix": "/api/v2",
        "status": "beta",
        "deprecation_date": "2025-06-01"
    }
}

@app.get("/api/versions")
async def get_api_versions():
    """返回支持的API版本"""
    return {
        "current_version": "v1",
        "supported_versions": list(API_VERSIONS.keys()),
        "versions": API_VERSIONS
    }
```

### 12.8.2 断路器模式

**工程化实践**：防止级联故障

```python
class CircuitBreaker:
    """断路器 - 服务熔断保护"""

    def __init__(self, service: str, failure_threshold: int = 5):
        self.service = service
        self.failure_threshold = failure_threshold
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED/OPEN/HALF_OPEN

    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            raise ServiceUnavailableError(self.service)

        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception:
            self.on_failure()
            raise

    def on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def on_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker OPEN for {self.service}")
```

---

## 12.9 本章小结

### 核心概念

| 概念 | 说明 |
|------|------|
| API网关 | 统一入口，处理横切关注点 |
| 请求转发 | 将客户端请求路由到微服务 |
| 限流保护 | 基于Redis的分布式限流 |
| 企业隔离 | Token验证 + 企业ID校验 |
| 断路器 | 防止级联故障 |

### 工程化思维要点

1. **统一入口** - 减少客户端复杂度
2. **错误处理** - 友好的错误信息
3. **超时控制** - 防止请求无限等待
4. **日志监控** - 结构化日志便于分析
5. **断路器** - 服务降级，防止级联故障

### 产品化思维要点

1. **性能优化** - 内网通信，降低延迟
2. **用户体验** - 流式响应，打字机效果
3. **高可用** - 健康检查，自动故障转移
4. **API版本** - 平滑升级，版本共存

### 下一步学习

接下来学习 [13_审计日志系统.md](file:///workspace/backend/learning/13_审计日志系统.md)，了解企业级安全审计的实现！
