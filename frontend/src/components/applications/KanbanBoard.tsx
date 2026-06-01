import { DndContext, type DragEndEvent } from '@dnd-kit/core';
import { Spinner, SmileySad } from '@phosphor-icons/react';
import KanbanColumn from './KanbanColumn';
import type { Application, Columns } from '../../hooks/useApplications';

interface KanbanBoardProps {
  columns: Columns;
  loading: boolean;
  error: string | null;
  onMove: (applicationId: string, newStatus: string) => void;
  onEdit?: (app: Application) => void;
  onDelete?: (app: Application) => void;
  onRetry?: () => void;
}

const COLUMN_ORDER = [
  'applied',
  'screening',
  'interview',
  'offer',
  'rejected',
  'closed',
];

export default function KanbanBoard({
  columns,
  loading,
  error,
  onMove,
  onEdit,
  onDelete,
  onRetry,
}: KanbanBoardProps) {
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const applicationId = active.id as string;
    const newStatus = over.id as string;

    // Validate: over must be a column id, not another card
    if (!COLUMN_ORDER.includes(newStatus)) return;

    onMove(applicationId, newStatus);
  };

  // Loading
  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner size={32} className="animate-spin text-apple-gray-text" />
      </div>
    );
  }

  // Error
  if (error) {
    return (
      <div className="flex flex-col items-center py-24 text-apple-gray-text">
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

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {COLUMN_ORDER.map((status) => (
          <KanbanColumn
            key={status}
            status={status}
            applications={columns[status] || []}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}
      </div>
    </DndContext>
  );
}
