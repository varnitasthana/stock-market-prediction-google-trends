import { ReactNode } from 'react';

interface HelpPanelProps {
  title: string;
  children: ReactNode;
  icon?: string;
  defaultOpen?: boolean;
}

export default function HelpPanel({ title, children, icon = 'i', defaultOpen = false }: HelpPanelProps) {
  return (
    <details className="rounded-lg border border-gray-200 bg-gray-50 p-4" open={defaultOpen}>
      <summary className="flex cursor-pointer select-none items-center gap-2 text-sm font-medium text-gray-700">
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">{icon}</span>
        <span>{title}</span>
        <span className="ml-auto text-gray-400 transition-transform">⌄</span>
      </summary>
      <div className="mt-3 space-y-2 text-sm text-gray-600">
        {children}
      </div>
    </details>
  );
}