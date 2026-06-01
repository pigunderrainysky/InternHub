import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { SmileySad } from '@phosphor-icons/react';
import Button from '../components/ui/Button';

export default function NotFoundPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-24 px-4 text-center"
    >
      <SmileySad size={56} weight="duotone" className="text-apple-gray-text mb-6" />
      <h1 className="text-5xl font-display font-bold text-apple-black mb-3">404</h1>
      <p className="text-base text-apple-gray-text mb-8 max-w-sm">
        你访问的页面不存在，可能已被删除或地址输入有误
      </p>
      <Link to="/">
        <Button>返回首页</Button>
      </Link>
    </motion.div>
  );
}
