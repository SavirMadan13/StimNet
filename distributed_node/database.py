"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from .models import Base
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Create database engine
if settings.database_url.startswith("sqlite"):
    # SQLite specific configuration
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(
        settings.database_url,
        echo=settings.debug
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with default data"""
    create_tables()
    
    # Add any default data here
    db = SessionLocal()
    try:
        # Example: Create default node entry for this instance
        from .models import Node
        
        existing_node = db.query(Node).filter(Node.node_id == settings.node_id).first()
        if not existing_node:
            default_node = Node(
                node_id=settings.node_id,
                name=settings.node_name,
                institution=settings.institution_name,
                endpoint_url=f"http://{settings.host}:{settings.port}",
                is_active=True
            )
            db.add(default_node)
            db.commit()
            logger.info(f"Created default node entry for {settings.node_id}")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()