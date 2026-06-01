import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  MapPin,
  CurrencyCircleDollar,
  Clock,
  ArrowRight,
} from '@phosphor-icons/react';
import Badge from '../ui/Badge';
import type { Job } from '../../hooks/useJobs';

interface JobCardProps {
  job: Job;
  index: number;
}

const sourceLabels: Record<string, string> = {
  shixiseng: '实习僧',
  niuke: '牛客',
  github: 'GitHub',
};

function formatSalary(min: number | null, max: number | null): string {
  if (min == null && max == null) return '薪资面议';
  if (min && max && min === max) return `¥${(min / 1000).toFixed(0)}k/月`;
  const parts = [];
  if (min) parts.push(`¥${(min / 1000).toFixed(0)}k`);
  if (max) parts.push(`¥${(max / 1000).toFixed(0)}k`);
  return parts.join('-') + '/月';
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return '';
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const diffHr = Math.floor(diffMs / 3600000);
  if (diffHr < 1) return '刚刚';
  if (diffHr < 24) return `${diffHr}h前`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 30) return `${diffDay}d前`;
  const diffMonth = Math.floor(diffDay / 30);
  return `${diffMonth}月前`;
}

export default function JobCard({ job, index }: JobCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: index * 0.06,
        duration: 0.4,
        ease: [0.25, 0.46, 0.45, 0.94],
      }}
      whileHover={{ y: -4 }}
      className="group"
    >
      <Link
        to={`/jobs/${job.id}`}
        className="block bg-white rounded-2xl p-6 border border-gray-200/50
                   shadow-sm hover:shadow-md transition-shadow duration-300"
      >
        {/* Header: Company + Source */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-apple-gray-text tracking-wide uppercase mb-1">
              {job.company}
            </p>
            <h3 className="text-base font-semibold text-apple-black leading-snug line-clamp-2 group-hover:text-apple-blue transition-colors duration-200">
              {job.title}
            </h3>
          </div>
          <Badge variant="default">
            {sourceLabels[job.source] || job.source}
          </Badge>
        </div>

        {/* Meta: City / Salary / Time */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-apple-gray-text mb-4">
          {job.city && (
            <span className="inline-flex items-center gap-1">
              <MapPin size={12} weight="fill" />
              {job.city}
            </span>
          )}
          {(job.salary_min || job.salary_max) && (
            <span className="inline-flex items-center gap-1 font-medium text-apple-orange">
              <CurrencyCircleDollar size={12} weight="fill" />
              {formatSalary(job.salary_min, job.salary_max)}
            </span>
          )}
          <span className="inline-flex items-center gap-1">
            <Clock size={12} />
            {timeAgo(job.posted_at)}
          </span>
        </div>

        {/* Skills */}
        {job.skills && job.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {job.skills.slice(0, 4).map((skill) => (
              <span
                key={skill}
                className="inline-block px-2.5 py-0.5 text-[11px] font-medium
                           text-apple-blue bg-apple-blue-light rounded-lg"
              >
                {skill}
              </span>
            ))}
          </div>
        )}

        {/* Description snippet */}
        {job.description && (
          <p className="text-[13px] text-apple-gray-text leading-relaxed line-clamp-2 mb-4">
            {job.description}
          </p>
        )}

        {/* Footer: View detail */}
        <div className="flex items-center justify-end">
          <span className="inline-flex items-center gap-1 text-xs font-medium text-apple-blue opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            查看详情
            <ArrowRight size={12} weight="bold" />
          </span>
        </div>
      </Link>
    </motion.div>
  );
}
