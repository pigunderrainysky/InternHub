import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/ui/Button';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '登录失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-[20px] shadow-sm border border-gray-200/50 p-8">
          <h1 className="text-2xl font-display font-semibold text-apple-black text-center mb-2">
            欢迎回来
          </h1>
          <p className="text-sm text-apple-gray-text text-center mb-8">
            登录 InternHub 管理投递和订阅
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
                密码
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm text-apple-black placeholder:text-apple-gray-text focus:outline-none focus:border-apple-blue focus:ring-[3px] focus:ring-apple-blue/10 transition-all duration-200"
                placeholder="••••••••"
              />
            </div>

            <Button
              type="submit"
              disabled={submitting}
              className="w-full"
              size="lg"
            >
              {submitting ? '登录中...' : '登录'}
            </Button>
          </form>

          <p className="mt-6 text-sm text-center text-apple-gray-text">
            还没有账号？{' '}
            <Link
              to="/register"
              className="text-apple-blue font-medium hover:underline"
            >
              立即注册
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
