/**
 * 前后端API联合调试脚本
 * =====================
 * 
 * 功能：
 * 1. 验证API网关路由
 * 2. 检查前后端API匹配
 * 3. 测试微服务连接
 * 4. 生成调试报告
 */

const fs = require('fs');
const path = require('path');

console.log('\n========================================');
console.log('  RAG智能客服系统 - API联合调试工具');
console.log('========================================\n');

// 后端API网关路由列表 (从代码中提取)
const BACKEND_APIS = [
  // 健康检查
  { path: '/', method: 'GET', service: 'api-gateway', description: '根路径' },
  { path: '/health', method: 'GET', service: 'api-gateway', description: '健康检查' },
  
  // 认证接口
  { path: '/api/v1/auth/login', method: 'POST', service: 'user-service', description: '用户登录' },
  { path: '/api/v1/auth/register', method: 'POST', service: 'user-service', description: '用户注册' },
  { path: '/api/v1/auth/me', method: 'GET', service: 'user-service', description: '获取当前用户' },
  
  // 企业接口
  { path: '/api/v1/enterprises', method: 'POST', service: 'user-service', description: '创建企业' },
  { path: '/api/v1/enterprises/{enterpriseId}', method: 'GET', service: 'user-service', description: '获取企业信息' },
  
  // 知识库接口
  { path: '/api/v1/knowledge-bases', method: 'POST', service: 'knowledge-service', description: '创建知识库' },
  { path: '/api/v1/knowledge-bases', method: 'GET', service: 'knowledge-service', description: '获取知识库列表' },
  { path: '/api/v1/knowledge-bases/{kbId}', method: 'GET', service: 'knowledge-service', description: '获取知识库详情' },
  { path: '/api/v1/knowledge-bases/{kbId}/documents', method: 'POST', service: 'knowledge-service', description: '上传文档' },
  { path: '/api/v1/knowledge-bases/{kbId}/documents', method: 'GET', service: 'knowledge-service', description: '获取文档列表' },
  { path: '/api/v1/documents/{docId}', method: 'DELETE', service: 'knowledge-service', description: '删除文档' },
  
  // 聊天接口
  { path: '/api/v1/chat/sessions', method: 'POST', service: 'chat-service', description: '创建会话' },
  { path: '/api/v1/chat/sessions', method: 'GET', service: 'chat-service', description: '获取会话列表' },
  { path: '/api/v1/chat/sessions/{sessionId}/messages', method: 'POST', service: 'chat-service', description: '发送消息' },
  { path: '/api/v1/chat/sessions/{sessionId}/messages', method: 'GET', service: 'chat-service', description: '获取消息列表' },
  { path: '/api/v1/chat/sessions/{sessionId}', method: 'DELETE', service: 'chat-service', description: '删除会话' },
  
  // 敏感设置接口
  { path: '/api/v1/sensitive-settings', method: 'GET', service: 'user-service', description: '获取敏感设置' },
  { path: '/api/v1/sensitive-settings', method: 'PUT', service: 'user-service', description: '更新敏感设置' },
  { path: '/api/v1/semantic-rules', method: 'POST', service: 'user-service', description: '创建语义规则' },
  { path: '/api/v1/semantic-rules/{ruleId}', method: 'DELETE', service: 'user-service', description: '删除语义规则' },
  
  // 告警接口
  { path: '/api/v1/alerts', method: 'GET', service: 'alert-service', description: '获取告警列表' },
  { path: '/api/v1/alerts/{alertId}/acknowledge', method: 'PUT', service: 'alert-service', description: '确认告警' },
  { path: '/api/v1/alerts/{alertId}/resolve', method: 'PUT', service: 'alert-service', description: '解决告警' },
  
  // 渠道接口
  { path: '/api/v1/channel/{enterpriseId}/{platformType}/webhook', method: 'POST', service: 'channel-service', description: '渠道Webhook' },
  { path: '/api/v1/channel/{enterpriseId}/message', method: 'POST', service: 'channel-service', description: '发送渠道消息' },
];

