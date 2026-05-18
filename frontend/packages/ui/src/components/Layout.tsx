import { ReactNode } from 'react';

interface LayoutProps {
  sidebar: ReactNode;
  content: ReactNode;
  title?: string;
}

export function Layout({ sidebar, content, title }: LayoutProps) {
  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {sidebar}
      </aside>
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {title && (
          <header className="bg-white border-b border-gray-200 px-8 py-6">
            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          </header>
        )}
        <div className="flex-1 overflow-auto">
          {content}
        </div>
      </main>
    </div>
  );
}
