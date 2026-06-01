import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, MagnifyingGlass } from '@phosphor-icons/react';
import Button from '../ui/Button';
import api from '../../lib/api';
import type { Application } from '../../hooks/useApplications';

interface JobOption {
  id: string;
  title: string;
  company: string;
}

interface ApplicationFormProps {
  open: boolean;
  onClose: () => void;
  onSave: (data: { job_id?: string; notes?: string }) => Promise<void>;
  application?: Application | null; // null = create mode
}

export default function ApplicationForm({
  open,
  onClose,
  onSave,
  application,
}: ApplicationFormProps) {
  const isEdit = application !== null && application !== undefined;

  const [jobSearch, setJobSearch] = useState('');
  const [jobResults, setJobResults] = useState<JobOption[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobOption | null>(null);
  const [notes, setNotes] = useState(application?.notes || '');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const searchTimer = useRef<ReturnType<typeof setTimeout>>();

  // Reset form on open
  useEffect(() => {
    if (open) {
      setNotes(application?.notes || '');
      setSelectedJob(null);
      setJobSearch('');
      setJobResults([]);
      setError('');
    }
  }, [open, application]);

  // Job search with debounce (only in create mode)
  const handleJobSearch = (value: string) => {
    setJobSearch(value);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    if (!value.trim()) {
      setJobResults([]);
      return;
    }
    searchTimer.current = setTimeout(async () => {
      try {
        const { data } = await api.get('/jobs', {
          params: { keyword: value, size: 5 },
        });
        if (data.code === 0) {
          setJobResults(data.data.items || []);
        }
      } catch {
        // Silently fail search
      }
    }, 300);
  };

  const handleSubmit = async () => {
    setError('');
    if (!isEdit && !selectedJob) {
      setError('请选择一个岗位');
      return;
    }
    setSubmitting(true);
    try {
      await onSave({
        job_id: selectedJob?.id,
        notes: notes || undefined,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '操作失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/20 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-md bg-white rounded-2xl shadow-xl border border-gray-200/50 p-6"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-apple-black">
                {isEdit ? '编辑备注' : '新增投递'}
              </h2>
              <button
                onClick={onClose}
                className="p-1.5 text-apple-gray-text hover:text-apple-black rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            {/* Error */}
            {error && (
              <div className="mb-4 p-3 rounded-xl bg-red-50 text-sm text-apple-red">
                {error}
              </div>
            )}

            {/* Edit mode: show job info */}
            {isEdit && application?.job && (
              <div className="mb-4 p-3 rounded-xl bg-gray-50">
                <p className="text-xs text-apple-gray-text">
                  {application.job.company}
                </p>
                <p className="text-sm font-medium text-apple-black">
                  {application.job.title}
                </p>
              </div>
            )}

            {/* Create mode: job search */}
            {!isEdit && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-apple-black mb-1.5">
                  选择岗位
                </label>
                {selectedJob ? (
                  <div className="flex items-center justify-between p-3 rounded-xl bg-apple-blue-light">
                    <div>
                      <p className="text-xs text-apple-gray-text">
                        {selectedJob.company}
                      </p>
                      <p className="text-sm font-medium text-apple-black">
                        {selectedJob.title}
                      </p>
                    </div>
                    <button
                      onClick={() => setSelectedJob(null)}
                      className="text-xs text-apple-gray-text hover:text-apple-red cursor-pointer"
                    >
                      取消
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="relative">
                      <MagnifyingGlass
                        size={14}
                        className="absolute left-3 top-1/2 -translate-y-1/2 text-apple-gray-text"
                      />
                      <input
                        type="text"
                        value={jobSearch}
                        onChange={(e) => handleJobSearch(e.target.value)}
                        placeholder="搜索岗位名称..."
                        className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 text-sm
                                   placeholder:text-apple-gray-text focus:outline-none focus:border-apple-blue
                                   focus:ring-[3px] focus:ring-apple-blue/10 transition-all duration-200"
                      />
                    </div>
                    {jobResults.length > 0 && (
                      <div className="mt-2 border border-gray-200 rounded-xl overflow-hidden">
                        {jobResults.map((job) => (
                          <button
                            key={job.id}
                            onClick={() => {
                              setSelectedJob(job);
                              setJobResults([]);
                              setJobSearch('');
                            }}
                            className="w-full text-left px-4 py-2.5 hover:bg-gray-50 text-sm
                                       border-b border-gray-100 last:border-0 cursor-pointer
                                       transition-colors duration-100"
                          >
                            <span className="text-apple-black">{job.title}</span>
                            <span className="text-apple-gray-text ml-2 text-xs">
                              {job.company}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* Notes */}
            <div className="mb-5">
              <label className="block text-sm font-medium text-apple-black mb-1.5">
                备注
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={4}
                placeholder="添加备注（可选）..."
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm
                           placeholder:text-apple-gray-text resize-none
                           focus:outline-none focus:border-apple-blue focus:ring-[3px] focus:ring-apple-blue/10
                           transition-all duration-200"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-3 justify-end">
              <Button variant="secondary" onClick={onClose}>
                取消
              </Button>
              <Button onClick={handleSubmit} disabled={submitting}>
                {submitting ? '保存中...' : isEdit ? '保存' : '添加投递'}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
