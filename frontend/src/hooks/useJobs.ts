import { useState, useEffect, useCallback, useRef } from 'react';
import api from '../lib/api';

export interface Job {
  id: string;
  title: string;
  company: string;
  city: string | null;
  job_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  description: string | null;
  skills: string[] | null;
  source: string;
  source_url: string;
  is_active: boolean;
  posted_at: string | null;
  deadline: string | null;
  created_at: string;
}

export interface JobFilters {
  keyword?: string;
  job_type?: string;
  city?: string;
  salary_min?: number;
  sort?: string;
}

interface Pagination {
  page: number;
  size: number;
  total: number;
  pages: number;
}

export function useJobs(initialFilters: JobFilters = {}) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<JobFilters>(initialFilters);
  const [pagination, setPagination] = useState<Pagination>({
    page: 1, size: 20, total: 0, pages: 1,
  });
  const abortRef = useRef<AbortController | null>(null);

  const fetchJobs = useCallback(async (page = 1, filterOverrides?: JobFilters) => {
    // Cancel previous request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);

    const currentFilters = filterOverrides ?? filters;
    const params: Record<string, string | number> = { page, size: 20 };
    if (currentFilters.keyword) params.keyword = currentFilters.keyword;
    if (currentFilters.job_type) params.job_type = currentFilters.job_type;
    if (currentFilters.city) params.city = currentFilters.city;
    if (currentFilters.salary_min) params.salary_min = currentFilters.salary_min;
    if (currentFilters.sort) params.sort = currentFilters.sort;

    try {
      const { data } = await api.get('/jobs', {
        params,
        signal: controller.signal,
      });
      if (data.code === 0) {
        setJobs(data.data.items);
        setPagination({
          page: data.data.page,
          size: data.data.size,
          total: data.data.total,
          pages: data.data.pages,
        });
      } else {
        setError(data.message);
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'CanceledError') return;
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Re-fetch when filters change (skip initial mount since fetchJobs is called via goToPage)
  const updateFilters = useCallback((newFilters: JobFilters) => {
    setFilters(newFilters);
    fetchJobs(1, newFilters);
  }, [fetchJobs]);

  const goToPage = useCallback((page: number) => {
    setPagination(p => ({ ...p, page }));
    fetchJobs(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [fetchJobs]);

  // Initial fetch
  useEffect(() => {
    fetchJobs(1);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    jobs,
    loading,
    error,
    filters,
    pagination,
    updateFilters,
    goToPage,
    refresh: () => fetchJobs(pagination.page),
  };
}
