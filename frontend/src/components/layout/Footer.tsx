import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="border-t border-gray-200/50 bg-white/50 mt-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-apple-gray-text">
          <div className="flex items-center gap-1">
            <span className="font-semibold text-apple-black">InternHub</span>
            <span>— 实习雷达 · 发现最适合你的实习机会</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/" className="hover:text-apple-blue transition-colors">
              首页
            </Link>
            <Link to="/subscription" className="hover:text-apple-blue transition-colors">
              订阅
            </Link>
            <Link to="/dashboard" className="hover:text-apple-blue transition-colors">
              投递记录
            </Link>
            <span className="text-gray-300">·</span>
            <span>© 2026 InternHub</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
