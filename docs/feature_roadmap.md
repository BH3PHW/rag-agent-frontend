# RAG 智能客服系统功能迭代规划

## 项目概述

本文档描述 RAG 智能客服系统的功能迭代规划，包含四大维度：数据洞察与运营后台、RAG 核心能力增强、渠道接入与生态、运维与成本控制。

---

## 维度一：数据洞察与运营后台

### 1.1 可视化运营管理后台

**目标**：提供完整的 Admin Dashboard，降低使用门槛

**功能模块**：
- 告警中心：查看和处理敏感问题告警
- 知识库管理：文档上传、编辑、删除
- 人工介入：手动回复用户消息
- 客服工作台：实时会话监控

**实现方式**：
- 创建独立的 admin-service 微服务
- 提供 WebSocket 实时通知
- RESTful API + React 前端

### 1.2 问答质量分析与埋点

**功能点**：

1. **点赞/点踩机制**
   - 用户可以对 AI 回复进行评价
   - 点"踩"时必须填写原因
   - 收集负面反馈用于优化

2. **热词统计**
   - 统计 Top 10 高频问题
   - 识别 AI 无法回答的问题
   - 生成知识库补充建议

3. **未命中日志**
   - 记录检索相似度 < 阈值的问题
   - 标记需要补充到知识库的问题
   - 提供导出和批量处理功能

### 1.3 对话历史与会话存档

**功能点**：
- 完整聊天记录持久化存储
- 支持按时间、用户、关键词检索
- 会话存档与导出（CSV/JSON）
- 用于纠纷复盘和质检

---

## 维度二：RAG 核心能力增强

### 2.1 常见问题 (FAQ) 强匹配模式

**架构设计**：
```
用户问题
    ↓
意图路由层
    ↓
┌─────────┬──────────┐
↓         ↓          ↓
FAQ匹配  规则引擎   RAG检索
    ↓         ↓          ↓
    └────┬────┘
         ↓
    返回答案
```

**FAQ 表设计**：
```sql
CREATE TABLE faqs (
    id UUID PRIMARY KEY,
    enterprise_id UUID NOT NULL,
    knowledge_base_id UUID,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    keywords TEXT[],  -- 关键词列表，用于精确匹配
    category VARCHAR(50),
    priority INT DEFAULT 0,  -- 优先级，越高越先匹配
    hit_count INT DEFAULT 0,  -- 命中次数
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 2.2 多模态文档解析

**支持的格式**：
- PDF 文档（支持表格提取）
- 图片 OCR（PaddleOCR）
- Word/Excel 表格
- 扫描件处理

**技术选型**：
- PaddleOCR：中文 OCR 识别
- Camelot/Tabula：PDF 表格提取
- python-docx：Word 文档解析

### 2.3 引用来源溯源

**实现方式**：
- 在返回答案时附带引用信息
- 格式：`[来源1] 《文档名》P.xx`
- 支持点击跳转到原文位置

**数据格式**：
```json
{
  "answer": "根据《产品手册》P.15，产品的保修期为...",
  "sources": [
    {
      "document_id": "xxx",
      "document_name": "产品手册.pdf",
      "page": 15,
      "chunk_id": "xxx",
      "excerpt": "产品的保修期为一年..."
    }
  ]
}
```

---

## 维度三：渠道接入与生态

### 3.1 多渠道适配器

**支持的渠道**：
1. Web Widget SDK（网页悬浮窗）
2. 微信公众号/小程序
3. 钉钉机器人
4. 飞书机器人

**架构设计**：
```
┌──────────────┐
│ 渠道适配层   │
├──────────────┤
│ Web Widget   │
│ WeChat       │
│ DingTalk     │
│ Feishu       │
└──────┬───────┘
       ↓
┌──────────────┐
│ 消息路由层   │
│ (统一格式)   │
└──────────────┘
       ↓
