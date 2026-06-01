#!/usr/bin/env python3
"""Seed realistic internship listings into the database."""

import asyncio
import random
from datetime import datetime, timezone, timedelta

from app.database import SessionLocal
from app.services.scraper_service import upsert_job

# ── Realistic internship listings from well-known companies ──
# Format: (title, company, city, job_type, salary_min, salary_max, description_keywords)
SEED_JOBS = [
    # ── Tech 技术类 ──
    ("前端开发实习生", "字节跳动", "北京", "tech", 400, 500, "React TypeScript Web前端"),
    ("后端开发实习生", "字节跳动", "上海", "tech", 450, 550, "Go Python 微服务 分布式"),
    ("算法实习生-抖音", "字节跳动", "北京", "tech", 500, 600, "推荐系统 深度学习 NLP CV"),
    ("测试开发实习生", "字节跳动", "杭州", "tech", 350, 450, "自动化测试 Python 质量保障"),
    ("算法工程师实习生", "阿里巴巴", "杭州", "tech", 450, 550, "机器学习 搜索推荐 大模型"),
    ("Java开发实习生", "阿里巴巴", "杭州", "tech", 400, 500, "Java Spring 分布式 中间件"),
    ("前端实习生-淘宝", "阿里巴巴", "杭州", "tech", 380, 480, "React Vue JavaScript CSS"),
    ("数据研发实习生", "阿里巴巴", "北京", "tech", 400, 500, "Flink Spark 数据仓库 ETL"),
    ("软件开发实习生", "腾讯", "深圳", "tech", 400, 500, "C++ Go 后台开发 Linux"),
    ("微信小程序开发实习生", "腾讯", "广州", "tech", 380, 480, "小程序 前端 JavaScript WXML"),
    ("游戏客户端开发实习生", "腾讯", "上海", "tech", 400, 500, "Unity C# 游戏引擎 Unreal"),
    ("AI算法实习生", "腾讯", "北京", "tech", 500, 600, "大语言模型 AIGC 多模态"),
    ("后端开发实习生", "美团", "北京", "tech", 380, 480, "Java Spring 高并发 分布式"),
    ("数据开发实习生", "美团", "上海", "tech", 380, 480, "Hadoop Spark 数据仓库 SQL"),
    ("前端开发实习生", "美团", "成都", "tech", 350, 450, "React Vue TypeScript Webpack"),
    ("嵌入式开发实习生", "华为", "深圳", "tech", 400, 500, "C/C++ 嵌入式 Linux RTOS"),
    ("AI框架开发实习生", "华为", "上海", "tech", 450, 550, "PyTorch TensorFlow 分布式训练"),
    ("云计算开发实习生", "华为", "成都", "tech", 400, 500, "Kubernetes Docker 云原生 Go"),
    ("软件开发实习生", "百度", "北京", "tech", 380, 480, "C++ Python 搜索 广告系统"),
    ("自动驾驶算法实习生", "百度", "北京", "tech", 450, 550, "感知 规划控制 SLAM 深度学习"),
    ("后端开发实习生", "小红书", "上海", "tech", 400, 500, "Go Java 微服务 Redis"),
    ("推荐算法实习生", "小红书", "北京", "tech", 450, 550, "推荐系统 机器学习 用户画像"),
    ("iOS开发实习生", "小红书", "上海", "tech", 380, 480, "Swift UIKit SwiftUI iOS"),
    ("后端开发实习生", "拼多多", "上海", "tech", 400, 500, "Java Python 高并发 电商"),
    ("前端开发实习生", "拼多多", "上海", "tech", 380, 480, "React Vue 小程序 H5"),
    ("软件开发实习生", "网易", "杭州", "tech", 380, 480, "Java Python 游戏 后台开发"),
    ("游戏引擎开发实习生", "网易游戏", "广州", "tech", 400, 500, "Unreal Unity C++ 图形学"),
    ("前端开发实习生", "快手", "北京", "tech", 400, 500, "React Vue TypeScript 直播"),
    ("音视频算法实习生", "快手", "北京", "tech", 450, 550, "视频编解码 音频处理 AI"),
    ("后端开发实习生", "京东", "北京", "tech", 350, 450, "Java Spring 电商 物流系统"),
    ("测试开发实习生", "京东", "北京", "tech", 300, 400, "自动化测试 Selenium Java"),
    ("后端开发实习生", "滴滴", "北京", "tech", 380, 480, "Go Java 出行 高并发"),
    ("算法实习生", "滴滴", "北京", "tech", 450, 550, "轨迹预测 定价策略 运筹优化"),
    ("软件开发实习生", "小米", "北京", "tech", 380, 480, "Java C++ IoT Android"),
    ("嵌入式实习生", "小米", "武汉", "tech", 350, 450, "C 嵌入式 Linux 智能硬件"),
    ("数据开发实习生", "哔哩哔哩", "上海", "tech", 380, 480, "Hadoop Spark 数据仓库"),
    ("后端开发实习生", "哔哩哔哩", "上海", "tech", 400, 500, "Go Python 弹幕系统 高并发"),
    ("软件开发实习生", "蚂蚁集团", "杭州", "tech", 400, 500, "Java Go 金融科技 区块链"),
    ("安全实习生", "蚂蚁集团", "杭州", "tech", 400, 500, "安全攻防 渗透测试 密码学"),
    ("后端开发实习生", "携程", "上海", "tech", 350, 450, "Java Python 旅行 电商"),
    ("全栈开发实习生", "知乎", "北京", "tech", 350, 450, "React Node.js TypeScript"),
    ("后端开发实习生", "得物", "上海", "tech", 400, 500, "Go Java 电商 潮牌"),
    ("后端开发实习生", "SHEIN", "广州", "tech", 350, 450, "Java Go 跨境电商 供应链"),
    ("数据开发实习生", "米哈游", "上海", "tech", 400, 500, "大数据 Spark 数据湖"),
    ("游戏开发实习生", "米哈游", "上海", "tech", 400, 500, "Unity C# 动作游戏 渲染"),
    ("后端开发实习生", "Shopee", "深圳", "tech", 400, 500, "Go Python 电商 东南亚"),
    ("前端开发实习生", "Shopee", "深圳", "tech", 380, 480, "React TypeScript 电商"),
    ("软件开发实习生", "微软", "北京", "tech", 400, 550, "C# .NET Azure 云计算"),
    ("软件工程实习生", "微软", "苏州", "tech", 400, 550, "C++ Java Office365 Azure"),
    ("软件开发实习生", "Intel", "上海", "tech", 350, 450, "C/C++ 芯片设计 Linux内核"),
    ("软件开发实习生", "NVIDIA", "上海", "tech", 450, 600, "CUDA C++ GPU 深度学习"),
    ("软件工程实习生", "SAP", "上海", "tech", 350, 450, "Java ABAP 企业软件 Cloud"),
    ("后端开发实习生", "大疆创新", "深圳", "tech", 400, 500, "C++ Python 机器人 嵌入式"),
    ("算法实习生", "大疆创新", "深圳", "tech", 450, 550, "计算机视觉 SLAM 路径规划"),

    # ── Product 产品类 ──
    ("产品经理实习生", "字节跳动", "北京", "product", 350, 450, "需求分析 用户研究 PRD"),
    ("产品经理实习生", "腾讯", "深圳", "product", 350, 450, "社交产品 数据分析 产品设计"),
    ("AI产品实习生", "阿里巴巴", "杭州", "product", 380, 480, "AI产品 大模型应用 产品设计"),
    ("产品经理实习生", "美团", "上海", "product", 300, 400, "O2O 用户增长 数据分析"),
    ("产品运营实习生", "小红书", "上海", "product", 250, 350, "内容产品 社区运营 用户研究"),
    ("商业化产品实习生", "快手", "北京", "product", 300, 400, "广告产品 商业化 数据分析"),
    ("产品经理实习生", "百度", "北京", "product", 300, 400, "搜索产品 AI产品 用户研究"),
    ("策略产品实习生", "滴滴", "北京", "product", 350, 450, "策略产品 出行 供需匹配"),
    ("产品实习生", "知乎", "北京", "product", 250, 350, "内容社区 用户增长 数据分析"),
    ("产品经理实习生", "京东", "北京", "product", 250, 350, "电商产品 供应链 用户研究"),
    ("产品实习生", "网易", "杭州", "product", 250, 350, "教育产品 游戏产品 用户需求"),

    # ── Operation 运营类 ──
    ("用户运营实习生", "字节跳动", "北京", "operation", 200, 300, "用户增长 社群运营 数据分析"),
    ("内容运营实习生", "小红书", "上海", "operation", 200, 300, "内容策划 社区运营 文案"),
    ("新媒体运营实习生", "腾讯", "深圳", "operation", 200, 300, "公众号 短视频 内容营销"),
    ("电商运营实习生", "拼多多", "上海", "operation", 250, 350, "电商运营 商家管理 GMV"),
    ("活动运营实习生", "美团", "北京", "operation", 200, 300, "活动策划 用户增长 营销"),
    ("游戏运营实习生", "网易游戏", "广州", "operation", 250, 350, "游戏运营 玩家社区 数据分析"),
    ("社区运营实习生", "哔哩哔哩", "上海", "operation", 200, 300, "社区运营 弹幕文化 UP主"),
    ("海外运营实习生", "SHEIN", "广州", "operation", 250, 350, "跨境电商 英语 社交媒体"),
    ("用户运营实习生", "快手", "北京", "operation", 200, 300, "用户增长 直播运营 数据分析"),
    ("社交媒体运营实习生", "得物", "上海", "operation", 200, 300, "潮流社区 社交媒体 内容策划"),

    # ── Finance 金融类 ──
    ("量化研究实习生", "幻方量化", "上海", "finance", 500, 800, "量化策略 Python 机器学习 因子分析"),
    ("投资分析实习生", "红杉资本", "北京", "finance", 300, 400, "行业研究 尽职调查 投资分析"),
    ("行业研究实习生", "中信证券", "北京", "finance", 200, 300, "行业分析 财务建模 报告撰写"),
    ("投行实习生", "中金公司", "北京", "finance", 300, 400, "IPO 并购 估值建模 财务分析"),
    ("风控实习生", "蚂蚁集团", "杭州", "finance", 300, 400, "风控策略 数据分析 机器学习"),
    ("量化开发实习生", "九坤投资", "北京", "finance", 500, 800, "C++ Python 低延迟 交易系统"),
    ("金融科技实习生", "招商银行", "深圳", "finance", 250, 350, "Fintech 区块链 移动支付"),
    ("咨询实习生", "麦肯锡", "上海", "finance", 350, 450, "管理咨询 战略分析 行业研究"),
    ("审计实习生", "普华永道", "上海", "finance", 200, 300, "审计 财务分析 风险评估"),
    ("研究实习生", "中金研究部", "上海", "finance", 250, 350, "行业研究 宏观分析 报告撰写"),

    # ── Design 设计类 ──
    ("UI设计实习生", "字节跳动", "北京", "design", 300, 400, "UI设计 Figma Sketch 设计系统"),
    ("UX设计师实习生", "腾讯", "深圳", "design", 300, 400, "用户研究 交互设计 可用性测试"),
    ("视觉设计实习生", "小红书", "上海", "design", 250, 350, "品牌设计 插画 视觉传达"),
    ("游戏UI设计实习生", "米哈游", "上海", "design", 300, 400, "游戏UI 原画 游戏交互"),
    ("交互设计实习生", "阿里巴巴", "杭州", "design", 300, 400, "交互设计 用户研究 移动端"),
    ("平面设计实习生", "网易", "杭州", "design", 200, 300, "品牌设计 海报 印刷"),
    ("UI设计实习生", "哔哩哔哩", "上海", "design", 250, 350, "移动端设计 二次元 UI设计"),
    ("体验设计实习生", "美团", "北京", "design", 250, 350, "交互设计 服务设计 用户研究"),
]


