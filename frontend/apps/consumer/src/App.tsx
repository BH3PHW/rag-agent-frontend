/**
 * Consumer 应用主组件 - RAG智能客服对话界面
 * ==========================================
 * 
 * 功能说明：
 * - 浮动式客服窗口组件（类似Intercom）
 * - 支持最小化、展开、关闭三种状态
 * - 实时消息对话功能
 * - 打字机效果的消息显示
 * 
 * 技术栈：
 * - React 18 + TypeScript
 * - Tailwind CSS 样式
 * - Lucide React 图标
 * 
 * 使用场景：
 * 嵌入到网站底部，提供即时客服功能
 */

import { useState } from 'react';
import { cn } from '@rag/ui';
import {
  Bot,        // AI机器人图标
  Send,       // 发送按钮图标
  User,       // 用户图标
  Loader2,    // 加载动画图标
  MessageSquare, // 消息图标
  X,          // 关闭图标
  ChevronDown, // 最小化图标
  ChevronUp   // 展开图标
} from 'lucide-react';

/**
 * 消息接口定义
 * 用于描述对话中每条消息的结构
 */
interface Message {
  id: string;                    // 消息唯一ID
  role: 'user' | 'assistant';  // 消息角色：用户或AI助手
  content: string;              // 消息内容
  timestamp: Date;               // 消息时间戳
}

/**
 * RAG智能客服主组件
 * 提供浮动的客服对话窗口
 */
export default function App() {
  // 组件状态管理
  const [isOpen, setIsOpen] = useState(false);      // 是否打开窗口
  const [isMinimized, setIsMinimized] = useState(false); // 是否最小化
  const [input, setInput] = useState('');          // 输入框内容
  const [messages, setMessages] = useState<Message[]>([
    // 初始欢迎消息
    {
      id: '1',
      role: 'assistant',
      content: '你好！我是 RAG 智能客服，有什么可以帮助你的吗？',
      timestamp: new Date()
    }
  ]);
  const [isLoading, setIsLoading] = useState(false); // 是否正在加载

  /**
   * 发送消息处理函数
   * 
   * 处理流程：
   * 1. 验证输入不为空
   * 2. 创建用户消息对象
   * 3. 更新消息列表显示用户消息
   * 4. 清空输入框
   * 5. 调用后端API获取回复（当前为模拟）
   * 6. 显示AI助手回复
   */
  const handleSend = async () => {
    // 防止空消息或加载中时发送
    if (!input.trim() || isLoading) return;

    // 创建用户消息
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    // 添加用户消息到列表
    setMessages(prev => [...prev, userMessage]);
    setInput('');              // 清空输入框
    setIsLoading(true);        // 显示加载状态

    // 模拟AI回复（实际项目中应调用API）
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '感谢你的提问！这是 RAG 智能客服系统的演示。你的问题是：' + userMessage.content,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);  // 1.5秒后返回模拟回复
  };

  // 状态1：窗口未打开，显示浮动按钮
  if (!isOpen) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        {/* 浮动消息按钮 */}
        <button
          onClick={() => setIsOpen(true)}
          className="w-16 h-16 bg-blue-600 rounded-full shadow-lg hover:bg-blue-700 transition-colors flex items-center justify-center"
          aria-label="打开客服窗口"
        >
          <MessageSquare className="w-7 h-7 text-white" />
        </button>
        
        {/* 悬停提示气泡 */}
        <div className="absolute bottom-20 right-0 bg-white rounded-lg shadow-xl p-3 min-w-[200px]">
          <p className="text-sm text-gray-600">有什么可以帮助你的吗？</p>
        </div>
      </div>
    );
  }

  // 状态2：窗口最小化，显示简洁版
  if (isMinimized) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 w-80 overflow-hidden">
          {/* 最小化状态的头部 */}
          <div className="bg-blue-600 text-white px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5" />
              <span className="font-medium">RAG 智能客服</span>
            </div>
            <div className="flex items-center gap-2">
              {/* 展开按钮 */}
              <button 
                onClick={() => setIsMinimized(false)} 
                className="p-1 hover:bg-blue-500 rounded"
                aria-label="展开窗口"
              >
                <ChevronUp className="w-5 h-5" />
              </button>
              {/* 关闭按钮 */}
              <button 
                onClick={() => setIsOpen(false)} 
                className="p-1 hover:bg-blue-500 rounded"
                aria-label="关闭窗口"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
          {/* 消息计数提示 */}
          <div className="p-3 text-center text-sm text-gray-500">
            {messages.length - 1} 条新消息
          </div>
        </div>
      </div>
    );
  }

  // 状态3：窗口完全展开，显示完整对话界面
  return (
    <div className="fixed bottom-6 right-6 z-50">
      <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 w-96 overflow-hidden">
        {/* 头部区域 - 渐变背景 */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-4 flex items-center justify-between">
          {/* 左侧：Logo和标题 */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold">RAG 智能客服</h3>
              <p className="text-xs text-blue-100">随时为你解答问题</p>
            </div>
          </div>
          
          {/* 右侧：控制按钮 */}
          <div className="flex items-center gap-1">
            {/* 最小化按钮 */}
            <button 
              onClick={() => setIsMinimized(true)} 
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              aria-label="最小化"
            >
              <ChevronDown className="w-5 h-5" />
            </button>
            {/* 关闭按钮 */}
            <button 
              onClick={() => setIsOpen(false)} 
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              aria-label="关闭"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 消息区域 - 可滚动 */}
        <div className="h-96 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {/* 消息列表 */}
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'flex gap-3',
                message.role === 'user' && 'flex-row-reverse'  // 用户消息靠右
              )}
            >
              {/* 头像 */}
              <div className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                message.role === 'user' ? 'bg-blue-600' : 'bg-gray-300'
              )}>
                {message.role === 'user' ? (
                  <User className="w-4 h-4 text-white" />
                ) : (
                  <Bot className="w-4 h-4 text-gray-600" />
                )}
              </div>
              
              {/* 消息气泡 */}
              <div className={cn(
                'max-w-[75%] rounded-2xl px-4 py-3',
                message.role === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-sm'   // 用户消息蓝色
                  : 'bg-white text-gray-800 rounded-tl-sm shadow-sm'  // AI消息白色
              )}>
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p className={cn(
                  'text-xs mt-1',
                  message.role === 'user' ? 'text-blue-100' : 'text-gray-400'
                )}>
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}

          {/* 加载动画 */}
          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
                <Bot className="w-4 h-4 text-gray-600" />
              </div>
              <div className="bg-white rounded-2xl rounded-tl-sm shadow-sm px-4 py-3">
                <div className="flex items-center gap-2 text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">正在思考...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 输入区域 */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="flex gap-2">
            {/* 文本输入框 */}
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}  // 回车发送
              placeholder="输入你的问题..."
              className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
              disabled={isLoading}  // 加载中禁用输入
            />
            {/* 发送按钮 */}
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}  // 空消息或加载中禁用
              className={cn(
                'w-11 h-11 rounded-xl flex items-center justify-center transition-colors',
                input.trim() && !isLoading
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'  // 可用状态
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'  // 禁用状态
              )}
              aria-label="发送消息"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
