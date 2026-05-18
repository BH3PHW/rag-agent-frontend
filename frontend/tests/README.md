/**
 * 前端测试用例说明文档
 * =====================
 * 
 * 本文档说明了前端项目的测试用例和调试方法
 */

# 前端测试用例说明

## 1. 项目结构

```
frontend/
├── apps/
│   ├── consumer/           # 消费者端应用
│   ├── enterprise/         # 企业管理端应用
│   └── system-admin/       # 系统管理端应用
├── packages/
│   ├── ui/                # 共享UI组件库
│   └── store/             # 共享状态库
└── tests/
    ├── debug_frontend.js  # 前端调试脚本
    └── README.md          # 本文档
```

## 2. 运行测试

### 2.1 基础构建测试

```bash
cd frontend
npm run build
```

这将构建所有前端应用：
- `@rag/consumer` - 消费者端
- `@rag/enterprise` - 企业端
- `@rag/system-admin` - 系统管理端

### 2.2 使用调试脚本

```bash
cd frontend/tests
node debug_frontend.js
```

### 2.3 TypeScript 类型检查

```bash
cd frontend
npx tsc --noEmit
```

### 2.4 ESLint 代码检查

```bash
cd frontend
npm run lint
```

## 3. 测试用例清单

### 3.1 Consumer 应用测试

| 测试项 | 说明 | 状态 |
|--------|------|------|
| 构建测试 | 应用能否正常构建 | ✅ |
| 类型检查 | TypeScript 类型是否正确 | ✅ |
| 组件渲染 | 主组件能否正常渲染 | ✅ |
| 状态管理 | 消息状态是否正确更新 | ✅ |
| 事件处理 | 发送按钮事件是否正常 | ✅ |

### 3.2 Enterprise 应用测试

| 测试项 | 说明 | 状态 |
|--------|------|------|
| 构建测试 | 应用能否正常构建 | ✅ |
| 类型检查 | TypeScript 类型是否正确 | ✅ |
| 页面切换 | 导航切换是否正常 | ✅ |
| API调用 | 页面数据加载是否正常 | ✅ |
| 表单提交 | 设置保存是否正常 | ✅ |

### 3.3 System Admin 应用测试

| 测试项 | 说明 | 状态 |
|--------|------|------|
| 构建测试 | 应用能否正常构建 | ✅ |
| 类型检查 | TypeScript 类型是否正确 | ✅ |
| 页面切换 | 导航切换是否正常 | ✅ |
| API配置 | 配置保存是否正常 | ✅ |
| 租户管理 | 租户CRUD是否正常 | ✅ |

## 4. 关键组件测试

### 4.1 Consumer App 组件

```tsx
// 测试场景：发送消息
import { render, fireEvent, screen } from '@testing-library/react';

test('发送消息功能', async () => {
  render(<App />);
  
  // 输入消息
  const input = screen.getByPlaceholderText('输入你的问题...');
  fireEvent.change(input, { target: { value: '你好' } });
  
  // 点击发送
  const sendButton = screen.getByRole('button', { name: '发送消息' });
  fireEvent.click(sendButton);
  
  // 验证消息已添加
  expect(screen.getByText('你好')).toBeInTheDocument();
});
```

### 4.2 Enterprise App 组件

```tsx
// 测试场景：页面导航
import { render, fireEvent, screen } from '@testing-library/react';

test('页面导航功能', async () => {
  render(<App />);
  
  // 默认显示知识库页面
  expect(screen.getByText('知识库')).toBeInTheDocument();
  
  // 点击对话监控
  const chatNav = screen.getByText('对话监控');
  fireEvent.click(chatNav);
  
  // 验证切换到对话监控
  expect(screen.getByText('对话监控')).toBeInTheDocument();
});
```

## 5. 调试技巧

### 5.1 查看构建错误

```bash
# 查看详细的构建输出
npm run build -- --verbose

# 查看TypeScript错误
npx tsc --noEmit 2>&1 | head -50
```

### 5.2 浏览器开发者工具

1. 打开浏览器开发者工具
2. 切换到 Console 标签
3. 查看React组件错误
4. 使用React DevTools检查组件状态

### 5.3 网络请求调试

1. 打开开发者工具的 Network 标签
2. 筛选 XHR 或 Fetch 请求
3. 查看API请求和响应

## 6. 常见问题

### Q1: 构建失败，显示模块找不到

**原因**: 依赖未安装或工作区配置问题

**解决方案**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Q2: TypeScript 类型错误

**原因**: 类型定义不完整或导入错误

**解决方案**:
1. 检查类型定义文件
2. 确保所有导入的模块存在
3. 运行 `npx tsc --noEmit` 查看具体错误

### Q3: 样式不生效

**原因**: Tailwind CSS 配置问题

**解决方案**:
1. 检查 `tailwind.config.js` 配置
2. 确保 `@tailwind` 指令在CSS文件中
3. 运行 `npm run build` 重新构建

### Q4: 运行时错误

**常见错误**:
- `undefined is not a function` - 函数未定义
- `Cannot read property 'xxx' of undefined` - 属性访问错误
- `Maximum update depth exceeded` - React状态更新死循环

**调试方法**:
1. 使用 `console.log` 输出关键变量
2. 使用 React DevTools 检查组件状态
3. 查看浏览器控制台的错误堆栈

## 7. 性能测试

### 7.1 构建性能

```bash
# 测量构建时间
time npm run build
```

### 7.2 Bundle大小

```bash
# 分析bundle大小
npx webpack-bundle-analyzer dist/stats.json
```

### 7.3 Lighthouse测试

在Chrome开发者工具中：
1. 打开 Lighthouse 标签
2. 选择性能测试
3. 点击 "Generate report"

## 8. CI/CD集成

```yaml
# .github/workflows/frontend-test.yml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm install
        
      - name: Type check
        run: npx tsc --noEmit
        
      - name: Build
        run: npm run build
```

## 9. 联系方式

如有问题，请联系前端开发团队。

作者：RAG客服系统开发团队
版本：1.0.0
更新日期：2026-05-18
