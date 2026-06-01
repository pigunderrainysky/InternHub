import { useState, useEffect, type KeyboardEvent } from 'react';
import { X } from '@phosphor-icons/react';
import Button from '../ui/Button';
import { JOB_TYPES, CITIES, FREQUENCY_OPTIONS } from '../../lib/constants';

interface SubscriptionData {
  keywords: string[];
  cities: string[];
  job_types: string[];
  frequency: string;
  enabled: boolean;
}

interface SubscriptionFormProps {
  initial?: SubscriptionData | null;
  onSave: (data: SubscriptionData) => Promise<void>;
  loading?: boolean;
}

export default function SubscriptionForm({
  initial,
  onSave,
  loading = false,
}: SubscriptionFormProps) {
  const [keywords, setKeywords] = useState<string[]>(initial?.keywords || []);
  const [cities, setCities] = useState<string[]>(initial?.cities || []);
  const [jobTypes, setJobTypes] = useState<string[]>(initial?.job_types || []);
  const [frequency, setFrequency] = useState(initial?.frequency || 'daily');
  const [enabled, setEnabled] = useState(initial?.enabled ?? true);
  const [keywordInput, setKeywordInput] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (initial) {
      setKeywords(initial.keywords || []);
      setCities(initial.cities || []);
      setJobTypes(initial.job_types || []);
      setFrequency(initial.frequency || 'daily');
      setEnabled(initial.enabled ?? true);
    }
  }, [initial]);

  const handleAddKeyword = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && keywordInput.trim()) {
      e.preventDefault();
      const kw = keywordInput.trim();
      if (!keywords.includes(kw)) {
        setKeywords([...keywords, kw]);
      }
      setKeywordInput('');
    }
  };

  const removeKeyword = (kw: string) => {
    setKeywords(keywords.filter((k) => k !== kw));
  };

  const toggleCity = (city: string) => {
    setCities((prev) =>
      prev.includes(city) ? prev.filter((c) => c !== city) : [...prev, city]
    );
  };

  const toggleJobType = (type: string) => {
    setJobTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const handleSave = async () => {
    await onSave({ keywords, cities, job_types: jobTypes, frequency, enabled });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200/50 shadow-sm p-6 md:p-8 space-y-8">
      {/* Keywords */}
      <div>
        <h3 className="text-sm font-semibold text-apple-black mb-2">关键词</h3>
        <p className="text-xs text-apple-gray-text mb-3">
          岗位标题或描述中包含这些关键词时，将推送给你
        </p>
        <div className="flex flex-wrap gap-2 mb-3">
          {keywords.map((kw) => (
            <span
              key={kw}
              className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium
                         text-apple-blue bg-apple-blue-light rounded-xl"
            >
              {kw}
              <button
                onClick={() => removeKeyword(kw)}
                className="hover:text-apple-red transition-colors cursor-pointer"
              >
                <X size={12} weight="bold" />
              </button>
            </span>
          ))}
        </div>
        <input
          type="text"
          value={keywordInput}
          onChange={(e) => setKeywordInput(e.target.value)}
          onKeyDown={handleAddKeyword}
          placeholder="输入关键词后按回车添加..."
          className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm
                     placeholder:text-apple-gray-text focus:outline-none focus:border-apple-blue
                     focus:ring-[3px] focus:ring-apple-blue/10 transition-all duration-200"
        />
      </div>

      {/* Cities */}
      <div>
        <h3 className="text-sm font-semibold text-apple-black mb-2">城市</h3>
        <p className="text-xs text-apple-gray-text mb-3">选择你想工作的城市（可多选）</p>
        <div className="flex flex-wrap gap-1.5">
          {CITIES.map((city) => (
            <button
              key={city}
              onClick={() => toggleCity(city)}
              className={`px-3 py-1.5 text-xs font-medium rounded-xl transition-all duration-200 cursor-pointer
                ${cities.includes(city)
                  ? 'bg-apple-blue text-white shadow-sm'
                  : 'bg-gray-100 text-apple-gray-text hover:bg-gray-200'
                }`}
            >
              {city}
            </button>
          ))}
        </div>
      </div>

      {/* Job Types */}
      <div>
        <h3 className="text-sm font-semibold text-apple-black mb-2">岗位类型</h3>
        <p className="text-xs text-apple-gray-text mb-3">选择你感兴趣的岗位类型（可多选）</p>
        <div className="flex flex-wrap gap-1.5">
          {JOB_TYPES.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => toggleJobType(value)}
              className={`px-3 py-1.5 text-xs font-medium rounded-xl transition-all duration-200 cursor-pointer
                ${jobTypes.includes(value)
                  ? 'bg-apple-blue text-white shadow-sm'
                  : 'bg-gray-100 text-apple-gray-text hover:bg-gray-200'
                }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Frequency + Enabled */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-6">
        <div>
          <h3 className="text-sm font-semibold text-apple-black mb-2">推送频率</h3>
          <div className="flex gap-2">
            {FREQUENCY_OPTIONS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => setFrequency(value)}
                className={`px-4 py-2 text-sm font-medium rounded-full transition-all duration-200 cursor-pointer
                  ${frequency === value
                    ? 'bg-apple-blue text-white shadow-sm'
                    : 'bg-gray-100 text-apple-gray-text hover:bg-gray-200'
                  }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3 pt-1">
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-10 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-apple-blue/20
                            rounded-full peer peer-checked:after:translate-x-full
                            peer-checked:after:border-white after:content-['']
                            after:absolute after:top-[2px] after:start-[2px]
                            after:bg-white after:rounded-full after:h-5 after:w-5
                            after:transition-all peer-checked:bg-apple-blue">
            </div>
          </label>
          <span className="text-sm text-apple-gray-text">
            {enabled ? '已开启推送' : '已暂停推送'}
          </span>
        </div>
      </div>

      {/* Save */}
      <div className="flex items-center gap-3 pt-2">
        <Button onClick={handleSave} disabled={loading}>
          {loading ? '保存中...' : saved ? '✅ 已保存' : '保存设置'}
        </Button>
        {saved && (
          <span className="text-xs text-apple-green font-medium">
            订阅设置已更新
          </span>
        )}
      </div>
    </div>
  );
}
