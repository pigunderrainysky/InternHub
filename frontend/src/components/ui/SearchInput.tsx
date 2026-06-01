import { type KeyboardEvent, useState, useRef } from 'react';
import { MagnifyingGlass } from '@phosphor-icons/react';

interface SearchInputProps {
  placeholder?: string;
  defaultValue?: string;
  onSearch?: (keyword: string) => void;
  className?: string;
}

export default function SearchInput({
  placeholder = '搜索...',
  defaultValue = '',
  onSearch,
  className = '',
}: SearchInputProps) {
  const [value, setValue] = useState(defaultValue);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && onSearch) {
      onSearch(value.trim());
    }
  };

  return (
    <div
      className={`flex items-center gap-2 bg-gray-100/70 rounded-full px-4 py-2 border border-transparent focus-within:border-apple-blue focus-within:bg-white focus-within:shadow-[0_0_0_3px_rgba(0,113,227,0.1)] transition-all duration-200 cursor-text ${className}`}
      onClick={() => inputRef.current?.focus()}
    >
      <MagnifyingGlass size={16} weight="bold" className="text-apple-gray-text shrink-0" />
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="flex-1 bg-transparent text-sm text-apple-black placeholder:text-apple-gray-text outline-none border-none p-0"
      />
    </div>
  );
}
