import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Building2, 
  Users, 
  Server, 
  BarChart3, 
  Bell, 
  Settings,
  LogOut,
  Shield,
  Loader2
} from 'lucide-react';
import { ProtectedRoute, PublicRoute, useAuthStore } from './auth';
import { LoginPage } from './auth/LoginPage';
import Dashboard from './pages/Dashboard';
import Tenants from './pages/Tenants';
import UsersPage from './pages/Users';
import Services from './pages/Services';
import Analytics from './pages/Analytics';
import Alerts from './pages/Alerts';
import SettingsPage from './pages/Settings';

interface SidebarProps {
  activePage: string;
  onNavigate: (page: string) => void;
  onLogout: () => void;
  user?: { username: string; email: string } | null;
}

const Sidebar: React.FC<SidebarProps> = ({ activePage, onNavigate, onLogout, user }) => {
  const menuItems = [
    { id: 'dashboard', label: '仪表盘', icon: LayoutDashboard },
    { id: 'tenants', label: '租户管理', icon: Building2 },
    { id: 'users', label: '用户管理', icon: Users },
    { id: 'services', label: '服务监控', icon: Server },
    { id: 'analytics', label: '数据分析', icon: BarChart3 },
    { id: 'alerts', label: '告警中心', icon: Bell },
    { id: 'settings', label: '系统设置', icon: Settings },
  ];

  return (
    <div className="w-64 h-screen bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-600 to-teal-600 rounded-xl flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-gray-900">系统管理</h1>
            <p className="text-xs text-gray-500">RAG智能客服</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-emerald-600' : 'text-gray-400'}`} />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-200">
        {user && (
          <div className="mb-3 px-4">
            <p className="text-sm font-medium text-gray-900">{user.username}</p>
            <p className="text-xs text-gray-500">{user.email}</p>
          </div>
        )}
        <button
          onClick={onLogout}
          className="w-full flex items-center gap-3 px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
        >
          <LogOut className="w-5 h-5" />
          <span>退出登录</span>
        </button>
      </div>
    </div>
  );
};

const MainLayout: React.FC = () => {
  const [activePage, setActivePage] = useState('dashboard');
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    const path = window.location.pathname.replace('/', '');
    if (path) setActivePage(path);
  }, []);

  const handleNavigate = (page: string) => {
    setActivePage(page);
    navigate(`/${page}`);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <Dashboard />;
      case 'tenants':
        return <Tenants />;
      case 'users':
        return <UsersPage />;
      case 'services':
        return <Services />;
      case 'analytics':
        return <Analytics />;
      case 'alerts':
        return <Alerts />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <Dashboard />;
    }
  };

  const pageTitle = {
    dashboard: '仪表盘',
    tenants: '租户管理',
    users: '用户管理',
    services: '服务监控',
    analytics: '数据分析',
    alerts: '告警中心',
    settings: '系统设置',
  }[activePage] || '仪表盘';

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar
        activePage={activePage}
        onNavigate={handleNavigate}
        onLogout={handleLogout}
        user={user}
      />
      <main className="flex-1 overflow-auto">
        <header className="bg-white border-b border-gray-200 px-8 py-4">
          <h2 className="text-xl font-semibold text-gray-900">{pageTitle}</h2>
        </header>
        <div className="p-8">
          {renderPage()}
        </div>
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="tenants" element={<Tenants />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="services" element={<Services />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;