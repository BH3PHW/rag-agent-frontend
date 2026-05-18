import { cn } from '../utils/cn';
import { ElementType } from 'react';

interface NavItemProps {
  icon: ElementType;
  label: string;
  active?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  badge?: string;
}

export function NavItem({ icon: Icon, label, active, disabled, onClick, badge }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-left',
        active
          ? 'bg-blue-50 text-blue-700 font-medium'
          : disabled
          ? 'text-gray-300 cursor-not-allowed'
          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
      )}
    >
      <Icon className="w-5 h-5 flex-shrink-0" />
      <span className="flex-1">{label}</span>
      {badge && (
        <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
          {badge}
        </span>
      )}
    </button>
  );
}
