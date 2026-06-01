import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';

export interface ApplicationJob {
  id: string;
  title: string;
  company: string;
  city: string | null;
  job_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  source: string;
  source_url: string;
}

export interface Application {
  id: string;
  user_id: string;
  job_id: string;
  status: string;
  notes: string | null;
  applied_at: string | null;
  updated_at: string | null;
  job: ApplicationJob | null;
}

export type Columns = Record<string, Application[]>;

export function useApplications() {
  const [columns, setColumns] = useState<Columns>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchApplications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get('/applications');
      if (data.code === 0) {
        setColumns(data.data.columns);
      } else {
        setError(data.message);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);

  // Move card to a new status (optimistic update)
  const moveApplication = useCallback(
    async (applicationId: string, newStatus: string) => {
      // Find the card in current columns
      let card: Application | null = null;
      let fromStatus = '';
      for (const [status, apps] of Object.entries(columns)) {
        const found = apps.find((a) => a.id === applicationId);
        if (found) {
          card = found;
          fromStatus = status;
          break;
        }
      }
      if (!card || fromStatus === newStatus) return;

      // Optimistic update
      setColumns((prev) => {
        const updated = { ...prev };
        updated[fromStatus] = (updated[fromStatus] || []).filter(
          (a) => a.id !== applicationId
        );
        updated[newStatus] = [
          { ...card!, status: newStatus },
          ...(updated[newStatus] || []),
        ];
        return updated;
      });

      // Persist
      try {
        await api.patch(`/applications/${applicationId}/status`, {
          status: newStatus,
        });
      } catch {
        // Revert on failure
        fetchApplications();
      }
    },
    [columns, fetchApplications]
  );

  // Create new application
  const addApplication = useCallback(
    async (jobId: string) => {
      const { data } = await api.post('/applications', { job_id: jobId });
      if (data.code === 0) {
        await fetchApplications(); // Refresh to get full data
      }
      return data;
    },
    [fetchApplications]
  );

  // Update notes
  const updateNotes = useCallback(
    async (applicationId: string, notes: string) => {
      try {
        await api.put(`/applications/${applicationId}`, { notes });
        setColumns((prev) => {
          const updated = { ...prev };
          for (const status of Object.keys(updated)) {
            updated[status] = updated[status].map((a) =>
              a.id === applicationId ? { ...a, notes } : a
            );
          }
          return updated;
        });
      } catch {
        // Revert on failure
        fetchApplications();
      }
    },
    [fetchApplications]
  );

  // Delete application
  const deleteApplication = useCallback(
    async (applicationId: string) => {
      try {
        await api.delete(`/applications/${applicationId}`);
        setColumns((prev) => {
          const updated = { ...prev };
          for (const status of Object.keys(updated)) {
            updated[status] = updated[status].filter(
              (a) => a.id !== applicationId
            );
          }
          return updated;
        });
      } catch {
        // Revert on failure
        fetchApplications();
      }
    },
    [fetchApplications]
  );

  return {
    columns,
    loading,
    error,
    refresh: fetchApplications,
    moveApplication,
    addApplication,
    updateNotes,
    deleteApplication,
  };
}