┌──────────────┐
│ Chat Service │
└──────────────┘
```

### 3.2 API 密钥管理与限流

**功能点**：
- 多租户 API Key 管理
- 自定义调用频率限制
- 用量统计与计费
- 开发者 Portal

---

## 维度四：运维与成本控制

### 4.1 意图识别与路由

**路由策略**：
1. **规则匹配**（零成本）
   - 寒暄语：你好、谢谢、再见
   - 订单查询：订单号、发货
   - 固定问答：FAQ 表

2. **小模型分类**（低成本）
   - 使用轻量级模型（如 100M 参数）
   - 预训练意图分类器

3. **大模型生成**（高成本）
   - 仅复杂问题时调用 Qwen
   - 启用 RAG 增强

**成本优化预期**：
- 30%-50% Token 节省
- 响应延迟降低

### 4.2 知识库版本控制

**功能点**：
- 文档版本历史
- 一键回滚
- 版本对比
- 快照管理

**表设计**：
```sql
-- 知识库快照
CREATE TABLE kb_snapshots (
    id UUID PRIMARY KEY,
    knowledge_base_id UUID,
    enterprise_id UUID,
    snapshot_name VARCHAR(200),
    description TEXT,
    document_count INT,
    created_at TIMESTAMP,
    created_by UUID
);

-- 文档版本
CREATE TABLE document_versions (
    id UUID PRIMARY KEY,
    document_id UUID,
    version INT,
    file_path VARCHAR(500),
    file_hash VARCHAR(64),
    created_at TIMESTAMP,
    created_by UUID
);
```

---

## 数据库模型扩展

### 新增表结构

1. **analytics_messages** - 消息反馈与评分
2. **analytics_queries** - 查询埋点
3. **faqs** - 常见问题库
4. **faq_keywords** - FAQ 关键词
5. **kb_snapshots** - 知识库快照
6. **document_versions** - 文档版本
7. **channel_configs** - 渠道配置
8. **api_keys** - API 密钥管理
9. **intent_rules** - 意图路由规则
10. **conversation_archive** - 会话存档

---

## 实施优先级

### 第一阶段（高优先级）
1. ✅ 维度一：数据库模型扩展
2. ✅ 维度一：反馈与埋点 API
3. ✅ 维度二：FAQ 强匹配
4. ✅ 维度二：引用来源溯源

### 第二阶段（中优先级）
5. 维度三：Web Widget SDK
6. 维度三：API 密钥管理
7. 维度一：会话存档

### 第三阶段（后续迭代）
8. 维度二：多模态文档解析
9. 维度四：意图路由
10. 维度一：Admin Dashboard

---

## 技术栈更新

### 新增依赖
- **PaddleOCR**：多模态文档解析
- **transformers**：轻量级意图分类
- **WebSocket**：实时通知
- **SQLAlchemy**：数据库迁移

### 前端技术
- **React 18** + TypeScript
- **Ant Design**：UI 组件库
- **ECharts**：数据可视化
- **Socket.io**：实时通信

---

## 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                      Docker Compose                      │
├─────────────────────────────────────────────────────────┤
│  API Gateway (8080)                                     │
│  ├── User Service (8001)                                │
│  ├── Knowledge Service (8002)                            │
│  ├── Chat Service (8003)                                 │
│  ├── Alert Service (8004)                                │
│  ├── Analytics Service (8006)  ← NEW                     │
│  ├── Admin Service (8007)      ← NEW                     │
│  └── Channel Adapter (8008)   ← NEW                     │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL │ Redis │ ChromaDB │ PaddleOCR Container    │
└─────────────────────────────────────────────────────────┘
```

---

## 成功指标

1. **维度一**：反馈收集率 > 5%
2. **维度二**：FAQ 命中率 > 30%，答案准确率 > 90%
3. **维度三**：支持 4+ 渠道接入
4. **维度四**：Token 成本降低 30%+

---

*文档版本：1.0*
*最后更新：2024-01-15*
