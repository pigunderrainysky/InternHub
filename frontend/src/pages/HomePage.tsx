import { useSearchParams } from 'react-router-dom';
import HeroSection from '../components/jobs/HeroSection';
import JobFilters from '../components/jobs/JobFilters';
import JobList from '../components/jobs/JobList';
import JobCardSkeleton from '../components/ui/JobCardSkeleton';
import Pagination from '../components/ui/Pagination';
import { useJobs, type JobFilters as Filters } from '../hooks/useJobs';

export default function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const initialFilters: Filters = {
    keyword: searchParams.get('keyword') || undefined,
    job_type: searchParams.get('job_type') || undefined,
    city: searchParams.get('city') || undefined,
    sort: searchParams.get('sort') || 'latest',
  };

  const { jobs, loading, error, filters, pagination, updateFilters, goToPage, refresh } =
    useJobs(initialFilters);

  const handleFiltersChange = (newFilters: Filters) => {
    // Sync to URL
    const params = new URLSearchParams();
    if (newFilters.keyword) params.set('keyword', newFilters.keyword);
    if (newFilters.job_type) params.set('job_type', newFilters.job_type);
    if (newFilters.city) params.set('city', newFilters.city);
    if (newFilters.sort && newFilters.sort !== 'latest') params.set('sort', newFilters.sort);
    setSearchParams(params, { replace: true });

    updateFilters(newFilters);
  };

  const handleSearch = (keyword: string) => {
    handleFiltersChange({ ...filters, keyword: keyword || undefined });
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <HeroSection
        defaultKeyword={initialFilters.keyword}
        onSearch={handleSearch}
      />

      <JobFilters
        filters={filters}
        onChange={handleFiltersChange}
      />

      {/* Skeleton on initial load, JobList for subsequent loads */}
      {loading && jobs.length === 0 ? (
        <JobCardSkeleton count={6} />
      ) : (
        <JobList
          jobs={jobs}
          loading={loading}
          error={error}
          onRetry={refresh}
        />
      )}

      <Pagination
        page={pagination.page}
        pages={pagination.pages}
        onPageChange={goToPage}
      />

      {/* Total count */}
      {pagination.total > 0 && (
        <p className="text-center text-xs text-apple-gray-text mt-6">
          共 {pagination.total} 个岗位
        </p>
      )}
    </div>
  );
}
