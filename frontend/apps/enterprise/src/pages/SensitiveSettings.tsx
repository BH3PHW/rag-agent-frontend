import { useState, useEffect } from 'react';
import { ShieldAlert, Plus, Trash2, Save, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAppStore } from '../store';
import { api } from '../api/client';
import type { SensitiveSettings, SemanticRule } from '../api/client';

export default function SensitiveSettingsPage() {
  const { enterpriseId } = useAppStore();
  const [settings, setSettings] = useState<SensitiveSettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [newWord, setNewWord] = useState('');
  const [newRule, setNewRule] = useState<Omit<SemanticRule, 'id'>>({
    category: '',
    description: '',
    keywords: [],
    enabled: true,
    requires_human: true,
  });
  const [newKeyword, setNewKeyword] = useState('');

  useEffect(() => {
    if (enterpriseId) {
      loadSettings();
    }
  }, [enterpriseId]);

  const loadSettings = async () => {
    if (!enterpriseId) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.sensitive.getSensitiveSettings(enterpriseId);
      if (result.data) {
        setSettings(result.data);
      }
      if (result.error) {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to load settings');
    } finally {
      setIsLoading(false);
    }
  };

  const saveSettings = async () => {
    if (!enterpriseId || !settings) return;
    setIsSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await api.sensitive.updateSensitiveSettings(enterpriseId, settings);
      if (result.data) {
        setSettings(result.data);
        setSuccess('Settings saved successfully');
        setTimeout(() => setSuccess(null), 3000);
      }
      if (result.error) {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const addSensitiveWord = () => {
    if (!newWord.trim() || !settings) return;
    if (!settings.sensitive_words.includes(newWord.trim())) {
      setSettings({
        ...settings,
        sensitive_words: [...settings.sensitive_words, newWord.trim()],
      });
    }
    setNewWord('');
  };

  const removeSensitiveWord = (word: string) => {
    if (!settings) return;
    setSettings({
      ...settings,
      sensitive_words: settings.sensitive_words.filter(w => w !== word),
    });
  };

  const addRuleKeyword = () => {
    if (!newKeyword.trim()) return;
    setNewRule({
      ...newRule,
      keywords: [...newRule.keywords, newKeyword.trim()],
    });
    setNewKeyword('');
  };

  const removeRuleKeyword = (keyword: string) => {
    setNewRule({
      ...newRule,
      keywords: newRule.keywords.filter(k => k !== keyword),
    });
  };

  const addSemanticRule = async () => {
    if (!enterpriseId || !newRule.category || !newRule.description) return;
    setIsSaving(true);
    setError(null);
    try {
      const result = await api.sensitive.createSemanticRule(newRule);
      if (result.data && settings) {
        setSettings({
          ...settings,
          semantic_rules: [...settings.semantic_rules, result.data],
        });
        setNewRule({
          category: '',
          description: '',
          keywords: [],
          enabled: true,
          requires_human: true,
        });
        setSuccess('Rule added successfully');
        setTimeout(() => setSuccess(null), 3000);
      }
      if (result.error) {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to add rule');
    } finally {
      setIsSaving(false);
    }
  };

  const deleteSemanticRule = async (ruleId: string) => {
    if (!enterpriseId) return;
    setIsSaving(true);
    setError(null);
    try {
      const result = await api.sensitive.deleteSemanticRule(ruleId);
      if (!result.error && settings) {
        setSettings({
          ...settings,
          semantic_rules: settings.semantic_rules.filter(r => r.id !== ruleId),
        });
        setSuccess('Rule deleted successfully');
        setTimeout(() => setSuccess(null), 3000);
      }
      if (result.error) {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to delete rule');
    } finally {
      setIsSaving(false);
    }
  };

  if (!enterpriseId) {
    return (
      <div className="flex flex-col h-full">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Sensitive Settings</h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-500">Please create or select an enterprise first</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Sensitive Settings</h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-800">Sensitive Settings</h2>
          <button
            onClick={saveSettings}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save All'}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-8">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <p className="text-sm text-green-800">{success}</p>
            </div>
          )}

          <section>
            <div className="flex items-center gap-2 mb-4">
              <ShieldAlert className="w-5 h-5 text-red-600" />
              <h3 className="text-lg font-medium text-gray-800">Detection Settings</h3>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings?.enable_keyword_detection ?? true}
                    onChange={(e) => settings && setSettings({ ...settings, enable_keyword_detection: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">Enable Keyword Detection</span>
                </label>
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings?.enable_semantic_detection ?? true}
                    onChange={(e) => settings && setSettings({ ...settings, enable_semantic_detection: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">Enable Semantic Detection</span>
                </label>
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings?.auto_escalation_enabled ?? true}
                    onChange={(e) => settings && setSettings({ ...settings, auto_escalation_enabled: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">Auto Escalation to Human</span>
                </label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sensitivity Threshold: {settings?.sensitivity_threshold ?? 0.7}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings?.sensitivity_threshold ?? 0.7}
                  onChange={(e) => settings && setSettings({ ...settings, sensitivity_threshold: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>
            </div>
          </section>

          <section>
            <h3 className="text-lg font-medium text-gray-800 mb-4">Sensitive Words</h3>
            <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newWord}
                  onChange={(e) => setNewWord(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addSensitiveWord()}
                  placeholder="Add sensitive word..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={addSensitiveWord}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {settings?.sensitive_words.map((word) => (
                  <span
                    key={word}
                    className="inline-flex items-center gap-2 px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm"
                  >
                    {word}
                    <button
                      onClick={() => removeSensitiveWord(word)}
                      className="hover:text-red-600"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </section>

          <section>
            <h3 className="text-lg font-medium text-gray-800 mb-4">Semantic Rules</h3>
            <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <input
                    type="text"
                    value={newRule.category}
                    onChange={(e) => setNewRule({ ...newRule, category: e.target.value })}
                    placeholder="e.g., Pricing, Refund"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <input
                    type="text"
                    value={newRule.description}
                    onChange={(e) => setNewRule({ ...newRule, description: e.target.value })}
                    placeholder="What this rule detects..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Keywords</label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addRuleKeyword()}
                    placeholder="Add keyword..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={addRuleKeyword}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {newRule.keywords.map((keyword) => (
                    <span
                      key={keyword}
                      className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                    >
                      {keyword}
                      <button
                        onClick={() => removeRuleKeyword(keyword)}
                        className="hover:text-blue-600"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newRule.enabled}
                    onChange={(e) => setNewRule({ ...newRule, enabled: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">Enabled</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newRule.requires_human}
                    onChange={(e) => setNewRule({ ...newRule, requires_human: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">Requires Human</span>
                </label>
              </div>
              <button
                onClick={addSemanticRule}
                disabled={isSaving || !newRule.category || !newRule.description}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Add Rule
              </button>
            </div>

            <div className="mt-6 space-y-4">
              {settings?.semantic_rules.map((rule) => (
                <div
                  key={rule.id}
                  className="bg-gray-50 border border-gray-200 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-medium text-gray-800">{rule.category}</h4>
                        {rule.enabled ? (
                          <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                            Enabled
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                            Disabled
                          </span>
                        )}
                        {rule.requires_human && (
                          <span className="px-2 py-0.5 bg-orange-100 text-orange-800 text-xs rounded-full">
                            Human Required
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{rule.description}</p>
                      <div className="flex flex-wrap gap-1">
                        {rule.keywords.map((keyword) => (
                          <span
                            key={keyword}
                            className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                    <button
                      onClick={() => rule.id && deleteSemanticRule(rule.id)}
                      disabled={isSaving}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg disabled:opacity-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