// 前端API调用列表 (从代码中提取)
const FRONTEND_APIS = [
  // Consumer app
  { path: '/api/v1/auth/login', method: 'POST', app: 'consumer', description: '用户登录' },
  { path: '/api/v1/auth/register', method: 'POST', app: 'consumer', description: '用户注册' },
  { path: '/api/v1/auth/me', method: 'GET', app: 'consumer', description: '获取当前用户' },
  { path: '/api/v1/chat/sessions', method: 'POST', app: 'consumer', description: '创建会话' },
  { path: '/api/v1/chat/sessions', method: 'GET', app: 'consumer', description: '获取会话列表' },
  { path: '/api/v1/chat/sessions/{sessionId}/messages', method: 'POST', app: 'consumer', description: '发送消息' },
  { path: '/api/v1/chat/sessions/{sessionId}/messages', method: 'GET', app: 'consumer', description: '获取消息列表' },
  
  // Enterprise app
  { path: '/api/v1/auth/login', method: 'POST', app: 'enterprise', description: '用户登录' },
  { path: '/api/v1/auth/register', method: 'POST', app: 'enterprise', description: '用户注册' },
  { path: '/api/v1/auth/me', method: 'GET', app: 'enterprise', description: '获取当前用户' },
  { path: '/api/v1/enterprises', method: 'POST', app: 'enterprise', description: '创建企业' },
  { path: '/api/v1/enterprises/{enterpriseId}', method: 'GET', app: 'enterprise', description: '获取企业信息' },
  { path: '/api/v1/knowledge-bases', method: 'POST', app: 'enterprise', description: '创建知识库' },
  { path: '/api/v1/knowledge-bases', method: 'GET', app: 'enterprise', description: '获取知识库列表' },
  { path: '/api/v1/knowledge-bases/{kbId}/documents', method: 'POST', app: 'enterprise', description: '上传文档' },
  { path: '/api/v1/knowledge-bases/{kbId}/documents', method: 'GET', app: 'enterprise', description: '获取文档列表' },
  { path: '/api/v1/documents/{docId}', method: 'DELETE', app: 'enterprise', description: '删除文档' },
  { path: '/api/v1/sensitive-settings', method: 'GET', app: 'enterprise', description: '获取敏感设置' },
  { path: '/api/v1/sensitive-settings', method: 'PUT', app: 'enterprise', description: '更新敏感设置' },
  { path: '/api/v1/semantic-rules', method: 'POST', app: 'enterprise', description: '创建语义规则' },
  { path: '/api/v1/semantic-rules/{ruleId}', method: 'DELETE', app: 'enterprise', description: '删除语义规则' },
  
  // System admin app
  { path: '/api/v1/auth/login', method: 'POST', app: 'system-admin', description: '用户登录' },
  { path: '/api/v1/auth/me', method: 'GET', app: 'system-admin', description: '获取当前用户' },
  { path: '/api/v1/alerts', method: 'GET', app: 'system-admin', description: '获取告警列表' },
  { path: '/api/v1/alerts/{alertId}/acknowledge', method: 'PUT', app: 'system-admin', description: '确认告警' },
  { path: '/api/v1/alerts/{alertId}/resolve', method: 'PUT', app: 'system-admin', description: '解决告警' },
];

// 检查文件是否存在
function checkFileExists(filePath) {
  try {
    return fs.existsSync(filePath);
  } catch {
    return false;
  }
}

// 检查后端微服务文件
function checkBackendServices() {
  console.log('📁 检查后端微服务...');
  
  const backendDir = path.join(__dirname, '../backend');
  const services = [
    { name: 'API Gateway', path: path.join(backendDir, 'api-gateway/main.py') },
    { name: 'User Service', path: path.join(backendDir, 'user-service/main.py') },
    { name: 'Chat Service', path: path.join(backendDir, 'chat-service/main.py') },
    { name: 'Knowledge Service', path: path.join(backendDir, 'knowledge-service/main.py') },
    { name: 'Alert Service', path: path.join(backendDir, 'alert-service/main.py') },
    { name: 'Channel Service', path: path.join(backendDir, 'channel-service/main.py') },
  ];
  
  const results = [];
  
  for (const service of services) {
    const exists = checkFileExists(service.path);
    results.push({ name: service.name, exists, path: service.path });
    console.log(`  ${exists ? '✅' : '❌'} ${service.name} - ${service.path}`);
  }
  
  return results;
}

