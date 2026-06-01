import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { List, X } from '@phosphor-icons/react';
import { useAuth } from '../../hooks/useAuth';
import SearchInput from '../ui/SearchInput';
import Button from '../ui/Button';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { to: '/subscription', label: '订阅' },
    { to: '/dashboard', label: '投递记录' },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-white/70 border-b border-gray-200/50">
      <div className="max-w-7xl mx-auto px-4 md:px-6 h-16 flex items-center gap-3 md:gap-6">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 shrink-0">
          <span className="text-xl font-display font-bold text-apple-blue tracking-tight">
            InternHub
          </span>
          <span className="hidden sm:inline text-xs font-medium text-apple-gray-text bg-apple-blue-light px-2 py-0.5 rounded-full">
            实习雷达
          </span>
        </Link>

        {/* Search — hidden on small mobile */}
        <div className="hidden sm:flex flex-1 max-w-xl">
          <SearchInput
            placeholder="搜索岗位、公司、技能..."
            onSearch={(kw) => {
              navigate(`/?keyword=${encodeURIComponent(kw)}`);
              setMobileMenuOpen(false);
            }}
          />
        </div>

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-1 text-sm font-medium">
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className="px-3 py-2 text-apple-gray-text hover:text-apple-black rounded-xl hover:bg-white/60 transition-colors duration-200"
            >
              {label}
            </Link>
          ))}

          {user ? (
            <button
              onClick={logout}
              className="ml-2 px-3 py-2 text-apple-gray-text hover:text-apple-red rounded-xl hover:bg-white/60 transition-colors duration-200 cursor-pointer"
            >
              退出
            </button>
          ) : (
            <Button size="sm" onClick={() => navigate('/login')}>
              登录
            </Button>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden ml-auto p-2 text-apple-gray-text hover:text-apple-black rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
        >
          {mobileMenuOpen ? <X size={20} /> : <List size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-100 bg-white/90 backdrop-blur-xl px-4 py-4 space-y-3">
          {/* Mobile search */}
          <div className="sm:hidden">
            <SearchInput
              placeholder="搜索岗位..."
              onSearch={(kw) => {
                navigate(`/?keyword=${encodeURIComponent(kw)}`);
                setMobileMenuOpen(false);
              }}
            />
          </div>
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm font-medium text-apple-gray-text hover:text-apple-black rounded-xl hover:bg-gray-100 transition-colors"
            >
              {label}
            </Link>
          ))}
          <div className="pt-2 border-t border-gray-100">
            {user ? (
              <button
                onClick={() => {
                  logout();
                  setMobileMenuOpen(false);
                }}
                className="block w-full text-left px-3 py-2 text-sm font-medium text-apple-red hover:bg-red-50 rounded-xl transition-colors cursor-pointer"
              >
                退出登录
              </button>
            ) : (
              <Button
                size="sm"
                onClick={() => {
                  navigate('/login');
                  setMobileMenuOpen(false);
                }}
                className="w-full"
              >
                登录
              </Button>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
