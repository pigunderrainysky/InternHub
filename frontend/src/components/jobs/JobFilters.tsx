import { CaretDown } from '@phosphor-icons/react';
import Tag from '../ui/Tag';
import { JOB_TYPES, CITIES, SORT_OPTIONS } from '../../lib/constants';
import type { JobFilters as Filters } from '../../hooks/useJobs';

interface JobFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  typeCounts?: Record<string, number>;
}

export default function JobFilters({ filters, onChange, typeCounts }: JobFiltersProps) {
  const handleTypeClick = (value: string) => {
    onChange({ ...filters, job_type: filters.job_type === value ? undefined : value });
  };

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 mb-8">
      {/* Job type tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 flex-1">
        <Tag
          variant={!filters.job_type ? 'active' : 'default'}
          onClick={() => onChange({ ...filters, job_type: undefined })}
        >
          全部
        </Tag>
        {JOB_TYPES.map(({ value, label }) => (
          <Tag
            key={value}
            variant={filters.job_type === value ? 'active' : 'default'}
            onClick={() => handleTypeClick(value)}
          >
            {label}
            {typeCounts?.[value] ? ` (${typeCounts[value]})` : ''}
          </Tag>
        ))}
      </div>

      {/* City + Sort selects */}
      <div className="flex items-center gap-2 shrink-0">
        {/* City select */}
        <div className="relative">
          <select
            value={filters.city || ''}
            onChange={(e) =>
              onChange({ ...filters, city: e.target.value || undefined })
            }
            className="appearance-none bg-white border border-gray-200 rounded-full px-4 py-1.5 pr-8
                       text-xs font-medium text-apple-black cursor-pointer
                       focus:outline-none focus:border-apple-blue focus:ring-[3px] focus:ring-apple-blue/10
                       transition-all duration-200"
          >
            <option value="">📍 全部城市</option>
            {CITIES.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
          <CaretDown
            size={12}
            weight="bold"
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-apple-gray-text pointer-events-none"
          />
        </div>

        {/* Sort select */}
        <div className="relative">
          <select
            value={filters.sort || 'latest'}
            onChange={(e) =>
              onChange({ ...filters, sort: e.target.value })
            }
            className="appearance-none bg-white border border-gray-200 rounded-full px-4 py-1.5 pr-8
                       text-xs font-medium text-apple-black cursor-pointer
                       focus:outline-none focus:border-apple-blue focus:ring-[3px] focus:ring-apple-blue/10
                       transition-all duration-200"
          >
            {SORT_OPTIONS.map(({ value, label }) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <CaretDown
            size={12}
            weight="bold"
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-apple-gray-text pointer-events-none"
          />
        </div>
      </div>
    </div>
  );
}
