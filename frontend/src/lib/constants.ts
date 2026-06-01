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
  // 一线城市
  '北京', '上海', '广州', '深圳',
  // 新一线
  '杭州', '成都', '武汉', '南京', '西安', '重庆', '长沙', '苏州', '天津', '合肥',
  '郑州', '青岛', '东莞', '宁波', '佛山', '沈阳', '昆明', '大连', '无锡',
  // 省会及重点城市
  '厦门', '福州', '济南', '哈尔滨', '长春', '石家庄', '太原', '南昌',
  '南宁', '贵阳', '兰州', '海口', '银川', '西宁', '拉萨', '乌鲁木齐',
  // 其他实习热门城市
  '珠海', '惠州', '中山', '嘉兴', '绍兴', '常州', '南通', '温州',
  '烟台', '潍坊', '泉州', '徐州', '盐城', '泰州', '镇江', '湖州',
  '芜湖', '洛阳', '宜昌', '襄阳', '绵阳', '宜宾', '柳州', '桂林',
  '三亚', '呼和浩特', '包头',
] as const;

export const FREQUENCY_OPTIONS = [
  { value: 'daily', label: '每日推送' },
  { value: 'weekly', label: '每周推送' },
] as const;
