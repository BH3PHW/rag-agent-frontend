/**
 * System Admin 应用主组件 - 系统管理后台
 * ========================================
 * 
 * 功能说明：
 * - 平台级系统管理后台
 * - 租户管理、服务监控、数据分析
 * - API配置、大模型配置、存储配置
 * - 告警中心、系统设置
 * 
 * 技术栈：
 * - React 18 + TypeScript
 * - Tailwind CSS 样式
 * - Lucide React 图标
 * - @rag/ui 共享组件库
 * 
 * 使用场景：
 * 平台管理员使用，进行系统配置、服务监控、租户管理等
 */

import { useState } from 'react';
import {
  Layout,  // 布局组件
  NavItem   // 导航项组件
} from '@rag/ui';
import {
  Building2,    // 租户管理图标
  Bot,          // 大模型配置图标
  HardDrive,    // 存储配置图标
  Server,       // 服务监控图标
  BarChart3,    // 数据分析图标
  Bell,         // 告警中心图标
  Settings,     // 系统设置图标
  Globe         // API配置图标
} from 'lucide-react';

// 导入各页面组件
import Tenants from './pages/Tenants';           // 租户管理页面
import ModelConfig from './pages/ModelConfig';   // 大模型配置页面
import StorageConfig from './pages/StorageConfig'; // 存储配置页面
import Services from './pages/Services';         // 服务监控页面
import Analytics from './pages/Analytics';       // 数据分析页面
import Alerts from './pages/Alerts';             // 告警中心页面
import SettingsPage from './pages/Settings';     // 系统设置页面
import ApiConfig from './pages/ApiConfig';       // API配置页面

/**
 * 页面类型定义
 */
type ActivePage = 
  | 'api-config'    // API配置
  | 'tenants'       // 租户管理
  | 'model'         // 大模型配置
  | 'storage'       // 存储配置
  | 'services'       // 服务监控
  | 'analytics'      // 数据分析
  | 'alerts'        // 告警中心
  | 'settings';     // 系统设置

/**
 * 导航项接口定义
 */
interface NavItemConfig {
  id: ActivePage;     // 页面ID
  label: string;      // 显示标签
  icon: any;         // 图标组件
  badge?: string;     // 徽章数字
}

/**
 * 系统管理主组件
 * 提供完整的平台管理界面
 */
export default function App() {
  // 当前激活的页面状态，默认显示API配置
  const [activePage, setActivePage] = useState<ActivePage>('api-config');

  /**
   * 导航菜单配置
   */
  const navItems: NavItemConfig[] = [
    { id: 'api-config', label: 'API配置', icon: Globe },              // API端点配置
    { id: 'tenants', label: '租户管理', icon: Building2 },            // 多租户管理
    { id: 'model', label: '大模型配置', icon: Bot },                  // LLM配置
    { id: 'storage', label: '存储配置', icon: HardDrive },            // 存储配置
    { id: 'services', label: '服务监控', icon: Server },              // 微服务监控
    { id: 'analytics', label: '数据分析', icon: BarChart3 },          // 运营数据
    { id: 'alerts', label: '告警中心', icon: Bell, badge: '5' },     // 告警管理（5条未处理）
    { id: 'settings', label: '系统设置', icon: Settings },            // 系统参数
  ];

  /**
   * 页面渲染函数
   */
  const renderPage = () => {
    switch (activePage) {
      case 'api-config':
        return <ApiConfig />;           // API配置页面
      case 'tenants':
        return <Tenants />;            // 租户管理页面
      case 'model':
        return <ModelConfig />;        // 大模型配置页面
      case 'storage':
        return <StorageConfig />;      // 存储配置页面
      case 'services':
        return <Services />;           // 服务监控页面
      case 'analytics':
        return <Analytics />;         // 数据分析页面
      case 'alerts':
        return <Alerts />;            // 告警中心页面
      case 'settings':
        return <SettingsPage />;       // 系统设置页面
      default:
        return <ApiConfig />;          // 默认显示API配置
    }
  };

  /**
   * 侧边栏组件
   */
  const sidebar = (
    <>
      {/* 顶部Logo区域 */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-3">
          {/* Logo图标 - 绿色渐变 */}
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-600 to-teal-600 rounded-xl flex items-center justify-center">
            <Server className="w-6 h-6 text-white" />
          </div>
          {/* Logo文字 */}
          <div>
            <h1 className="font-bold text-gray-900">系统管理</h1>
            <p className="text-xs text-gray-500">RAG智能客服</p>
          </div>
        </div>
      </div>

      {/* 导航菜单 */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavItem
            key={item.id}
            icon={item.icon}
            label={item.label}
            active={activePage === item.id}
            onClick={() => setActivePage(item.id as ActivePage)}
            badge={item.badge}
          />
        ))}
      </nav>

      {/* 底部版本信息 */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-400">
          <p>系统版本: v1.0.0</p>
          <p>运行环境: Docker</p>
        </div>
      </div>
    </>
  );

  /**
   * 渲染主界面
   */
  return (
    <Layout
      sidebar={sidebar}
      title={navItems.find((item) => item.id === activePage)?.label}
      content={renderPage()}
    />
  );
}
