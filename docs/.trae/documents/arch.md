
## 1. Architecture Design
```mermaid
graph TB
    subgraph Frontend
        A[React App]
        B[Components]
        C[State Management]
        D[Routing]
    end
    
    subgraph External Services
        E[LLM API]
        F[Vector DB API]
    end
    
    A &lt;--&gt; B
    A &lt;--&gt; C
    A &lt;--&gt; D
    A --&gt; E
    A --&gt; F
```

## 2. Technology Description
- Frontend: React@18 + TypeScript + tailwindcss@3 + vite
- Initialization Tool: vite-init (react-ts template)
- State Management: Zustand
- Markdown Rendering: react-markdown
- Icons: lucide-react
- Containerization: Docker + nginx

## 3. Route Definitions
| Route | Purpose |
|-------|---------|
| / | 聊天主页面 |
| /documents | 文档管理页面 |
| /settings | 设置页面 |

## 4. API Definitions
前端直接调用外部API，无后端服务。

### Type Definitions
```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
}

interface Source {
  id: string;
  title: string;
  content: string;
  score: number;
}

interface Document {
  id: string;
  name: string;
  size: number;
  uploadDate: Date;
  status: 'processing' | 'ready' | 'error';
}

interface Settings {
  apiKey: string;
  apiEndpoint: string;
  model: string;
  temperature: number;
  topP: number;
  topK: number;
  chunkSize: number;
  chunkOverlap: number;
}
```

## 5. Data Model
使用 localStorage 存储本地数据，无需数据库。

### LocalStorage Keys
- `rag_messages`: 聊天历史
- `rag_documents`: 文档列表
- `rag_settings`: 用户设置
