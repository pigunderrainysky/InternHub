import { motion } from 'framer-motion';
import {
  MapPin,
  CurrencyCircleDollar,
  Clock,
  Buildings,
  ArrowSquareOut,
  CalendarCheck,
} from '@phosphor-icons/react';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import type { Job } from '../../hooks/useJobs';

interface JobDetailProps {
  job: Job;
  onApply?: () => void;
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

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export default function JobDetail({ job, onApply }: JobDetailProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main: JD */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl border border-gray-200/50 shadow-sm p-6 md:p-8">
            {/* Company + Title */}
            <div className="mb-6">
              <p className="text-sm font-medium text-apple-gray-text mb-2">
                {job.company}
              </p>
              <h1 className="text-2xl md:text-3xl font-display font-semibold text-apple-black mb-4">
                {job.title}
              </h1>
              <div className="flex flex-wrap items-center gap-3 text-sm text-apple-gray-text">
                {job.city && (
                  <span className="inline-flex items-center gap-1">
                    <MapPin size={14} weight="fill" />
                    {job.city}
                  </span>
                )}
                <span className="inline-flex items-center gap-1 font-medium text-apple-orange">
                  <CurrencyCircleDollar size={14} weight="fill" />
                  {formatSalary(job.salary_min, job.salary_max)}
                </span>
                <span className="inline-flex items-center gap-1">
                  <Clock size={14} />
                  发布于 {formatDate(job.posted_at)}
                </span>
                {job.deadline && (
                  <span className="inline-flex items-center gap-1 text-apple-red">
                    <CalendarCheck size={14} weight="fill" />
                    截止 {formatDate(job.deadline)}
                  </span>
                )}
              </div>
            </div>

            {/* Skills */}
            {job.skills && job.skills.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {job.skills.map((skill) => (
                  <span
                    key={skill}
                    className="px-3 py-1 text-xs font-medium text-apple-blue bg-apple-blue-light rounded-xl"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            )}

            {/* Description */}
            {job.description && (
              <div className="border-t border-gray-100 pt-6">
                <h2 className="text-lg font-semibold text-apple-black mb-4">
                  岗位描述
                </h2>
                <pre className="text-sm text-apple-black leading-relaxed whitespace-pre-wrap font-sans">
                  {job.description}
                </pre>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="sticky top-20 space-y-4">
            {/* Company Card */}
            <div className="bg-white rounded-2xl border border-gray-200/50 shadow-sm p-6">
              <h3 className="text-sm font-semibold text-apple-black mb-3">
                公司信息
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2 text-apple-gray-text">
                  <Buildings size={16} />
                  <span>{job.company}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="default">
                    {sourceLabels[job.source] || job.source}
                  </Badge>
                  {job.job_type && (
                    <Badge variant="default">
                      {job.job_type === 'tech' ? '技术' :
                       job.job_type === 'product' ? '产品' :
                       job.job_type === 'operation' ? '运营' :
                       job.job_type === 'finance' ? '金融' :
                       job.job_type === 'design' ? '设计' : job.job_type}
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-white rounded-2xl border border-gray-200/50 shadow-sm p-6 space-y-3">
              <Button
                onClick={onApply}
                className="w-full bg-gradient-to-r from-[#0071E3] to-[#5AC8FA] hover:from-[#0077ED] hover:to-[#6CD4FF] shadow-md"
                size="md"
              >
                投递此岗位
              </Button>
              <a
                href={job.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-1.5 w-full px-6 py-2.5
                           text-sm font-medium text-apple-gray-text hover:text-apple-blue
                           rounded-full transition-colors duration-200"
              >
                <ArrowSquareOut size={14} />
                查看原文
              </a>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
