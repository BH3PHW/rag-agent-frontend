import { useState } from 'react';
import { 
  FileSearch, 
  CheckCircle, 
  XCircle, 
  Play, 
  Trash2, 
  Plus,
  Settings,
  RefreshCw
} from 'lucide-react';
import { useAppStore } from '../store';
import { CleaningRule, CleaningJob } from '../types';

export default function CleaningPage() {
  const { 
    documents, 
    cleaningRules, 
    cleaningJobs, 
    currentUser,
    addCleaningRule, 
    removeCleaningRule, 
    updateCleaningRule,
    addCleaningJob,
    updateCleaningJob,
    removeCleaningJob
  } = useAppStore();
  
  const [showAddRule, setShowAddRule] = useState(false);
  const [newRule, setNewRule] = useState<Partial<CleaningRule>>({
    name: '',
    type: 'custom',
    enabled: true,
    pattern: '',
    replacement: ''
  });

  const handleAddRule = () => {
    if (!newRule.name) return;
    
    const rule: CleaningRule = {
      id: Date.now().toString(),
      name: newRule.name || '自定义规则',
      type: newRule.type || 'custom',
      enabled: true,
      pattern: newRule.pattern,
      replacement: newRule.replacement,
    };
    addCleaningRule(rule);
    setShowAddRule(false);
    setNewRule({ name: '', type: 'custom', enabled: true, pattern: '', replacement: '' });
  };

  const handleStartCleaning = (docId: string, docName: string) => {
    if (!currentUser) return;
    
    const job: CleaningJob = {
      id: Date.now().toString(),
      documentId: docId,
      documentName: docName,
      status: 'pending',
      progress: 0,
      rules: cleaningRules.filter(r => r.enabled),
      userId: currentUser.id,
    };
    
    addCleaningJob(job);
    
    // 模拟清洗过程
    updateCleaningJob(job.id, { status: 'processing', startTime: new Date() });
    
    let progress = 0;
    const interval = setInterval(() => {
      progress += 20;
      updateCleaningJob(job.id, { progress });
      
      if (progress >= 100) {
        clearInterval(interval);
        updateCleaningJob(job.id, { 
          status: 'completed', 
          progress: 100,
          endTime: new Date(),
          result: '清洗完成！数据已优化'
        });
      }
    }, 500);
  };

  const _cleanText = (text: string, rules: CleaningRule[]): string => {
    let result = text;
    
    rules.filter(r => r.enabled).forEach(rule => {
      switch (rule.type) {
        case 'remove_whitespace':
          result = result.replace(/\s+/g, ' ').trim();
          break;
        case 'remove_newlines':
          result = result.replace(/\n+/g, '\n').trim();
          break;
        case 'remove_special_chars':
          result = result.replace(/[^a-zA-Z0-9\u4e00-\u9fa5\s]/g, '');
          break;
        case 'custom':
          if (rule.pattern) {
            try {
              result = result.replace(new RegExp(rule.pattern, 'g'), rule.replacement || '');
            } catch (e) {
              // 忽略无效正则
            }
          }
          break;
      }
    });
    
    return result;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'processing': return 'text-blue-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <FileSearch className="w-8 h-8 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-800">数据清洗</h2>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左侧：清洗规则 */}
          <div>
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  清洗规则
                </h3>
                <button
                  onClick={() => setShowAddRule(true)}
                  className="flex items-center gap-2 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4" />
                  添加规则
                </button>
              </div>
              
              <div className="space-y-3">
                {cleaningRules.map((rule) => (
                  <div key={rule.id} className="border rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={rule.enabled}
                          onChange={(e) => updateCleaningRule(rule.id, { enabled: e.target.checked })}
                          className="rounded"
                        />
                        <div>
                          <p className="font-medium">{rule.name}</p>
                          <p className="text-xs text-gray-500">
                            {rule.type === 'custom' ? '自定义' : rule.type === 'remove_whitespace' ? '移除空白' : rule.type === 'remove_newlines' ? '移除换行' : '移除特殊字符'}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => removeCleaningRule(rule.id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 添加规则表单 */}
            {showAddRule && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">添加自定义规则</h3>
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="规则名称"
                    value={newRule.name}
                    onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                    className="w-full px-3 py-2 border rounded"
                  />
                  <select
                    value={newRule.type}
                    onChange={(e) => setNewRule({ ...newRule, type: e.target.value as any })}
                    className="w-full px-3 py-2 border rounded"
                  >
                    <option value="remove_whitespace">移除多余空白</option>
                    <option value="remove_newlines">移除多余换行</option>
                    <option value="remove_special_chars">移除特殊字符</option>
                    <option value="custom">自定义</option>
                  </select>
                  {newRule.type === 'custom' && (
                    <>
                      <input
                        type="text"
                        placeholder="正则表达式"
                        value={newRule.pattern || ''}
                        onChange={(e) => setNewRule({ ...newRule, pattern: e.target.value })}
                        className="w-full px-3 py-2 border rounded"
                      />
                      <input
                        type="text"
                        placeholder="替换文本"
                        value={newRule.replacement || ''}
                        onChange={(e) => setNewRule({ ...newRule, replacement: e.target.value })}
                        className="w-full px-3 py-2 border rounded"
                      />
                    </>
                  )}
                  <div className="flex gap-2">
                    <button
                      onClick={handleAddRule}
                      className="flex-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
                    >
                      添加
                    </button>
                    <button
                      onClick={() => setShowAddRule(false)}
                      className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300"
                    >
                      取消
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 右侧：文档和任务 */}
          <div>
            {/* 可用文档 */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">待清洗文档</h3>
              {documents.length === 0 ? (
                <p className="text-gray-500 text-center py-4">暂无文档，请先上传文档</p>
              ) : (
                <div className="space-y-2">
                  {documents
                    .filter(d => !currentUser || d.userId === currentUser.id)
                    .map((doc) => (
                      <div key={doc.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <p className="font-medium">{doc.name}</p>
                          <p className="text-xs text-gray-500">{(doc.size / 1024).toFixed(2)} KB</p>
                        </div>
                        <button
                          onClick={() => handleStartCleaning(doc.id, doc.name)}
                          className="flex items-center gap-1 px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                        >
                          <Play className="w-4 h-4" />
                          清洗
                        </button>
                      </div>
                    ))}
                </div>
              )}
            </div>

            {/* 清洗任务 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">清洗任务</h3>
              {cleaningJobs.length === 0 ? (
                <p className="text-gray-500 text-center py-4">暂无清洗任务</p>
              ) : (
                <div className="space-y-3">
                  {cleaningJobs
                    .filter(j => !currentUser || j.userId === currentUser.id)
                    .map((job) => (
                      <div key={job.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {job.status === 'completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
                            {job.status === 'processing' && <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />}
                            {job.status === 'error' && <XCircle className="w-4 h-4 text-red-500" />}
                            <span className="font-medium">{job.documentName}</span>
                          </div>
                          <button
                            onClick={() => removeCleaningJob(job.id)}
                            className="text-gray-400 hover:text-red-500"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                        
                        <div className="mb-2">
                          <div className="flex justify-between text-sm text-gray-500 mb-1">
                            <span>进度</span>
                            <span>{job.progress}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${job.progress}%` }}
                            />
                          </div>
                        </div>
                        
                        <div className="text-sm">
                          <span className={getStatusColor(job.status)}>
                            {job.status === 'pending' && '等待中'}
                            {job.status === 'processing' && '清洗中'}
                            {job.status === 'completed' && '已完成'}
                            {job.status === 'error' && '出错'}
                          </span>
                          {job.result && (
                            <p className="text-gray-600 mt-1">{job.result}</p>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
