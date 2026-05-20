import React, { useEffect } from 'react';
import { useAuthStore } from './useAuthStore';
import { RequireRole, RoleType } from './rolePermissions';
import { useNavigate } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: RoleType;
  loginPath?: string;
  fallback?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  loginPath = '/login',
  fallback = null,
}) => {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    checkAuth?.();
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate(loginPath, { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, loginPath]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (requiredRole) {
    return <RequireRole role={requiredRole} fallback={fallback}>{children}</RequireRole>;
  }

  return <>{children}</>;
};

interface EnterpriseProtectedRouteProps {
  children: React.ReactNode;
  loginPath?: string;
  fallback?: React.ReactNode;
}

export const EnterpriseProtectedRoute: React.FC<EnterpriseProtectedRouteProps> = ({
  children,
  loginPath = '/login',
  fallback = null,
}) => {
  return (
    <ProtectedRoute
      requiredRole={RoleType.ENTERPRISE_ADMIN}
      loginPath={loginPath}
      fallback={fallback}
    >
      {children}
    </ProtectedRoute>
  );
};

interface AdminProtectedRouteProps {
  children: React.ReactNode;
  loginPath?: string;
  fallback?: React.ReactNode;
}

export const AdminProtectedRoute: React.FC<AdminProtectedRouteProps> = ({
  children,
  loginPath = '/login',
  fallback = null,
}) => {
  return (
    <ProtectedRoute
      requiredRole={RoleType.SYSTEM_ADMIN}
      loginPath={loginPath}
      fallback={fallback}
    >
      {children}
    </ProtectedRoute>
  );
};