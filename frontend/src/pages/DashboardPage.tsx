import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from '@phosphor-icons/react';
import KanbanBoard from '../components/applications/KanbanBoard';
import ApplicationForm from '../components/applications/ApplicationForm';
import Button from '../components/ui/Button';
import { useAuth } from '../hooks/useAuth';
import { useApplications, type Application } from '../hooks/useApplications';

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const {
    columns,
    loading,
    error,
    refresh,
    moveApplication,
    addApplication,
    updateNotes,
    deleteApplication,
  } = useApplications();

  const [modalOpen, setModalOpen] = useState(false);
  const [editingApp, setEditingApp] = useState<Application | null>(null);

  // Redirect to login if not authenticated
  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-apple-gray-text">
        <p className="text-sm mb-3">请先登录以管理投递记录</p>
        <Button onClick={() => navigate('/login')}>去登录</Button>
      </div>
    );
  }

  const handleEdit = (app: Application) => {
    setEditingApp(app);
    setModalOpen(true);
  };

  const handleDelete = async (app: Application) => {
    if (!window.confirm('确定要删除这条投递记录吗？')) return;
    await deleteApplication(app.id);
  };

  const handleSave = async (data: { job_id?: string; notes?: string }) => {
    if (editingApp) {
      await updateNotes(editingApp.id, data.notes || '');
    } else if (data.job_id) {
      await addApplication(data.job_id);
    }
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setEditingApp(null);
  };

  // Count total applications
  const totalApps = Object.values(columns).reduce(
    (sum, apps) => sum + apps.length,
    0
  );

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-display font-semibold text-apple-black mb-1">
            我的投递
          </h1>
          <p className="text-sm text-apple-gray-text">
            {totalApps > 0
              ? `共 ${totalApps} 个投递记录`
              : '拖拽卡片管理投递进度'}
          </p>
        </div>
        <Button
          onClick={() => {
            setEditingApp(null);
            setModalOpen(true);
          }}
          className="gap-2"
        >
          <Plus size={16} weight="bold" />
          新增投递
        </Button>
      </div>

      {/* Kanban */}
      <KanbanBoard
        columns={columns}
        loading={loading}
        error={error}
        onMove={moveApplication}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onRetry={refresh}
      />

      {/* Modal */}
      <ApplicationForm
        open={modalOpen}
        onClose={handleCloseModal}
        onSave={handleSave}
        application={editingApp}
      />
    </div>
  );
}
