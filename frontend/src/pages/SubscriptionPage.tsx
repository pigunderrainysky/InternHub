import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Spinner } from '@phosphor-icons/react';
import SubscriptionForm from '../components/subscriptions/SubscriptionForm';
import Button from '../components/ui/Button';
import { useAuth } from '../hooks/useAuth';
import api from '../lib/api';

interface SubscriptionData {
  keywords: string[];
  cities: string[];
  job_types: string[];
  frequency: string;
  enabled: boolean;
}

export default function SubscriptionPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [subscription, setSubscription] = useState<SubscriptionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSubscription = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get('/subscriptions');
      if (data.code === 0) {
        setSubscription(data.data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) fetchSubscription();
    else setLoading(false);
  }, [user, fetchSubscription]);

  const handleSave = async (data: SubscriptionData) => {
    setSaving(true);
    setError(null);
    try {
      const { data: res } = await api.post('/subscriptions', data);
      if (res.code === 0) {
        setSubscription(res.data);
      } else {
        setError(res.message);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '保存失败');
    } finally {
      setSaving(false);
    }
  };

  // Not authenticated
  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-apple-gray-text">
        <p className="text-sm mb-3">请先登录以管理订阅</p>
        <Button onClick={() => navigate('/login')}>去登录</Button>
      </div>
    );
  }

  // Loading
  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner size={32} className="animate-spin text-apple-gray-text" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-display font-semibold text-apple-black mb-2">
          订阅设置
        </h1>
        <p className="text-sm text-apple-gray-text">
          设置关键词和城市，有新岗位匹配时我们会邮件通知你
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 text-sm text-apple-red">
          {error}
        </div>
      )}

      <SubscriptionForm
        initial={subscription}
        onSave={handleSave}
        loading={saving}
      />

      {/* Digest info */}
      <p className="mt-6 text-xs text-apple-gray-text text-center">
        {subscription?.enabled !== false
          ? `当前推送频率：${subscription?.frequency === 'daily' ? '每日' : '每周'} · 我们不会发送垃圾邮件`
          : '推送已暂停 · 开启后可接收岗位速递'}
      </p>
    </div>
  );
}
