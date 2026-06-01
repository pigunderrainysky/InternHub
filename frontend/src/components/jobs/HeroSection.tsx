import { motion } from 'framer-motion';
import SearchInput from '../ui/SearchInput';

interface HeroSectionProps {
  defaultKeyword?: string;
  onSearch: (keyword: string) => void;
}

export default function HeroSection({ defaultKeyword, onSearch }: HeroSectionProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="text-center py-12 md:py-16"
    >
      <h1 className="text-3xl md:text-4xl font-display font-bold text-apple-black tracking-tight mb-3">
        发现最适合你的实习机会
      </h1>
      <p className="text-base md:text-lg text-apple-gray-text mb-8 max-w-lg mx-auto leading-relaxed">
        聚合多平台实习信息，一站搜索、筛选、投递追踪
      </p>
      <div className="max-w-xl mx-auto">
        <SearchInput
          defaultValue={defaultKeyword}
          placeholder="搜索岗位、公司、技能..."
          onSearch={onSearch}
          className="shadow-sm"
        />
      </div>
    </motion.section>
  );
}
