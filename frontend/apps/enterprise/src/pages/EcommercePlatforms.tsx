import { useState, useEffect } from 'react';
import { Card, Button, Switch, Input, Tabs, Tag, Modal, Form, Input as AntdInput, Space } from 'antd';
import { 
  ShoppingCartOutlined, 
  PackageOutlined, 
  SettingsOutlined,
  PlusOutlined,
  SaveOutlined,
  RefreshOutlined,
  AppstoreOutlined
} from '@ant-design/icons';
import { useApiClient } from '../api/client';

const { TabPane } = Tabs;

interface EcommercePlatformsPageProps {
  enterpriseId: string;
}

export default function EcommercePlatformsPage({ enterpriseId }: EcommercePlatformsPageProps) {
  const apiClient = useApiClient();
  const [platforms, setPlatforms] = useState<any[]>([]);
  const [tools, setTools] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingPlatform, setEditingPlatform] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [addForm] = Form.useForm();

  const fetchPlatforms = async () => {
    setLoading(true);
    try {
      const response = await apiClient.ecommerce.getPlatforms(enterpriseId);
      setPlatforms(response.data);
    } catch (error) {
      console.error('Failed to fetch platforms:', error);
    }
    setLoading(false);
  };

  const fetchTools = async () => {
    setLoading(true);
    try {
      const response = await apiClient.ecommerce.getTools(enterpriseId);
      setTools(response.data);
    } catch (error) {
      console.error('Failed to fetch tools:', error);
    }
    setLoading(false);
  };

  const togglePlatform = async (platformId: string, enabled: boolean) => {
    setLoading(true);
    try {
      await apiClient.ecommerce.updatePlatform(platformId, enterpriseId, enabled);
      fetchPlatforms();
    } catch (error) {
      console.error('Failed to update platform:', error);
    }
    setLoading(false);
  };

  const toggleTool = async (toolName: string, enabled: boolean) => {
    setLoading(true);
    try {
      await apiClient.ecommerce.updateTool(toolName, enterpriseId, enabled);
      fetchTools();
    } catch (error) {
      console.error('Failed to update tool:', error);
    }
    setLoading(false);
  };

  const savePlatformConfig = async (platformId: string) => {
    setLoading(true);
    try {
      await apiClient.ecommerce.updatePlatform(
        platformId, 
        enterpriseId, 
        true,
        { api_key: apiKey }
      );
      setEditingPlatform(null);
      setApiKey('');
      fetchPlatforms();
    } catch (error) {
      console.error('Failed to save platform config:', error);
    }
    setLoading(false);
  };

  const handleAddPlatform = async (values: any) => {
    setLoading(true);
    try {
      await apiClient.ecommerce.addPlatform(
        values.platform_id,
        values.name,
        values.icon || '🔧',
        values.api_type || 'custom',
        values.config_schema ? JSON.parse(values.config_schema) : undefined
      );
      setAddModalVisible(false);
      addForm.resetFields();
      fetchPlatforms();
    } catch (error) {
      console.error('Failed to add platform:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchPlatforms();
    fetchTools();
  }, [enterpriseId]);

  const getCategoryTag = (category: string) => {
    const tags: Record<string, { color: string; label: string }> = {
      order: { color: 'blue', label: '订单' },
      product: { color: 'green', label: '商品' },
      platform: { color: 'orange', label: '平台' }
    };
    const tag = tags[category] || { color: 'gray', label: category };
    return <Tag color={tag.color}>{tag.label}</Tag>;
  };

  return (
    <div className="ecommerce-platforms-page">
      <div className="page-header">
        <h2 className="page-title">
          <ShoppingCartOutlined className="icon" />
          电商工具配置
        </h2>
        <Space>
          <Button 
            type="primary" 
            onClick={() => setAddModalVisible(true)}
            icon={<AppstoreOutlined />}
          >
            添加新平台
          </Button>
          <Button 
            type="default" 
            onClick={() => { fetchPlatforms(); fetchTools(); }}
            icon={<RefreshOutlined />}
            loading={loading}
          >
            刷新配置
          </Button>
        </Space>
      </div>

      <Tabs defaultActiveKey="platforms" className="tabs-container">
        <TabPane tab={<span><PackageOutlined /> 电商平台</span>} key="platforms">
          <Card className="platforms-card">
            <div className="platforms-grid">
              {platforms.map((platform) => (
                <div 
                  key={platform.platform_id} 
                  className={`platform-card ${platform.enabled ? 'enabled' : 'disabled'}`}
                >
                  <div className="platform-header">
                    <span className="platform-icon">{platform.icon}</span>
                    <div className="platform-info">
                      <h3>{platform.name}</h3>
                      <span className="platform-id">{platform.platform_id}</span>
                    </div>
                    <Switch
                      checked={platform.enabled}
                      onChange={(checked) => togglePlatform(platform.platform_id, checked)}
                      loading={loading}
                    />
                  </div>

                  {platform.enabled && (
                    <div className="platform-body">
                      {editingPlatform === platform.platform_id ? (
                        <div className="config-form">
                          <Input
                            placeholder="请输入API Key"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            className="api-key-input"
                          />
                          <div className="config-actions">
                            <Button 
                              type="primary" 
                              onClick={() => savePlatformConfig(platform.platform_id)}
                              icon={<SaveOutlined />}
                              loading={loading}
                            >
                              保存
                            </Button>
                            <Button onClick={() => setEditingPlatform(null)}>
                              取消
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="config-summary">
                          {platform.has_config ? (
                            <div className="config-item">
                              <SettingsOutlined className="config-icon" />
                              <span>已配置API</span>
                              <Button 
                                type="text" 
                                onClick={() => setEditingPlatform(platform.platform_id)}
                              >
                                修改配置
                              </Button>
                            </div>
                          ) : (
                            <Button 
                              type="dashed" 
                              onClick={() => setEditingPlatform(platform.platform_id)}
                              icon={<PlusOutlined />}
                            >
                              添加API配置
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </TabPane>

        <TabPane tab={<span><SettingsOutlined /> 工具配置</span>} key="tools">
          <Card className="tools-card">
            <div className="tools-list">
              {tools.map((tool) => (
                <div 
                  key={tool.tool_name} 
                  className={`tool-item ${tool.enabled ? 'enabled' : 'disabled'}`}
                >
                  <div className="tool-info">
                    <div className="tool-header">
                      <h3>{tool.name}</h3>
                      {getCategoryTag(tool.category)}
                    </div>
                    <p className="tool-description">{tool.description}</p>
                  </div>
                  <Switch
                    checked={tool.enabled}
                    onChange={(checked) => toggleTool(tool.tool_name, checked)}
                    loading={loading}
                  />
                </div>
              ))}
            </div>
          </Card>
        </TabPane>
      </Tabs>

      <Modal
        title="添加新平台"
        open={addModalVisible}
        onOk={addForm.submit}
        onCancel={() => { setAddModalVisible(false); addForm.resetFields(); }}
        confirmLoading={loading}
        width={600}
      >
        <Form
          form={addForm}
          onFinish={handleAddPlatform}
          layout="vertical"
        >
          <Form.Item
            label="平台ID"
            name="platform_id"
            rules={[{ required: true, message: '请输入平台ID' }]}
          >
            <Input placeholder="例如: wechat" />
          </Form.Item>
          <Form.Item
            label="平台名称"
            name="name"
            rules={[{ required: true, message: '请输入平台名称' }]}
          >
            <Input placeholder="例如: 微信小店" />
          </Form.Item>
          <Form.Item
            label="平台图标"
            name="icon"
            initialValue="🔧"
          >
            <Input placeholder="例如: 💰" />
          </Form.Item>
          <Form.Item
            label="API类型"
            name="api_type"
            initialValue="custom"
          >
            <Input placeholder="例如: custom" />
          </Form.Item>
          <Form.Item
            label="配置项定义"
            name="config_schema"
          >
            <AntdInput.TextArea 
              rows={4} 
              placeholder='{"api_key": {"type": "string", "label": "API Key"}}'
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
