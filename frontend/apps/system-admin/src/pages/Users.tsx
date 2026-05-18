import { useState } from 'react';
import { Users, LogOut, Lock, Building } from 'lucide-react';
import { useAppStore } from '../store';

export default function UsersPage() {
  const { 
    currentUser, 
    enterpriseId,
    login,
    register,
    logout,
    createEnterprise,
    isLoading,
    error,
    setError
  } = useAppStore();
  
  const [isLogin, setIsLogin] = useState(true);
  const [isCreatingEnterprise, setIsCreatingEnterprise] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [enterpriseName, setEnterpriseName] = useState('');
  const [message, setMessage] = useState('');

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('');
    setError(null);
    
    if (isLogin) {
      const success = await login(username, password);
      setMessage(success ? 'Login successful!' : 'Login failed. Please check your credentials.');
    } else {
      const success = await register(username, email, password);
      setMessage(success ? 'Registration successful!' : 'Registration failed. Username or email already exists.');
    }
  };

  const handleCreateEnterprise = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('');
    setError(null);
    
    if (!enterpriseName.trim()) {
      setMessage('Please enter enterprise name');
      return;
    }

    const success = await createEnterprise(enterpriseName);
    setMessage(success ? 'Enterprise created successfully!' : 'Failed to create enterprise.');
  };

  if (!currentUser) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="bg-white p-8 rounded-xl shadow-lg max-w-md w-full">
          <div className="flex items-center justify-center mb-6">
            <Lock className="w-12 h-12 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-center mb-6">
            {isLogin ? 'Login' : 'Register'}
          </h2>
          
          <form onSubmit={handleAuth} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter username"
                required
              />
            </div>
            
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter email"
                  required
                />
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter password"
                required
              />
            </div>
            
            {message && (
              <div className={message.includes('successful') ? 'text-green-600 text-sm' : 'text-red-600 text-sm'}>
                {message}
              </div>
            )}
            
            {error && (
              <div className="text-red-600 text-sm">
                {error}
              </div>
            )}
            
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300"
            >
              {isLoading ? 'Loading...' : (isLogin ? 'Login' : 'Register')}
            </button>
          </form>
          
          <div className="mt-6 text-center">
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setMessage('');
                setError(null);
              }}
              className="text-blue-600 hover:underline text-sm"
            >
              {isLogin ? "Don't have an account? Register now" : 'Already have an account? Login'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!enterpriseId && !isCreatingEnterprise) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="bg-white p-8 rounded-xl shadow-lg max-w-md w-full">
          <div className="flex items-center justify-center mb-6">
            <Building className="w-12 h-12 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-center mb-6">
            Create Your Enterprise
          </h2>
          <p className="text-gray-600 text-center mb-6">
            To start using the RAG Customer Service, you need to create an enterprise first.
          </p>
          
          <button
            onClick={() => setIsCreatingEnterprise(true)}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create Enterprise
          </button>
          
          <div className="mt-6 text-center">
            <button
              onClick={logout}
              className="text-gray-600 hover:text-gray-800 text-sm"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!enterpriseId && isCreatingEnterprise) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="bg-white p-8 rounded-xl shadow-lg max-w-md w-full">
          <div className="flex items-center justify-center mb-6">
            <Building className="w-12 h-12 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-center mb-6">
            Create Enterprise
          </h2>
          
          <form onSubmit={handleCreateEnterprise} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Enterprise Name
              </label>
              <input
                type="text"
                value={enterpriseName}
                onChange={(e) => setEnterpriseName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter enterprise name"
                required
              />
            </div>
            
            {message && (
              <div className={message.includes('successfully') ? 'text-green-600 text-sm' : 'text-red-600 text-sm'}>
                {message}
              </div>
            )}
            
            {error && (
              <div className="text-red-600 text-sm">
                {error}
              </div>
            )}
            
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300"
            >
              {isLoading ? 'Creating...' : 'Create'}
            </button>
            
            <button
              type="button"
              onClick={() => setIsCreatingEnterprise(false)}
              className="w-full bg-gray-200 text-gray-700 py-2 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Users className="w-8 h-8 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-800">User Profile</h2>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Account Information</h3>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-semibold text-lg">
                  {currentUser.username[0].toUpperCase()}
                </span>
              </div>
              <div>
                <p className="font-medium text-gray-900">{currentUser.username}</p>
                <p className="text-sm text-gray-500">{currentUser.email}</p>
              </div>
              <span className={currentUser.role === 'admin' 
                ? 'ml-auto px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium'
                : 'ml-auto px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium'
              }>
                {currentUser.role === 'admin' ? 'Administrator' : 'User'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Enterprise Information</h3>
          <div className="flex items-center gap-3">
            <Building className="w-10 h-10 text-blue-600" />
            <div>
              <p className="font-medium text-gray-900">Enterprise ID:</p>
              <p className="text-sm text-gray-500 font-mono">{enterpriseId}</p>
            </div>
          </div>
          <p className="mt-4 text-sm text-gray-600">
            Your account is linked to an enterprise. All data and conversations are isolated within this enterprise.
          </p>
        </div>
      </div>
    </div>
  );
}
