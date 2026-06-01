import { motion } from 'framer-motion';
import { Spinner, SmileySad } from '@phosphor-icons/react';
import JobCard from './JobCard';
import type { Job } from '../../hooks/useJobs';

interface JobListProps {
  jobs: Job[];
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}

export default function JobList({ jobs, loading, error, onRetry }: JobListProps) {
  // Loading state
  if (loading && jobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-apple-gray-text">
        <Spinner size={32} className="animate-spin mb-4" />
        <p className="text-sm">正在加载岗位...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-apple-gray-text">
        <SmileySad size={40} weight="duotone" className="mb-4 text-apple-red" />
        <p className="text-sm mb-3">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-sm text-apple-blue font-medium hover:underline cursor-pointer"
          >
            重试
          </button>
        )}
      </div>
    );
  }

  // Empty state
  if (!loading && jobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-apple-gray-text">
        <SmileySad size={40} weight="duotone" className="mb-4" />
        <p className="text-sm mb-1">暂无匹配的岗位</p>
        <p className="text-xs">试试其他关键词或筛选条件？</p>
      </div>
    );
  }

  return (
    <motion.div
      className="grid grid-cols-1 md:grid-cols-2 gap-5"
      initial="hidden"
      animate="visible"
      variants={{
        hidden: {},
        visible: {
          transition: { staggerChildren: 0.06 },
        },
      }}
    >
      {jobs.map((job, i) => (
        <JobCard key={job.id} job={job} index={i} />
      ))}

      {/* Loading more indicator */}
      {loading && jobs.length > 0 && (
        <div className="col-span-full flex justify-center py-8">
          <Spinner size={20} className="animate-spin text-apple-gray-text" />
        </div>
      )}
    </motion.div>
  );
}
