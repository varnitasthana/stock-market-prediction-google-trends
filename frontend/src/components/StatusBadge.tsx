interface StatusBadgeProps {
  label: string;
  tone?: 'success' | 'warning' | 'neutral';
}

export default function StatusBadge({ label, tone = 'neutral' }: StatusBadgeProps) {
  const tones = {
    success: 'bg-green-50 text-green-700 border-green-200',
    warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    neutral: 'bg-gray-50 text-gray-700 border-gray-200',
  };

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${tones[tone]}`}>
      {label}
    </span>
  );
}
