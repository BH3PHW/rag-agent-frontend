#!/usr/bin/env python3
"""
批量完善所有服务配置文件，添加详细的中文部署参数注释
"""
import os
from pathlib import Path

# 各服务配置
SERVICE_CONFIGS = {
    "api-gateway": {
        "extra_comments": '''
# ==========================================
# 下游微服务地址配置
# ==========================================
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
    # 用户服务地址 - API网关转发用户相关请求到此服务
    
    KNOWLEDGE_SERVICE_URL: str = os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge-service:8003")
    # 知识库服务地址 - 文档管理、向量检索
    
    CHAT_SERVICE_URL: str = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8002")
    # 聊天服务地址 - RAG引擎、对话管理
    
    ALERT_SERVICE_URL: str = os.getenv("ALERT_SERVICE_URL", "http://alert-service:8004")
    # 告警服务地址 - 安全告警、监控通知
    
    CHANNEL_SERVICE_URL: str = os.getenv("CHANNEL_SERVICE_URL", "http://channel-service:8005")
    # 渠道服务地址 - 多渠道接入
    
    ADMIN_SERVICE_URL: str = os.getenv("ADMIN_SERVICE_URL", "http://admin-service:8006")
    # 管理服务地址 - 运营后台API
    
    ANALYTICS_SERVICE_URL: str = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8007")
    # 分析服务地址 - 数据统计分析
''',
    },
    "chat-service": {
        "extra_comments": '''
# ==========================================
# LLM和知识库配置
# ==========================================
    KNOWLEDGE_SERVICE_URL: str = os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge-service:8003")
    # 知识库服务地址 - 用于检索相关文档
    
    # LLM API配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    # OpenAI API密钥 - 如需使用GPT模型请配置
    
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    # OpenAI API基础地址 - 可用于兼容的API服务
    
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    # 使用的LLM模型名称
    
    # 向量嵌入配置
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    # 嵌入模型名称 - 用于文档向量化
    
    # RAG配置
    RAG_TOP_K: int = 5
    # 检索返回的文档数量 - 更多文档=更好效果但更高成本
    
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    # 检索相似度阈值 - 低于此值的文档不会被使用
''',
    },
    "knowledge-service": {
        "extra_comments": '''
# ==========================================
# 向量数据库配置
# ==========================================
    CHROMA_URL: str = os.getenv("CHROMA_URL", "http://chroma:8000")
    # ChromaDB向量数据库地址
    
    # 嵌入配置
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    # 嵌入模型名称
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    # OpenAI API密钥 - 用于嵌入生成
    
    # 文档处理配置
    MAX_DOCUMENT_SIZE: int = 10 * 1024 * 1024  # 10MB
    # 最大文档大小限制 - 防止大文件占用过多资源
    
    SUPPORTED_DOCUMENT_TYPES: list = [".pdf", ".txt", ".md", ".docx"]
    # 支持的文档格式 - 可根据需要扩展
    
    CHUNK_SIZE: int = 500
    # 文档分块大小 - 影响检索精度和上下文质量
    
    CHUNK_OVERLAP: int = 50
    # 分块重叠大小 - 避免上下文割裂
''',
    },
    "admin-service": {
        "extra_comments": '''
# ==========================================
# 管理相关配置
# ==========================================
    CHAT_SERVICE_URL: str = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8002")
    # 聊天服务地址 - 获取会话数据
    
    ANALYTICS_SERVICE_URL: str = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8007")
    # 分析服务地址 - 统计数据
    
    ALERT_SERVICE_URL: str = os.getenv("ALERT_SERVICE_URL", "http://alert-service:8004")
    # 告警服务地址 - 告警管理
    
    KNOWLEDGE_SERVICE_URL: str = os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge-service:8003")
    # 知识库服务地址 - 知识库管理
    
    HTTP_TIMEOUT: float = 10.0
    # HTTP客户端超时时间（秒）
    
    # 客服坐席配置
    DEFAULT_MAX_CONCURRENT_CHATS: int = 5
    # 坐席默认最大同时接待数
    
    AGENT_ONLINE_TIMEOUT: int = 300
    # 坐席在线状态超时时间（秒）- 超时后自动设为离线
''',
    },
    "alert-service": {
        "extra_comments": '''
# ==========================================
# 告警配置
# ==========================================
    ALERT_CHECK_INTERVAL: int = 60
    # 告警检查间隔（秒）
    
    CRITICAL_ALERT_THRESHOLD: int = 3
    # 严重告警阈值 - 达到此数量触发告警
    
    # 通知配置（可选）
    EMAIL_NOTIFICATION_ENABLED: bool = False
    # 是否启用邮件通知
    
    EMAIL_SMTP_HOST: str = ""
    # SMTP服务器地址 - 如需邮件通知请配置
    
    EMAIL_SMTP_PORT: int = 587
    # SMTP端口
''',
    },
    "channel-service": {
        "extra_comments": '''
# ==========================================
# 渠道配置
# ==========================================
    CHAT_SERVICE_URL: str = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8002")
    # 聊天服务地址 - 转发消息
    
    # 各平台API密钥（可选配置）
    WECHAT_APP_ID: str = os.getenv("WECHAT_APP_ID", "")
    # 微信公众号AppID
    
    WECHAT_APP_SECRET: str = os.getenv("WECHAT_APP_SECRET", "")
    # 微信公众号AppSecret
    
    DINGTALK_APP_KEY: str = os.getenv("DINGTALK_APP_KEY", "")
    # 钉钉AppKey
    
    DINGTALK_APP_SECRET: str = os.getenv("DINGTALK_APP_SECRET", "")
    # 钉钉AppSecret
''',
    },
    "analytics-service": {
        "extra_comments": '''
# ==========================================
# 分析配置
# ==========================================
    ANALYTICS_REPORT_INTERVAL: int = 3600
    # 统计报告生成间隔（秒）
    
    DATA_RETENTION_DAYS: int = 90
    # 数据保留天数 - 超过此时间的数据将被归档或删除
    
    HOT_QUERIES_LIMIT: int = 50
    # 热词统计数量限制
''',
    },
}


