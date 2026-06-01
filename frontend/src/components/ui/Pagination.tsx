import { CaretLeft, CaretRight } from '@phosphor-icons/react';

interface PaginationProps {
  page: number;
  pages: number;
  onPageChange: (page: number) => void;
}

function getPageRange(page: number, pages: number): (number | 'ellipsis')[] {
  if (pages <= 7) {
    return Array.from({ length: pages }, (_, i) => i + 1);
  }

  const range: (number | 'ellipsis')[] = [1];

  if (page > 3) range.push('ellipsis');

  const start = Math.max(2, page - 1);
  const end = Math.min(pages - 1, page + 1);

  for (let i = start; i <= end; i++) {
    range.push(i);
  }

  if (page < pages - 2) range.push('ellipsis');

  range.push(pages);
  return range;
}

export default function Pagination({
  page,
  pages,
  onPageChange,
}: PaginationProps) {
  if (pages <= 1) return null;

  const pageRange = getPageRange(page, pages);

  return (
    <div className="flex items-center justify-center gap-1 mt-10">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="flex items-center justify-center w-9 h-9 rounded-full
                   text-apple-gray-text hover:text-apple-black hover:bg-gray-100
                   disabled:opacity-30 disabled:cursor-not-allowed
                   transition-all duration-200 cursor-pointer"
      >
        <CaretLeft size={14} weight="bold" />
      </button>

      {pageRange.map((p, i) =>
        p === 'ellipsis' ? (
          <span
            key={`ellipsis-${i}`}
            className="w-9 h-9 flex items-center justify-center text-xs text-apple-gray-text"
          >
            ...
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={`w-9 h-9 rounded-full text-sm font-medium transition-all duration-200 cursor-pointer
              ${p === page
                ? 'bg-apple-blue text-white shadow-sm'
                : 'text-apple-gray-text hover:text-apple-black hover:bg-gray-100'
              }`}
          >
            {p}
          </button>
        )
      )}

      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= pages}
        className="flex items-center justify-center w-9 h-9 rounded-full
                   text-apple-gray-text hover:text-apple-black hover:bg-gray-100
                   disabled:opacity-30 disabled:cursor-not-allowed
                   transition-all duration-200 cursor-pointer"
      >
        <CaretRight size={14} weight="bold" />
      </button>
    </div>
  );
}
