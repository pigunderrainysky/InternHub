export const JOB_TYPES = [
  { value: 'tech', label: '技术' },
  { value: 'product', label: '产品' },
  { value: 'operation', label: '运营' },
  { value: 'finance', label: '金融' },
  { value: 'design', label: '设计' },
  { value: 'other', label: '其他' },
] as const;

export const APPLICATION_STATUSES = [
  { value: 'applied', label: '已投递', icon: '📥' },
  { value: 'screening', label: '初筛中', icon: '👀' },
  { value: 'interview', label: '面试中', icon: '💬' },
  { value: 'offer', label: 'Offer', icon: '✅' },
  { value: 'rejected', label: '未通过', icon: '❌' },
  { value: 'closed', label: '已关闭', icon: '🔒' },
] as const;

export const SORT_OPTIONS = [
  { value: 'latest', label: '最新发布' },
  { value: 'deadline', label: '截止日期' },
  { value: 'salary', label: '薪资高低' },
] as const;

export const CITIES = [
  '北京', '上海', '广州', '深圳', '杭州',
  '南京', '成都', '武汉', '西安', '苏州',
  '重庆', '长沙', '天津', '合肥', '厦门',
] as const;

export const FREQUENCY_OPTIONS = [
  { value: 'daily', label: '每日推送' },
  { value: 'weekly', label: '每周推送' },
] as const;
