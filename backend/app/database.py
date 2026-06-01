"""SQLAlchemy database engine and session setup."""

import socket
from urllib.parse import urlparse, urlunparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings


def _resolve_ipv4_url(db_url: str) -> str:
    """Replace hostname with IPv4 address if hostname resolves to IPv6.

    Railway containers lack IPv6 routing; this forces psycopg2 to use IPv4.
    """
    parsed = urlparse(db_url)
    hostname = parsed.hostname
    port = parsed.port

    # Skip if already an IP address or local
    if not hostname:
        return db_url

    try:
        socket.inet_aton(hostname)
        # Already an IPv4 address, no change needed
        return db_url
    except OSError:
        pass

    try:
        socket.inet_pton(socket.AF_INET6, hostname)
        # Already an IPv6 address literal, keep as-is (though may fail on Railway)
        return db_url
    except OSError:
        pass

    # Resolve hostname to IPv4 only
    try:
        addrs = socket.getaddrinfo(hostname, port or 5432, socket.AF_INET, socket.SOCK_STREAM)
        ipv4 = addrs[0][4][0]
        # Replace hostname with IPv4 address in netloc
        if port:
            netloc = f"{parsed.username}:{parsed.password}@{ipv4}:{port}"
        else:
            netloc = f"{parsed.username}:{parsed.password}@{ipv4}"
        new_url = urlunparse(parsed._replace(netloc=netloc))
        print(f"[Database] Resolved {hostname} → {ipv4} (IPv4)")
        return new_url
    except (socket.gaierror, OSError) as e:
        print(f"[Database] Could not resolve IPv4 for {hostname}: {e}, using original URL")
        return db_url


engine = create_engine(
    _resolve_ipv4_url(settings.DATABASE_URL),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
