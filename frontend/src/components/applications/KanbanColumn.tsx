import { useDroppable } from '@dnd-kit/core';
import { motion } from 'framer-motion';
import ApplicationCard from './ApplicationCard';
import type { Application } from '../../hooks/useApplications';

interface StatusConfig {
  label: string;
  icon: string;
  color: string;
  bgColor: string;
}

const STATUS_CONFIG: Record<string, StatusConfig> = {
  applied:   { label: '已投递', icon: '📥', color: 'text-blue-600',    bgColor: 'bg-blue-50' },
  screening: { label: '初筛中', icon: '👀', color: 'text-yellow-600',  bgColor: 'bg-yellow-50' },
  interview: { label: '面试中', icon: '💬', color: 'text-purple-600',  bgColor: 'bg-purple-50' },
  offer:     { label: 'Offer',  icon: '✅', color: 'text-green-600',   bgColor: 'bg-green-50' },
  rejected:  { label: '未通过', icon: '❌', color: 'text-red-600',     bgColor: 'bg-red-50' },
  closed:    { label: '已关闭', icon: '🔒', color: 'text-gray-500',    bgColor: 'bg-gray-100' },
};

interface KanbanColumnProps {
  status: string;
  applications: Application[];
  onEdit?: (app: Application) => void;
  onDelete?: (app: Application) => void;
}

export default function KanbanColumn({
  status,
  applications,
  onEdit,
  onDelete,
}: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.applied;

  return (
    <div
      ref={setNodeRef}
      className={`flex flex-col rounded-2xl border-2 transition-colors duration-200 min-h-[200px]
        ${isOver
          ? 'border-apple-blue bg-apple-blue-light/30'
          : 'border-transparent bg-gray-100/50'
        }`}
    >
      {/* Column header */}
      <div className="flex items-center gap-2 px-4 py-3">
        <span className="text-lg">{config.icon}</span>
        <h3 className={`text-sm font-semibold ${config.color}`}>
          {config.label}
        </h3>
        <span className={`ml-auto text-xs font-bold rounded-full px-2 py-0.5 ${config.bgColor} ${config.color}`}>
          {applications.length}
        </span>
      </div>

      {/* Cards */}
      <motion.div className="flex-1 px-3 pb-3 space-y-2.5" layout>
        {applications.map((app) => (
          <ApplicationCard
            key={app.id}
            application={app}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}

        {/* Empty state */}
        {applications.length === 0 && (
          <div className="flex items-center justify-center h-20 text-[11px] text-apple-gray-text">
            拖拽卡片到此处
          </div>
        )}
      </motion.div>
    </div>
  );
}
