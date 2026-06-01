import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Spinner, SmileySad, ArrowLeft } from '@phosphor-icons/react';
import api from '../lib/api';
import JobDetail from '../components/jobs/JobDetail';
import { useAuth } from '../hooks/useAuth';
import type { Job } from '../hooks/useJobs';

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    api
      .get(`/jobs/${id}`)
      .then(({ data }) => {
        if (data.code === 0) {
          setJob(data.data);
        } else {
          setError(data.message);
        }
      })
      .catch((err) => {
        setError(err.response?.status === 404 ? '岗位不存在或已下线' : '加载失败');
      })
      .finally(() => setLoading(false));
  }, [id]);

  const handleApply = async () => {
    if (!user) {
      navigate('/login');
      return;
    }
    try {
      await api.post('/applications', { job_id: id });
      navigate('/dashboard');
    } catch {
      // If already applied, still go to dashboard
      navigate('/dashboard');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner size={32} className="animate-spin text-apple-gray-text" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-apple-gray-text">
        <SmileySad size={40} weight="duotone" className="mb-4 text-apple-red" />
        <p className="text-sm mb-4">{error || '岗位未找到'}</p>
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm text-apple-blue font-medium hover:underline"
        >
          <ArrowLeft size={14} />
          返回首页
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Back link */}
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-sm text-apple-gray-text hover:text-apple-blue mb-6 transition-colors duration-200"
      >
        <ArrowLeft size={14} />
        返回列表
      </Link>

      <JobDetail job={job} onApply={handleApply} />
    </div>
  );
}
