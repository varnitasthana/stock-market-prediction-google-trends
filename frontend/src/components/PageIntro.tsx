import { ReactNode } from 'react';

interface PageIntroProps {
  title: string;
  description: string;
  children?: ReactNode;
}

export default function PageIntro({ title, description, children }: PageIntroProps) {
  return (
    <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <p className="mt-1 text-sm text-gray-600">{description}</p>
        </div>
        {children}
      </div>
    </section>
  );
}
