import { Link, useRouteError, isRouteErrorResponse } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Warning } from '@phosphor-icons/react';
import Button from '../components/ui/Button';

export default function ErrorPage() {
  const error = useRouteError();
  const status = isRouteErrorResponse(error) ? error.status : 500;
  const message =
    isRouteErrorResponse(error)
      ? error.statusText
      : error instanceof Error
        ? error.message
        : '未知错误';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-24 px-4 text-center"
    >
      <Warning size={56} weight="duotone" className="text-apple-orange mb-6" />
      <h1 className="text-5xl font-display font-bold text-apple-black mb-3">{status}</h1>
      <p className="text-base text-apple-gray-text mb-2">抱歉，出了点问题</p>
      <p className="text-sm text-apple-gray-text mb-8 max-w-sm">{message}</p>
      <div className="flex gap-3">
        <Link to="/">
          <Button variant="secondary">返回首页</Button>
        </Link>
        <Button onClick={() => window.location.reload()}>刷新页面</Button>
      </div>
    </motion.div>
  );
}
