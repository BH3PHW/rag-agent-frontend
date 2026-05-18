# GitHub 提交和推送指南

## 📋 提交前的准备工作

### 1. 检查 Git 状态
```bash
cd /workspace
git status
```

### 2. 查看变更
```bash
git diff --stat
```

---

## 🚀 提交步骤

### 方式一：一次性提交所有变更

```bash
# 添加所有文件到暂存区
git add .

# 提交变更
git commit -m "feat: 完成RAG智能客服系统前后端开发

主要功能：
- 前端：3个独立应用（Consumer/Enterprise/System Admin）
- 后端：6个微服务（API Gateway/User/Chat/Knowledge/Alert/Channel）
- 完整的中文注释
- API联调完成
- 安全防护完善"

# 查看提交历史
git log --oneline -5
```

### 方式二：分步提交

#### 第一步：提交后端代码
```bash
git add backend/
git commit -m "feat(backend): 实现后端微服务架构

后端服务：
- API Gateway (端口8000): 统一入口、路由转发
- User Service (端口8001): 用户认证、企业管理
- Chat Service (端口8002): RAG聊天、流式输出
- Knowledge Service (端口8003): 知识库、文档管理
- Alert Service (端口8004): 告警通知
- Channel Service (端口8005): 多渠道接入

技术特性：
- FastAPI + SQLAlchemy
- JWT认证 + bcrypt加密
- Redis限流 + CORS保护
- 防提示词注入
- 完整的中文注释"
```

#### 第二步：提交前端代码
```bash
git add frontend/
git commit -m "feat(frontend): 实现前端Monorepo架构

前端应用：
- Consumer (端口3000): 浮动式客服窗口
- Enterprise (端口8080): 企业管理控制台
- System Admin (端口9090): 系统管理后台

技术特性：
- React 18 + TypeScript
- Tailwind CSS + Zustand
- Vite构建工具
- SSE流式对话
- API动态配置
- 完整的中文注释"
```

#### 第三步：提交文档和测试
```bash
git add docs/ tests/
git commit -m "docs: 添加完整项目文档和测试用例

文档：
- 产品经理视角文档
- API规范文档
- 部署指南
- 安全检查报告

测试：
- 后端调试脚本
- API联调报告
- 前端测试工具"
```

---

## 🔗 推送到 GitHub

### 1. 创建远程仓库

在 GitHub 上创建新仓库后：

```bash
# 添加远程仓库（替换 YOUR_USERNAME 为你的用户名）
git remote add origin https://github.com/YOUR_USERNAME/rag-customer-service.git

# 或使用 SSH（推荐）
git remote add origin git@github.com:YOUR_USERNAME/rag-customer-service.git
```

### 2. 推送代码

```bash
# 推送所有分支
git push -u origin main

# 推送所有分支和标签
git push -u origin --all
git push origin --tags
```

### 3. 验证推送

```bash
# 查看远程仓库
git remote -v

# 查看推送状态
git status
```

---

## 🔄 更新代码

### 拉取最新代码
```bash
git pull origin main
```

### 推送更新
```bash
git add .
git commit -m "fix: 修复XXX问题"
git push origin main
```

---

## 🎯 推荐的 Git 工作流

### 1. 创建功能分支
```bash
git checkout -b feature/new-feature
```

### 2. 开发完成后合并
```bash
git checkout main
git merge feature/new-feature
git push origin main
```

### 3. 删除分支
```bash
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```

---

## 📝 提交信息规范

### 格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档变更
- `style`: 代码格式（不影响功能）
- `refactor`: 重构（既不是新功能也不是修复bug）
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具变更

### 示例
```bash
git commit -m "feat(chat): 添加流式对话功能

实现了SSE流式输出，支持打字机效果

Closes #123"
```

---

## ⚠️ 注意事项

1. **不要提交敏感信息**
   - 永远不要提交 `.env` 文件
   - 不要提交密钥、密码等
   - 使用 `.env.example` 作为模板

2. **提交前检查**
   ```bash
   # 检查暂存的文件
   git status

   # 查看变更内容
   git diff --cached
   ```

3. **保持提交原子性**
   - 每个提交只做一件事
   - 相关的变更放在一起
   - 不相关的变更分开提交

---

## 🆘 常见问题

### 问题1：合并冲突
```bash
# 手动解决冲突后
git add <resolved-files>
git commit -m "merge: 解决冲突"
```

### 问题2：撤销提交
```bash
# 撤销最后一次提交（保留变更）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃变更）
git reset --hard HEAD~1
```

### 问题3：推送被拒绝
```bash
# 先拉取远程更新
git pull --rebase origin main

# 再推送
git push origin main
```

---

## 📚 相关资源

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub 快速入门](https://docs.github.com/en/get-started)
- [Conventional Commits 规范](https://www.conventionalcommits.org/)

---

**创建时间**: 2026-05-18
**版本**: 1.0.0
