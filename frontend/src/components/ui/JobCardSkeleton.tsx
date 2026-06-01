import { motion } from 'framer-motion';

interface JobCardSkeletonProps {
  count?: number;
}

function SkeletonCard({ index }: { index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.3 }}
      className="bg-white rounded-2xl p-6 border border-gray-200/50 shadow-sm"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 space-y-2">
          <div className="h-3 bg-gray-100 rounded-full w-20 animate-pulse" />
          <div className="h-5 bg-gray-100 rounded-full w-48 animate-pulse" />
        </div>
        <div className="h-5 bg-gray-100 rounded-lg w-14 animate-pulse" />
      </div>
      <div className="flex items-center gap-4 mb-4">
        <div className="h-3 bg-gray-100 rounded-full w-12 animate-pulse" />
        <div className="h-3 bg-gray-100 rounded-full w-20 animate-pulse" />
        <div className="h-3 bg-gray-100 rounded-full w-14 animate-pulse" />
      </div>
      <div className="flex gap-1.5 mb-4">
        <div className="h-5 bg-gray-100 rounded-lg w-14 animate-pulse" />
        <div className="h-5 bg-gray-100 rounded-lg w-16 animate-pulse" />
        <div className="h-5 bg-gray-100 rounded-lg w-12 animate-pulse" />
      </div>
      <div className="space-y-2">
        <div className="h-3 bg-gray-100 rounded-full w-full animate-pulse" />
        <div className="h-3 bg-gray-100 rounded-full w-3/4 animate-pulse" />
      </div>
    </motion.div>
  );
}

export default function JobCardSkeleton({ count = 6 }: JobCardSkeletonProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      {Array.from({ length: count }, (_, i) => (
        <SkeletonCard key={i} index={i} />
      ))}
    </div>
  );
}
