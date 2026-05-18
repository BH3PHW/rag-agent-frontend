import { cn } from '../utils/cn';
import { ReactNode } from 'react';

type TagVariant = 'default' | 'success' | 'warning' | 'danger';

interface TagProps {
  children: ReactNode;
  variant?: TagVariant;
  className?: string;
}

export function Tag({ children, variant = 'default', className }: TagProps) {
  const variants = {
    default: 'bg-blue-100 text-blue-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-amber-100 text-amber-800',
    danger: 'bg-red-100 text-red-800'
  };

  return (
    <span className={cn(
      'inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium',
      variants[variant],
      className
    )}>
      {children}
    </span>
  );
}
