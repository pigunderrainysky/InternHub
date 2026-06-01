import { useDraggable } from '@dnd-kit/core';
import { motion } from 'framer-motion';
import { PencilSimple, TrashSimple, MapPin } from '@phosphor-icons/react';
import type { Application } from '../../hooks/useApplications';

interface ApplicationCardProps {
  application: Application;
  onEdit?: (app: Application) => void;
  onDelete?: (app: Application) => void;
}

function formatSalary(min: number | null, max: number | null): string | null {
  if (min == null && max == null) return null;
  if (min && max && min === max) return `¥${(min / 1000).toFixed(0)}k`;
  const parts = [];
  if (min) parts.push(`¥${(min / 1000).toFixed(0)}k`);
  if (max) parts.push(`¥${(max / 1000).toFixed(0)}k`);
  return parts.join('-');
}

export default function ApplicationCard({
  application,
  onEdit,
  onDelete,
}: ApplicationCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({
      id: application.id,
      data: { application },
    });

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        zIndex: isDragging ? 50 : undefined,
        opacity: isDragging ? 0.85 : undefined,
      }
    : undefined;

  const job = application.job;

  return (
    <motion.div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      layout
      className={`bg-white rounded-xl border border-gray-200/60 p-3.5
                  shadow-sm hover:shadow-md cursor-grab active:cursor-grabbing
                  touch-none select-none
                  transition-shadow duration-200
                  ${isDragging ? 'shadow-lg ring-2 ring-apple-blue/20' : ''}`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <p className="text-[11px] font-medium text-apple-gray-text truncate">
            {job?.company || '—'}
          </p>
          <p className="text-sm font-semibold text-apple-black leading-snug line-clamp-2">
            {job?.title || '未知岗位'}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-0.5 shrink-0" onClick={(e) => e.stopPropagation()}>
          {onEdit && (
            <button
              onClick={() => onEdit(application)}
              className="p-1 text-apple-gray-text hover:text-apple-blue rounded-lg hover:bg-blue-50 transition-colors cursor-pointer"
              title="编辑备注"
            >
              <PencilSimple size={13} />
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(application)}
              className="p-1 text-apple-gray-text hover:text-apple-red rounded-lg hover:bg-red-50 transition-colors cursor-pointer"
              title="删除"
            >
              <TrashSimple size={13} />
            </button>
          )}
        </div>
      </div>

      {/* Meta info */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-apple-gray-text">
        {job?.city && (
          <span className="inline-flex items-center gap-0.5">
            <MapPin size={10} weight="fill" />
            {job.city}
          </span>
        )}
        {formatSalary(job?.salary_min ?? null, job?.salary_max ?? null) && (
          <span className="font-medium text-apple-orange">
            {formatSalary(job?.salary_min ?? null, job?.salary_max ?? null)}
          </span>
        )}
      </div>

      {/* Notes indicator */}
      {application.notes && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <p className="text-[11px] text-apple-gray-text line-clamp-2">
            📝 {application.notes}
          </p>
        </div>
      )}
    </motion.div>
  );
}
