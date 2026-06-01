interface TagProps {
  children: React.ReactNode;
  variant?: 'default' | 'active';
  onClick?: () => void;
  className?: string;
}

export default function Tag({
  children,
  variant = 'default',
  onClick,
  className = '',
}: TagProps) {
  const base =
    'inline-flex items-center px-3 py-1 text-xs font-medium rounded-xl transition-all duration-200';
  const variants = {
    default:
      'bg-gray-100 text-apple-gray-text hover:bg-gray-200 cursor-pointer',
    active:
      'bg-apple-blue text-white cursor-pointer shadow-sm',
  };

  return (
    <span
      className={`${base} ${variants[variant]} ${className}`}
      onClick={onClick}
    >
      {children}
    </span>
  );
}
