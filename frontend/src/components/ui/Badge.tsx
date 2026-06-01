interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error';
  className?: string;
}

const variants: Record<string, string> = {
  default: 'bg-gray-100 text-apple-gray-text',
  success: 'bg-green-50 text-apple-green',
  warning: 'bg-orange-50 text-apple-orange',
  error: 'bg-red-50 text-apple-red',
};

export default function Badge({
  children,
  variant = 'default',
  className = '',
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-[11px] font-semibold rounded-lg tracking-wide ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