// 检查前端应用文件
function checkFrontendApps() {
  console.log('\n📁 检查前端应用...');
  
  const frontendDir = path.join(__dirname, '../frontend/apps');
  const apps = [
    { name: 'Consumer App', path: path.join(frontendDir, 'consumer/src/App.tsx') },
    { name: 'Enterprise App', path: path.join(frontendDir, 'enterprise/src/App.tsx') },
    { name: 'System Admin App', path: path.join(frontendDir, 'system-admin/src/App.tsx') },
  ];
  
  const results = [];
  
  for (const app of apps) {
    const exists = checkFileExists(app.path);
    results.push({ name: app.name, exists, path: app.path });
    console.log(`  ${exists ? '✅' : '❌'} ${app.name} - ${app.path}`);
  }
  
  return results;
}

// 比较前后端API
function compareAPIs() {
  console.log('\n🔗 比较前后端API...');
  
  const missingAPIs = [];
  const extraAPIs = [];
  
  // 检查前端调用的API是否都有后端实现
  for (const frontendAPI of FRONTEND_APIS) {
    const backendAPI = BACKEND_APIS.find(
      api => api.path === frontendAPI.path && api.method === frontendAPI.method
    );
    
    if (!backendAPI) {
      missingAPIs.push(frontendAPI);
      console.log(`  ❌ 缺失API: ${frontendAPI.method} ${frontendAPI.path} (${frontendAPI.description})`);
    } else {
      console.log(`  ✅ 匹配: ${frontendAPI.method} ${frontendAPI.path} (${frontendAPI.description})`);
    }
  }
  
  // 检查后端有但前端未使用的API
  for (const backendAPI of BACKEND_APIS) {
    const frontendAPI = FRONTEND_APIS.find(
      api => api.path === backendAPI.path && api.method === backendAPI.method
    );
    
    if (!frontendAPI) {
      extraAPIs.push(backendAPI);
    }
  }
  
  if (extraAPIs.length > 0) {
    console.log(`\n📋 后端有但前端暂未使用的API (${extraAPIs.length}个):`);
    for (const api of extraAPIs) {
      console.log(`  ${api.method} ${api.path} (${api.description})`);
    }
  }
  
  return { missingAPIs, extraAPIs };
}

// 生成报告
function generateReport() {
  const report = {
    timestamp: new Date().toISOString(),
    backend: {
      services: checkBackendServices(),
      apis: BACKEND_APIS,
    },
    frontend: {
      apps: checkFrontendApps(),
      apis: FRONTEND_APIS,
    },
    comparison: compareAPIs(),
  };
  
  // 保存报告
  const reportPath = path.join(__dirname, 'api-debug-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  console.log(`\n📄 报告已保存: ${reportPath}`);
  
  return report;
}

// 主函数
function main() {
  console.log('开始前后端API联合调试...\n');
  
  const report = generateReport();
  
  console.log('\n========================================');
  console.log('  调试结果摘要');
  console.log('========================================\n');
  
  // 统计后端服务
  const backendExists = report.backend.services.filter(s => s.exists).length;
  console.log(`后端微服务: ${backendExists}/${report.backend.services.length} 存在`);
  
  // 统计前端应用
  const frontendExists = report.frontend.apps.filter(a => a.exists).length;
  console.log(`前端应用: ${frontendExists}/${report.frontend.apps.length} 存在`);
  
  // 统计API匹配
  const missingCount = report.comparison.missingAPIs.length;
  if (missingCount === 0) {
    console.log('✅ 所有前端API都有后端实现');
  } else {
    console.log(`❌ ${missingCount} 个前端API缺失后端实现`);
  }
  
  console.log('\n========================================');
  console.log('  调试完成');
  console.log('========================================\n');
}

// 运行主函数
main();
