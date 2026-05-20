import { useState, useEffect } from 'react';
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
  Trash2,
  Plus,
  RefreshCw,
  Loader2,
  BarChart3
} from 'lucide-react';
import { useAppStore } from '../store';
import { api } from '../api/client';

export default function KnowledgeBase() {
  const { currentUser, enterpriseId, setError } = useAppStore();
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showNewKB, setShowNewKB] = useState(false);
  const [newKBNamename, setNewKBNamename] = useState('');
  const [newKBDescription, setNewKBDescription] = useState('');

  useEffect(() => {
    if (currentUser && enterpriseId) {
      loadKnowledgeBases();
    }
  }, [currentUser, enterpriseId]);

  const loadKnowledgeBases = async () => {
    if (!enterpriseId) return;

    setIsLoading(true);
    try {
      const result = await api.documents.getKnowledgeBases(enterpriseId);
      if (result.data && result.data.knowledge_bases) {
        setKnowledgeBases(result.data.knowledge_bases);
      }
    } catch (err) {
      console.error('Failed to load knowledge bases:', err);
      setError('Failed to load knowledge bases');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateKB = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKBNamename.trim() || !enterpriseId) return;

    try {
      const result = await api.documents.createKnowledgeBase(newKBNamename, enterpriseId);
      if (result.data) {
        setKnowledgeBases([...knowledgeBases, result.data]);
        setShowNewKB(false);
        setNewKBNamename('');
        setNewKBDescription('');
      }
    } catch (err) {
      console.error('Failed to create knowledge base:', err);
      setError('Failed to create knowledge base');
    }
  };

  const filteredKBs = knowledgeBases.filter(kb =>
    kb.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (kb.description && kb.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (!currentUser) {
    return (
      <div className="flex items-center justify-center h-full text-center text-gray-500">
        <div>
          <Database className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p>Please login first to manage knowledge bases.</p>
        </div>
      </div>
    );
  }

  if (!enterpriseId) {
    return (
      <div className="flex items-center justify-center h-full text-center text-gray-500">
        <div>
          <Database className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p>Please create an enterprise first.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">知识库管理</h2>
          <p className="text-gray-500">管理用于RAG检索的文档和知识库</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            leftIcon={<RefreshCw className="w-4 h-4" />}
            onClick={loadKnowledgeBases}
            disabled={isLoading}
          >
            {isLoading ? '刷新中...' : '刷新'}
          </Button>
          <Button
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => setShowNewKB(true)}
          >
            新建知识库
          </Button>
        </div>
      </div>

      <div className="mb-6">
        <Input
          placeholder="搜索知识库..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          type="search"
        />
      </div>

      {showNewKB && (
        <Card className="mb-8">
          <CardHeader>
            <h3 className="font-medium text-gray-900">创建新知识库</h3>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateKB} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  知识库名称
                </label>
                <Input
                  value={newKBNamename}
                  onChange={(e) => setNewKBNamename(e.target.value)}
                  placeholder="输入知识库名称..."
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  描述（可选）
                </label>
                <Input
                  value={newKBDescription}
                  onChange={(e) => setNewKBDescription(e.target.value)}
                  placeholder="简要描述知识库内容..."
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={!newKBNamename.trim()}>
                  创建
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setShowNewKB(false)}
                >
                  取消
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">总知识库数</p>
                <p className="text-2xl font-bold text-gray-900">{knowledgeBases.length}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <Database className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">总文档数</p>
                <p className="text-2xl font-bold text-gray-900">
                  {knowledgeBases.reduce((sum, kb) => sum + (kb.document_count || 0), 0)}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <FileText className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">活跃知识库</p>
                <p className="text-2xl font-bold text-gray-900">
                  {knowledgeBases.filter(kb => kb.is_active).length}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredKBs.length === 0 ? (
            <Card className="col-span-full">
              <CardContent className="p-8 text-center text-gray-500">
                <Database className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p>{searchTerm ? '未找到匹配的知识库' : '暂无知识库，请创建一个开始使用'}</p>
              </CardContent>
            </Card>
          ) : (
            filteredKBs.map((kb) => (
              <Card key={kb.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">{kb.name}</h3>
                      {kb.description && (
                        <p className="text-sm text-gray-500 mt-1">{kb.description}</p>
                      )}
                    </div>
                    <Tag variant={kb.is_active ? 'success' : 'secondary'}>
                      {kb.is_active ? '活跃' : '已停用'}
                    </Tag>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-gray-500">文档数</p>
                      <p className="text-lg font-semibold text-gray-900">{kb.document_count || 0}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">分块数</p>
                      <p className="text-lg font-semibold text-gray-900">{kb.chunk_count || 0}</p>
                    </div>
                  </div>
                  {kb.created_at && (
                    <p className="text-xs text-gray-400">
                      创建时间: {new Date(kb.created_at).toLocaleDateString()}
                    </p>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}
