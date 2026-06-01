"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import settings
from .routers import auth, jobs, applications, subscriptions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    from .database import engine, Base

    Base.metadata.create_all(bind=engine)
    yield
    await engine.dispose()


app = FastAPI(
    title="InternHub API",
    description="实习信息聚合平台 — REST API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ──
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(subscriptions.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/admin/scrape")
async def trigger_scrape():
    """Trigger a full scrape run across all sources."""
    from .database import SessionLocal
    from .services.scraper_service import upsert_job
    from .scraper.shixiseng import ShixisengScraper
    from .scraper.niuke import NiukeScraper
    from .scraper.github_jobs import GitHubJobsScraper

    scrapers = [
        ShixisengScraper(max_pages=3),
        NiukeScraper(max_pages=3),
        GitHubJobsScraper(),
    ]

    results = {}
    total = 0

    for scraper in scrapers:
        name = scraper.source
        try:
            raw = await scraper.fetch()
            parsed = scraper.parse(raw)
        except Exception as e:
            results[name] = {"fetched": 0, "upserted": 0, "error": str(e)}
            continue

        db = SessionLocal()
        new_count = 0
        try:
            for job_data in parsed:
                if upsert_job(db, job_data):
                    new_count += 1
            db.commit()
        except Exception as e:
            db.rollback()
            results[name] = {"fetched": len(raw), "upserted": 0, "error": str(e)}
        finally:
            db.close()

        results[name] = {"fetched": len(raw), "upserted": new_count}
        total += new_count

    return {"status": "ok", "total_upserted": total, "sources": results}


@app.post("/api/admin/seed")
async def trigger_seed():
    """Insert realistic seed job data into the database."""
    from .database import SessionLocal
    from .services.scraper_service import upsert_job
    from datetime import datetime, timezone, timedelta
    import hashlib, random

    # Compact seed data
    seed_jobs = [
        # Tech
        ("前端开发实习生", "字节跳动", "北京", "tech", 400, 500),
        ("后端开发实习生", "字节跳动", "上海", "tech", 450, 550),
        ("算法实习生-抖音", "字节跳动", "北京", "tech", 500, 600),
        ("测试开发实习生", "字节跳动", "杭州", "tech", 350, 450),
        ("Java开发实习生", "阿里巴巴", "杭州", "tech", 400, 500),
        ("前端实习生-淘宝", "阿里巴巴", "杭州", "tech", 380, 480),
        ("数据研发实习生", "阿里巴巴", "北京", "tech", 400, 500),
        ("软件开发实习生", "腾讯", "深圳", "tech", 400, 500),
        ("微信小程序开发实习生", "腾讯", "广州", "tech", 380, 480),
        ("游戏客户端开发实习生", "腾讯", "上海", "tech", 400, 500),
        ("AI大模型实习生", "腾讯", "北京", "tech", 500, 600),
        ("后端开发实习生", "美团", "北京", "tech", 380, 480),
        ("数据开发实习生", "美团", "上海", "tech", 380, 480),
        ("前端开发实习生", "美团", "成都", "tech", 350, 450),
        ("嵌入式开发实习生", "华为", "深圳", "tech", 400, 500),
        ("AI框架开发实习生", "华为", "上海", "tech", 450, 550),
        ("云计算开发实习生", "华为", "成都", "tech", 400, 500),
        ("软件开发实习生", "百度", "北京", "tech", 380, 480),
        ("自动驾驶算法实习生", "百度", "北京", "tech", 450, 550),
        ("后端开发实习生", "小红书", "上海", "tech", 400, 500),
        ("推荐算法实习生", "小红书", "北京", "tech", 450, 550),
        ("iOS开发实习生", "小红书", "上海", "tech", 380, 480),
        ("后端开发实习生", "拼多多", "上海", "tech", 400, 500),
        ("软件开发实习生", "网易", "杭州", "tech", 380, 480),
        ("游戏引擎开发实习生", "网易游戏", "广州", "tech", 400, 500),
        ("前端开发实习生", "快手", "北京", "tech", 400, 500),
        ("音视频算法实习生", "快手", "北京", "tech", 450, 550),
        ("后端开发实习生", "京东", "北京", "tech", 350, 450),
        ("后端开发实习生", "滴滴", "北京", "tech", 380, 480),
        ("软件开发实习生", "小米", "北京", "tech", 380, 480),
        ("嵌入式实习生", "小米", "武汉", "tech", 350, 450),
        ("后端开发实习生", "哔哩哔哩", "上海", "tech", 400, 500),
        ("数据开发实习生", "哔哩哔哩", "上海", "tech", 380, 480),
        ("软件开发实习生", "蚂蚁集团", "杭州", "tech", 400, 500),
        ("安全实习生", "蚂蚁集团", "杭州", "tech", 400, 500),
        ("后端开发实习生", "携程", "上海", "tech", 350, 450),
        ("后端开发实习生", "得物", "上海", "tech", 400, 500),
        ("后端开发实习生", "SHEIN", "广州", "tech", 350, 450),
        ("游戏开发实习生", "米哈游", "上海", "tech", 400, 500),
        ("后端开发实习生", "Shopee", "深圳", "tech", 400, 500),
        ("软件开发实习生", "微软", "北京", "tech", 400, 550),
        ("软件工程实习生", "微软", "苏州", "tech", 400, 550),
        ("软件开发实习生", "NVIDIA", "上海", "tech", 450, 600),
        ("后端开发实习生", "大疆创新", "深圳", "tech", 400, 500),
        ("算法实习生", "大疆创新", "深圳", "tech", 450, 550),
        # Product
        ("产品经理实习生", "字节跳动", "北京", "product", 350, 450),
        ("产品经理实习生", "腾讯", "深圳", "product", 350, 450),
        ("AI产品实习生", "阿里巴巴", "杭州", "product", 380, 480),
        ("产品经理实习生", "美团", "上海", "product", 300, 400),
        ("产品运营实习生", "小红书", "上海", "product", 250, 350),
        ("商业化产品实习生", "快手", "北京", "product", 300, 400),
        ("策略产品实习生", "滴滴", "北京", "product", 350, 450),
        ("产品经理实习生", "百度", "北京", "product", 300, 400),
        # Operation
        ("用户运营实习生", "字节跳动", "北京", "operation", 200, 300),
        ("内容运营实习生", "小红书", "上海", "operation", 200, 300),
        ("新媒体运营实习生", "腾讯", "深圳", "operation", 200, 300),
        ("电商运营实习生", "拼多多", "上海", "operation", 250, 350),
        ("活动运营实习生", "美团", "北京", "operation", 200, 300),
        ("游戏运营实习生", "网易游戏", "广州", "operation", 250, 350),
        ("社区运营实习生", "哔哩哔哩", "上海", "operation", 200, 300),
        ("海外运营实习生", "SHEIN", "广州", "operation", 250, 350),
        # Finance
        ("量化研究实习生", "幻方量化", "上海", "finance", 500, 800),
        ("投资分析实习生", "红杉资本", "北京", "finance", 300, 400),
        ("行业研究实习生", "中信证券", "北京", "finance", 200, 300),
        ("投行实习生", "中金公司", "北京", "finance", 300, 400),
        ("风控实习生", "蚂蚁集团", "杭州", "finance", 300, 400),
        ("金融科技实习生", "招商银行", "深圳", "finance", 250, 350),
        # Design
        ("UI设计实习生", "字节跳动", "北京", "design", 300, 400),
        ("UX设计实习生", "腾讯", "深圳", "design", 300, 400),
        ("视觉设计实习生", "小红书", "上海", "design", 250, 350),
        ("游戏UI设计实习生", "米哈游", "上海", "design", 300, 400),
        ("交互设计实习生", "阿里巴巴", "杭州", "design", 300, 400),
    ]

    now = datetime.now(timezone.utc)
    count = 0

    for title, company, city, job_type, salary_min, salary_max in seed_jobs:
        days_ago = random.randint(0, 14)
        posted_at = now - timedelta(days=days_ago)
        dedup_raw = f"{company.lower()}|{title.lower().replace(' ', '')}|{city}"
        dedup_key = hashlib.sha256(dedup_raw.encode("utf-8")).hexdigest()
        source_hash = hashlib.sha256(f"seed:{dedup_key}".encode()).hexdigest()

        job_data = {
            "title": title,
            "company": company,
            "city": city,
            "job_type": job_type,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "description": f"【{company}】{title} | {city} | {salary_min}-{salary_max}元/天 | 表现优秀者有转正机会",
            "skills": None,
            "source": "seed",
            "source_url": f"https://seed.internhub/{dedup_key[:12]}",
            "source_hash": source_hash,
            "dedup_key": dedup_key,
            "is_active": True,
            "posted_at": posted_at,
            "deadline": now + timedelta(days=random.randint(30, 60)),
        }

        db = SessionLocal()
        try:
            if upsert_job(db, job_data):
                count += 1
        except Exception:
            pass
        finally:
            db.close()

    return {"status": "ok", "total_inserted": count}


@app.post("/api/admin/debug-scrape/{source}")
async def debug_scrape(source: str):
    """Debug: fetch raw data from one source and show samples."""
    from .scraper.shixiseng import ShixisengScraper
    from .scraper.niuke import NiukeScraper
    from .scraper.github_jobs import GitHubJobsScraper

    scraper_map = {
        "shixiseng": ShixisengScraper(max_pages=1),
        "niuke": NiukeScraper(max_pages=1),
        "github": GitHubJobsScraper(),
    }

    scraper = scraper_map.get(source)
    if not scraper:
        return {"error": f"Unknown source: {source}", "available": list(scraper_map.keys())}

    raw = await scraper.fetch()
    parsed = scraper.parse(raw)

    return {
        "source": source,
        "raw_count": len(raw),
        "parsed_count": len(parsed),
        "raw_sample": raw[:3],
        "parsed_sample": [
            {k: v for k, v in j.items() if k != "description"}
            for j in parsed[:3]
        ],
    }


# ── Static files (frontend build output) ──
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")


@app.get("/favicon.svg", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.svg")


@app.get("/icons.svg", include_in_schema=False)
async def icons():
    return FileResponse("static/icons.svg")


# ── SPA fallback — serve index.html for all non-API routes ──
@app.get("/{path:path}", include_in_schema=False)
async def spa_fallback(request: Request, path: str):
    """Serve index.html for SPA client-side routing."""
    return FileResponse("static/index.html")
