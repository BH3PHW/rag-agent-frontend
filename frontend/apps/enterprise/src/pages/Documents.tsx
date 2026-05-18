import { useState, useEffect } from 'react';
import { Upload, FileText, Trash2, CheckCircle2, AlertCircle, Loader2, Plus } from 'lucide-react';
import { useAppStore } from '../store';
import { api } from '../api/client';

export default function DocumentsPage() {
  const { documents, addDocument, removeDocument, currentUser, enterpriseId, setError } = useAppStore();
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [knowledgeBaseId, setKnowledgeBaseId] = useState<string | null>(null);
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([]);
  const [showNewKB, setShowNewKB] = useState(false);
  const [newKBNamename, setNewKBNamename] = useState('');

  useEffect(() => {
    if (currentUser && enterpriseId) {
      loadKnowledgeBases();
    }
  }, [currentUser, enterpriseId]);

  const loadKnowledgeBases = async () => {
    if (!enterpriseId) return;

    try {
      const result = await api.documents.getKnowledgeBases(enterpriseId);
      if (result.data && result.data.knowledge_bases && result.data.knowledge_bases.length > 0) {
        setKnowledgeBases(result.data.knowledge_bases);
        setKnowledgeBaseId(result.data.knowledge_bases[0].id);
        loadDocuments(result.data.knowledge_bases[0].id);
      }
    } catch (err) {
      console.error('Failed to load knowledge bases:', err);
    }
  };

  const loadDocuments = async (kbId: string) => {
    if (!enterpriseId) return;

    try {
      const result = await api.documents.getDocuments(kbId, enterpriseId);
      if (result.data) {
        setKnowledgeBases(prev => prev.map(kb => {
          if (kb.id === kbId) {
            return { ...kb, documents: result.data };
          }
          return kb;
        }));
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const handleCreateKB = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKBNamename.trim() || !enterpriseId) return;

    try {
      const result = await api.documents.createKnowledgeBase(newKBNamename, enterpriseId);
      if (result.data) {
        setKnowledgeBases([...knowledgeBases, result.data]);
        setKnowledgeBaseId(result.data.id);
        setShowNewKB(false);
        setNewKBNamename('');
      }
    } catch (err) {
      console.error('Failed to create knowledge base:', err);
      setError('Failed to create knowledge base');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files: FileList) => {
    if (!currentUser || !enterpriseId || !knowledgeBaseId) return;
    
    setIsUploading(true);
    setError(null);

    try {
      for (const file of Array.from(files)) {
        const result = await api.documents.uploadDocument(knowledgeBaseId, enterpriseId, file);
        
        if (result.data) {
          addDocument({
            id: result.data.document_id,
            name: result.data.filename,
            size: file.size,
            uploadDate: new Date(),
            status: result.data.status === 'processing' ? 'processing' : 'ready',
            userId: currentUser.id,
          });
        } else if (result.error) {
          setError(result.error);
        }
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError('Failed to upload document');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!enterpriseId) return;

    try {
      const result = await api.documents.deleteDocument(docId, enterpriseId);
      if (result.data !== undefined || result.error === undefined) {
        removeDocument(docId);
      } else {
        setError(result.error || 'Failed to delete document');
      }
    } catch (err) {
      console.error('Delete error:', err);
      setError('Failed to delete document');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processing':
        return <Loader2 className="w-5 h-5 text-yellow-500 animate-spin" />;
      case 'ready':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <FileText className="w-5 h-5 text-gray-500" />;
    }
  };

  if (!currentUser) {
    return (
      <div className="flex items-center justify-center h-full text-center text-gray-500">
        <div>
          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p>Please login first to manage documents.</p>
        </div>
      </div>
    );
  }

  if (!enterpriseId) {
    return (
      <div className="flex items-center justify-center h-full text-center text-gray-500">
        <div>
          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p>Please create an enterprise first.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-800">Documents</h2>
          <button
            onClick={() => setShowNewKB(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            New Knowledge Base
          </button>
        </div>

        <div className="flex gap-2">
          {knowledgeBases.map((kb) => (
            <button
              key={kb.id}
              onClick={() => {
                setKnowledgeBaseId(kb.id);
                loadDocuments(kb.id);
              }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                knowledgeBaseId === kb.id
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {kb.name}
            </button>
          ))}
        </div>
      </div>

      {showNewKB && (
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <form onSubmit={handleCreateKB} className="flex gap-2">
            <input
              type="text"
              value={newKBNamename}
              onChange={(e) => setNewKBNamename(e.target.value)}
              placeholder="Knowledge base name..."
              className="flex-1 px-3 py-2 border rounded-lg"
              autoFocus
            />
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => setShowNewKB(false)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
          </form>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input')?.click()}
          className={`border-2 border-dashed rounded-lg p-8 mb-6 text-center cursor-pointer transition-all ${
            isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
          }`}
        >
          <input
            id="file-input"
            type="file"
            multiple
            accept=".txt,.pdf,.md,.docx"
            onChange={handleFileInput}
            className="hidden"
          />
          <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-gray-600 mb-2">
            {isUploading ? 'Uploading...' : 'Drag files here or click to upload'}
          </p>
          <p className="text-sm text-gray-400">Supports .txt, .pdf, .md, .docx formats</p>
        </div>

        {documents.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p>No documents uploaded yet. Upload documents to enable RAG Q&A.</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow"
              >
                <div className="flex-shrink-0">
                  <FileText className="w-10 h-10 text-blue-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-800 truncate">{doc.name}</p>
                  <p className="text-sm text-gray-500">
                    {formatFileSize(doc.size)} · {new Date(doc.uploadDate).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(doc.status)}
                  <button
                    onClick={() => handleDeleteDocument(doc.id)}
                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
