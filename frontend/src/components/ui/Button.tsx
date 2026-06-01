import { type ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

const variantStyles: Record<string, string> = {
  primary:
    'bg-apple-blue text-white hover:bg-blue-600 active:scale-[0.97] shadow-sm',
  secondary:
    'bg-white text-apple-black border border-gray-200 hover:bg-gray-50 active:scale-[0.97]',
  ghost:
    'text-apple-gray-text hover:text-apple-black hover:bg-gray-100',
};

const sizeStyles: Record<string, string> = {
  sm: 'px-4 py-1.5 text-sm rounded-full',
  md: 'px-6 py-2.5 text-sm rounded-full',
  lg: 'px-8 py-3 text-base rounded-full',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  className = '',
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center font-medium tracking-tight transition-all duration-200 cursor-pointer ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
