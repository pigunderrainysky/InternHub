import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/ui/Button';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [nickname, setNickname] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('两次密码不一致');
      return;
    }
    if (password.length < 6) {
      setError('密码至少 6 位');
      return;
    }

    setSubmitting(true);
    try {
      await register(email, password, nickname);
      navigate('/login', { state: { registered: true } });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '注册失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-[20px] shadow-sm border border-gray-200/50 p-8">
          <h1 className="text-2xl font-display font-semibold text-apple-black text-center mb-2">
            创建账号
          </h1>
          <p className="text-sm text-apple-gray-text text-center mb-8">
            加入 InternHub，发现属于你的实习机会
          </p>

          {error && (
            <div className="mb-6 p-3 rounded-xl bg-red-50 text-sm text-apple-red text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-apple-black mb-1.5">
                邮箱
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm text-apple-black placeholder:text-apple-gray-text focus:outline-none focus:border-apple-blue focus:ring-[3px] focus:ring-apple-blue/10 transition-all duration-200"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-apple-black mb-1.5">
                昵称
              </label>
              <input
                type="text"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm text-apple-black placeholder:text-apple-gray-text focus:outline-none focus:border-apple-blue focus:ring-[3px] focus:ring-apple-blue/10 transition-all duration-200"
                placeholder="如何称呼你？"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-apple-black mb-1.5">
                密码
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm text-apple-black placeholder:text-apple-gray-text focus:outline-none focus:border-apple-blue focus:ring-[3px] focus:ring-apple-blue/10 transition-all duration-200"
                placeholder="至少 6 位"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-apple-black mb-1.5">
                确认密码
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm text-apple-black placeholder:text-apple-gray-text focus:outline-none focus:border-apple-blue focus:ring-[3px] focus:ring-apple-blue/10 transition-all duration-200"
                placeholder="再次输入密码"
              />
            </div>

            <Button
              type="submit"
              disabled={submitting}
              className="w-full"
              size="lg"
            >
              {submitting ? '注册中...' : '注册'}
            </Button>
          </form>

          <p className="mt-6 text-sm text-center text-apple-gray-text">
            已有账号？{' '}
            <Link
              to="/login"
              className="text-apple-blue font-medium hover:underline"
            >
              去登录
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