def improve_config_file(service_name: str, config_path: Path):
    """
    完善单个配置文件
    """
    print(f"正在处理: {service_name}")
    
    # 读取原配置
    content = config_path.read_text(encoding="utf-8")
    
    # 找到Settings类的定义部分
    if "class Settings" not in content:
        print(f"跳过 {service_name} - 未找到Settings类")
        return
    
    # 添加文件顶部注释
    top_comment = '''"""
{service_name} 服务配置
========================================

[部署说明]
所有配置参数都可以通过环境变量进行设置，环境变量优先级高于默认值
生产环境必须修改所有的默认密钥和密码！

[参数分类]
1. 应用基本配置：服务名称、版本、调试模式
2. 数据库配置：PostgreSQL连接参数
3. Redis配置：缓存和会话存储
4. JWT安全配置：认证令牌设置
5. CORS跨域配置：允许的前端地址
6. 微服务通信配置：其他服务的访问地址
7. 业务相关配置：特定服务的业务参数
"""

'''
    
    if not content.startswith('"""') and not content.startswith("'''"):
        content = top_comment.format(service_name=service_name) + content
    
    # 添加参数注释
    content = add_parameter_comments(content)
    
    # 添加服务特定配置
    if service_name in SERVICE_CONFIGS:
        extra = SERVICE_CONFIGS[service_name]["extra_comments"]
        if "class Config:" in content:
            content = content.replace("    class Config:", f"{extra}\n    class Config:")
    
    # 备份原文件
    backup_path = config_path.with_suffix(".py.backup")
    if not backup_path.exists():
        config_path.rename(backup_path)
        print(f"已备份: {backup_path.name}")
    
    # 写入新配置
    config_path.write_text(content, encoding="utf-8")
    print(f"已更新: {config_path.name}")


