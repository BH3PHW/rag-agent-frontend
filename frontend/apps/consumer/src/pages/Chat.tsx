import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Trash2, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useAppStore } from '../store';
import { api } from '../api/client';
import type { Message, Source } from '../types';

export default function Chat() {
  const { 
    messages, 
    addMessage, 
    clearMessages, 
    isLoading, 
    setIsLoading,
    currentUser,
    enterpriseId,
    error,
    setError
  } = useAppStore();
  
  const [input, setInput] = useState('');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (currentUser && enterpriseId && !currentSessionId) {
      initChatSession();
    }
  }, [currentUser, enterpriseId]);

  const initChatSession = async () => {
    if (!currentUser || !enterpriseId) return;

    try {
      const result = await api.createChatSession(currentUser.id, enterpriseId);
      if (result.data) {
        setCurrentSessionId(result.data.id);
      }
    } catch (err) {
      console.error('Failed to create chat session:', err);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading || !currentUser || !enterpriseId || !currentSessionId) return;

    const userMessage: any = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const result = await api.sendMessage(currentSessionId, currentUser.id, input);

      if (result.error) {
        setError(result.error);
        const errorMessage: any = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Error: ${result.error}`,
          timestamp: new Date(),
        };
        addMessage(errorMessage);
      } else if (result.data) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: result.data.content,
          timestamp: new Date(),
          sources: result.data.sources?.map((s, idx): Source => ({
            id: `${idx}`,
            title: s.document_id || 'Document',
            content: s.content,
            score: s.score,
          })),
        };
        addMessage(assistantMessage);
      }
    } catch (err) {
      console.error('Send message error:', err);
      setError('Failed to send message');
      
      const errorMessage: any = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = async () => {
    if (!currentUser || !enterpriseId) return;

    clearMessages();
    setCurrentSessionId(null);
    
    try {
      const result = await api.createChatSession(currentUser.id, enterpriseId);
      if (result.data) {
        setCurrentSessionId(result.data.id);
      }
    } catch (err) {
      console.error('Failed to create new chat session:', err);
    }
  };

  if (!currentUser) {
    return (
      <div className="flex items-center justify-center h-full text-center text-gray-500">
        <div>
          <Bot className="w-16 h-16 mx-auto mb-4 text-blue-500" />
          <h3 className="text-lg font-medium mb-2">Please Login First</h3>
          <p className="text-sm">You need to login to use the chat feature.</p>
        </div>
      </div>
    );
  }

  if (!enterpriseId) {
    return (
      <div className="flex items-center justify-center h-full text-center text-gray-500">
        <div>
          <FileText className="w-16 h-16 mx-auto mb-4 text-blue-500" />
          <h3 className="text-lg font-medium mb-2">Create an Enterprise First</h3>
          <p className="text-sm">Please create an enterprise to start using the chat.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-800">Chat</h2>
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button
              onClick={clearMessages}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              Clear Chat
            </button>
          )}
          <button
            onClick={handleNewChat}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            New Chat
          </button>
        </div>
      </div>
      
      {error && (
        <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <Bot className="w-16 h-16 mb-4 text-blue-500" />
            <h3 className="text-lg font-medium mb-2">Welcome to RAG Agent</h3>
            <p className="text-sm max-w-md">
              Upload your documents and start asking questions. AI will answer based on your document content.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-white" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  message.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'
                }`}
              >
                <div className="prose prose-sm max-w-none">
                  {message.role === 'assistant' ? (
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  ) : (
                    <p>{message.content}</p>
                  )}
                </div>
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs font-medium text-gray-500 mb-2">Sources:</p>
                    {message.sources.map((source) => (
                      <div
                        key={source.id}
                        className="bg-white rounded p-2 mb-2 text-xs border border-gray-200"
                      >
                        <div className="flex items-center gap-1 mb-1">
                          <FileText className="w-3 h-3" />
                          <span className="font-medium">{source.title}</span>
                          <span className="text-gray-400 ml-auto">
                            {(source.score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-gray-600">{source.content}</p>
                      </div>
                    ))}
                  </div>
                )}
                <p className="text-xs mt-2 opacity-70">
                  {message.timestamp instanceof Date ? message.timestamp.toLocaleTimeString() : new Date(message.timestamp).toLocaleTimeString()}
                </p>
              </div>
              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gray-500 flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-white" />
                </div>
              )}
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={1}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
