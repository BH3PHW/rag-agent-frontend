/**
 * Enterprise 应用主组件 - 企业控制台
 * ======================================
 * 
 * 功能说明：
 * - 企业级客服系统管理后台
 * - 多页面布局，支持知识库管理、对话监控、渠道接入等
 * - 集成敏感词设置、人工坐席、数据清洗等功能
 * 
 * 技术栈：
 * - React 18 + TypeScript
 * - Tailwind CSS 样式
 * - Lucide React 图标
 * - @rag/ui 共享组件库
 * 
 * 使用场景：
 * 企业客服团队使用，进行知识库维护、对话监控、设置管理等
 */

import { useState } from 'react';
import {
  Layout,  // 布局组件
  NavItem   // 导航项组件
} from '@rag/ui';
import {
  Database,        // 知识库图标
  MessageSquare,   // 对话监控图标
  Bot,            // 机器人图标
  Users,          // 人工坐席图标
  Link2,          // 渠道接入图标
  Settings,        // 系统设置图标
  FileText,       // 文档管理图标
  HelpCircle,     // FAQ管理图标
  ShieldAlert,    // 敏感词设置图标
  FileSearch      // 数据清洗图标
} from 'lucide-react';

// 导入各页面组件
import KnowledgeBase from './pages/KnowledgeBase';    // 知识库页面
import ChatMonitor from './pages/ChatMonitor';       // 对话监控页面
import HumanAgent from './pages/HumanAgent';         // 人工坐席页面
import Channels from './pages/Channels';             // 渠道接入页面
import SettingsPage from './pages/Settings';        // 系统设置页面
import Documents from './pages/Documents';          // 文档管理页面
import Cleaning from './pages/Cleaning';             // 数据清洗页面
import SensitiveSettings from './pages/SensitiveSettings'; // 敏感词设置页面

/**
 * 页面类型定义
 * 定义所有支持的页面路由
 */
type ActivePage = 
  | 'knowledge'      // 知识库
  | 'documents'      // 文档管理
  | 'cleaning'       // 数据清洗
  | 'sensitive'      // 敏感词设置
  | 'chat'           // 对话监控
  | 'human'          // 人工坐席
  | 'channels'       // 渠道接入
  | 'faq'            // FAQ管理
  | 'settings';      // 系统设置

/**
 * 导航项接口定义
 */
interface NavItemConfig {
  id: ActivePage;     // 页面ID
  label: string;      // 显示标签
  icon: any;          // 图标组件
  badge?: string;     // 徽章数字（如未读消息数）
}

/**
 * 企业控制台主组件
 * 提供完整的客服管理界面
 */
export default function App() {
  // 当前激活的页面状态
  const [activePage, setActivePage] = useState<ActivePage>('knowledge');

  /**
   * 导航菜单配置
   * 定义侧边栏的所有导航项
   */
  const navItems: NavItemConfig[] = [
    { id: 'knowledge', label: '知识库', icon: Database },           // 知识库管理
    { id: 'documents', label: '文档管理', icon: FileText },          // 文档上传下载
    { id: 'cleaning', label: '数据清洗', icon: FileSearch },         // 数据清洗工具
    { id: 'sensitive', label: '敏感词设置', icon: ShieldAlert },      // 敏感词配置
    { id: 'chat', label: '对话监控', icon: MessageSquare, badge: '3' }, // 对话监控（3条未读）
    { id: 'human', label: '人工坐席', icon: Users },                  // 人工客服
    { id: 'channels', label: '渠道接入', icon: Link2 },              // 多渠道接入
    { id: 'faq', label: 'FAQ管理', icon: HelpCircle },                // 常见问题
    { id: 'settings', label: '系统设置', icon: Settings },           // 系统配置
  ];

  /**
   * 页面渲染函数
   * 根据当前激活的页面渲染对应组件
   */
  const renderPage = () => {
    switch (activePage) {
      case 'knowledge':
        return <KnowledgeBase />;       // 知识库管理
      case 'documents':
        return <Documents />;            // 文档管理
      case 'cleaning':
        return <Cleaning />;             // 数据清洗
      case 'sensitive':
        return <SensitiveSettings />;     // 敏感词设置
      case 'chat':
        return <ChatMonitor />;          // 对话监控
      case 'human':
        return <HumanAgent />;           // 人工坐席
      case 'channels':
        return <Channels />;             // 渠道接入
      case 'settings':
        return <SettingsPage />;        // 系统设置
      default:
        return <KnowledgeBase />;        // 默认显示知识库
    }
  };

  /**
   * 侧边栏组件
   * 包含Logo、导航菜单等
   */
  const sidebar = (
    <>
      {/* 顶部Logo区域 */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-3">
          {/* Logo图标 */}
          <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-xl flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          {/* Logo文字 */}
          <div>
            <h1 className="font-bold text-gray-900">企业控制台</h1>
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
            active={activePage === item.id}       // 是否激活
            onClick={() => setActivePage(item.id as ActivePage)} // 点击事件
            badge={item.badge}                     // 徽章数字
          />
        ))}
      </nav>
    </>
  );

  /**
   * 渲染主界面
   * 使用Layout组件包裹侧边栏和内容区
   */
  return (
    <Layout
      sidebar={sidebar}                                          // 侧边栏内容
      title={navItems.find((item) => item.id === activePage)?.label} // 页面标题
      content={renderPage()}                                       // 主内容区
    />
  );
}