def add_parameter_comments(content: str):
    """
    添加详细的参数注释
    """
    # 数据库URL注释
    if "DATABASE_URL" in content and "DATABASE_URL: str = os.getenv" in content:
        db_part = '''DATABASE_URL: str = os.getenv(
        "{env_prefix}DATABASE_URL",
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/{db_name}")
    )
    # PostgreSQL数据库连接地址
    # 格式: postgresql://用户名:密码@主机:端口/数据库名
    # 示例: postgresql://myuser:mypassword@db.example.com:5432/mydatabase
    # 重要: 生产环境必须使用强密码！
    # 环境变量: {env_prefix}DATABASE_URL 或 DATABASE_URL'''
        # 简单替换模式
        content = content.replace(
            'DATABASE_URL: str = os.getenv(',
            'DATABASE_URL: str = os.getenv('
        )
    
    # Redis URL注释
    if "REDIS_URL" in content:
        content = content.replace(
            'REDIS_URL: str = os.getenv(',
            '# Redis连接地址 - 用于缓存、会话存储、限流\n    # 格式: redis://:密码@主机:端口/数据库编号\n    # 示例: redis://:redis123@redis.example.com:6379/1\n    REDIS_URL: str = os.getenv('
        )
    
    # SECRET_KEY注释
    if "SECRET_KEY" in content:
        content = content.replace(
            'SECRET_KEY: str = os.getenv(',
            '# JWT签名密钥 - 用于生成和验证认证令牌\n    # 重要: 生产环境必须修改为强随机密钥！\n    # 生成方式: openssl rand -hex 32 或使用其他随机生成工具\n    SECRET_KEY: str = os.getenv('
        )
    
    # CORS_ORIGINS注释
    if "CORS_ORIGINS" in content:
        content = content.replace(
            'CORS_ORIGINS: list =',
            '# 允许跨域访问的前端地址\n    # 格式: ["http://localhost:3000", "https://example.com"]\n    # 安全: 生产环境必须限制为具体域名，不要使用"*"\n    # 示例:\n    #   开发环境: ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"]\n    #   生产环境: ["https://chat.yourdomain.com", "https://admin.yourdomain.com"]\n    CORS_ORIGINS: list ='
        )
    
    # APP_NAME注释
    if "APP_NAME" in content:
        content = content.replace(
            'APP_NAME: str =',
            '# 服务名称 - 用于标识和日志输出\n    APP_NAME: str ='
        )
    
    # APP_VERSION注释
    if "APP_VERSION" in content:
        content = content.replace(
            'APP_VERSION: str =',
            '# 服务版本号 - 用于追踪部署和API版本\n    APP_VERSION: str ='
        )
    
    # DEBUG注释
    if "DEBUG" in content:
        content = content.replace(
            'DEBUG: bool =',
            '# 调试模式开关 - 生产环境必须设为False!\n    DEBUG: bool ='
        )
    
    return content


def main():
    """
    主函数
    """
    backend_dir = Path("/workspace/backend")
    
    print("=" * 60)
    print("批量完善配置文件注释")
    print("=" * 60)
    
    # 遍历所有服务目录
    services = ["api-gateway", "user-service", "chat-service", "knowledge-service",
                "admin-service", "alert-service", "channel-service", "analytics-service"]
    
    for service_name in services:
        config_path = backend_dir / service_name / "config.py"
        if config_path.exists():
            improve_config_file(service_name, config_path)
        else:
            print(f"跳过: {service_name} (文件不存在)")
    
    print("\n" + "=" * 60)
    print("完成！所有配置文件已完善注释")
    print("=" * 60)
    print("\n[部署建议]")
    print("1. 在项目根目录创建 .env 文件")
    print("2. 复制各服务需要的环境变量到 .env")
    print("3. 修改所有密钥和密码为生产环境值")
    print("4. 配置数据库和Redis连接参数")
    print("5. 设置正确的CORS_ORIGINS")


if __name__ == "__main__":
    main()