async def seed():
    now = datetime.now(timezone.utc)
    count = 0

    # Spread post dates across last 14 days
    for i, (title, company, city, job_type, salary_min, salary_max, desc) in enumerate(SEED_JOBS):
        days_ago = random.randint(0, 14)
        posted_at = now - timedelta(days=days_ago)

        # Generate realistic source URL
        source_domains = {
            "字节跳动": "jobs.bytedance.com",
            "阿里巴巴": "talent.alibaba.com",
            "腾讯": "join.qq.com",
            "美团": "campus.meituan.com",
            "华为": "career.huawei.com",
            "百度": "talent.baidu.com",
            "小红书": "job.xiaohongshu.com",
            "拼多多": "careers.pinduoduo.com",
            "网易": "campus.163.com",
            "网易游戏": "game.campus.163.com",
            "快手": "zhaopin.kuaishou.cn",
            "京东": "zhaopin.jd.com",
            "滴滴": "talent.didiglobal.com",
            "小米": "xiaomi.jobs.feishu.cn",
            "哔哩哔哩": "jobs.bilibili.com",
            "蚂蚁集团": "talent.antgroup.com",
            "携程": "job.ctrip.com",
            "知乎": "zhaopin.zhihu.com",
            "得物": "app.mokahr.com/apply/poizon",
            "SHEIN": "app.mokahr.com/apply/shein",
            "米哈游": "campus.mihoyo.com",
            "Shopee": "careers.shopee.cn",
            "微软": "careers.microsoft.com",
            "Intel": "jobs.intel.com",
            "NVIDIA": "nvidia.wd5.myworkdayjobs.com",
            "SAP": "jobs.sap.com",
            "大疆创新": "we.dji.com",
            "幻方量化": "www.high-flyer.cn",
            "红杉资本": "app.mokahr.com/apply/sequoiacap",
            "中信证券": "careers.citics.com",
            "中金公司": "cicc.zhiye.com",
            "九坤投资": "career.ubiquant.com",
            "招商银行": "career.cmbchina.com",
            "麦肯锡": "www.mckinsey.com/careers",
            "普华永道": "pwc.wd3.myworkdayjobs.com",
            "中金研究部": "cicc.zhiye.com",
        }

        domain = source_domains.get(company, "example.com")
        slug = f"{company}-{title}-{i:04d}".replace("/", "-").replace(" ", "-")
        source_url = f"https://{domain}/position/{slug}"

        # Dedup key (sha256 of company|title|city)
        import hashlib

        dedup_raw = f"{company.lower()}|{title.lower().replace(' ', '')}|{city}"
        dedup_key = hashlib.sha256(dedup_raw.encode("utf-8")).hexdigest()
        source_hash = hashlib.sha256(source_url.encode("utf-8")).hexdigest()

        # Skills extraction from description
        skills = None
        skill_keywords = desc.split()
        if skill_keywords:
            skills = skill_keywords

        job_data = {
            "title": title,
            "company": company,
            "city": city,
            "job_type": job_type,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "description": (
                f"【岗位】{title}\n"
                f"【公司】{company}\n"
                f"【城市】{city}\n"
                f"【薪资】{salary_min}-{salary_max}元/天\n"
                f"【关键词】{desc}\n\n"
                f"表现优秀者有转正机会，提供免费三餐/下午茶。"
            ),
            "skills": skills,
            "source": "seed",
            "source_url": source_url,
            "source_hash": source_hash,
            "dedup_key": dedup_key,
            "is_active": True,
            "posted_at": posted_at,
            "deadline": now + timedelta(days=random.randint(30, 60)),
        }

        db = SessionLocal()
        try:
            result = upsert_job(db, job_data)
            if result:
                count += 1
                print(f"  ✓ [{count:03d}/{len(SEED_JOBS)}] {company} — {title} ({city})")
        except Exception as e:
            print(f"  ✗ Failed: {company} - {title}: {e}")
        finally:
            db.close()

    print(f"\n{'='*50}")
    print(f"  Done! Inserted {count} jobs into database.")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(seed())
