import { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Button,
  Input,
  Tag
} from '@rag/ui';
import {
  Upload,
  FileText,
  FileSpreadsheet,
  File,
  Database,
  Trash2
} from 'lucide-react';

interface Document {
  id: string;
  name: string;
  type: 'pdf' | 'docx' | 'txt' | 'xlsx';
  size: string;
  status: 'ready' | 'processing' | 'error';
  uploadedAt: string;
}

export default function KnowledgeBase() {
  const [documents] = useState<Document[]>([
    { id: '1', name: '产品使用手册.pdf', type: 'pdf', size: '2.4 MB', status: 'ready', uploadedAt: '2024-01-15' },
    { id: '2', name: '常见问题解答.docx', type: 'docx', size: '856 KB', status: 'ready', uploadedAt: '2024-01-14' },
    { id: '3', name: '技术规格文档.txt', type: 'txt', size: '128 KB', status: 'processing', uploadedAt: '2024-01-13' },
  ]);

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'pdf': return <FileText className="w-5 h-5 text-red-500" />;
      case 'docx': return <FileText className="w-5 h-5 text-blue-500" />;
      case 'xlsx': return <FileSpreadsheet className="w-5 h-5 text-green-500" />;
      default: return <File className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'ready': return <Tag variant="success">已就绪</Tag>;
      case 'processing': return <Tag variant="warning">处理中</Tag>;
      case 'error': return <Tag variant="danger">失败</Tag>;
      default: return <Tag>未知</Tag>;
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">知识库管理</h2>
          <p className="text-gray-500">管理用于RAG检索的文档和知识库</p>
        </div>
        <Button leftIcon={<Upload className="w-4 h-4" />}>
          上传文档
        </Button>
      </div>

      <div className="mb-6">
        <Input placeholder="搜索文档..." />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">总文档数</p>
                <p className="text-2xl font-bold text-gray-900">24</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">总存储</p>
                <p className="text-2xl font-bold text-gray-900">128.5 MB</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <Database className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">今日上传</p>
                <p className="text-2xl font-bold text-gray-900">3</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h3 className="font-semibold text-gray-900">文档列表</h3>
        </CardHeader>
        <CardContent className="divide-y divide-gray-100">
          {documents.map((doc) => (
            <div key={doc.id} className="py-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                {getFileIcon(doc.type)}
                <div>
                  <p className="font-medium text-gray-900">{doc.name}</p>
                  <p className="text-sm text-gray-500">
                    {doc.size} · {doc.uploadedAt}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {getStatusTag(doc.status)}
                <Button variant="secondary" size="sm" leftIcon={<Trash2 className="w-4 h-4" />}>
                  删除
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
