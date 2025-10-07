"""Database connection management with pooling for PostgreSQL"""
from typing import Optional
import psycopg2
from psycopg2 import pool, extras
from contextlib import contextmanager
from config.settings import settings
from services.logger import get_logger
from services.exceptions import DatabaseError

logger = get_logger(__name__)

# Global connection pool
_connection_pool: Optional[pool.SimpleConnectionPool] = None


def initialize_pool():
    """Initialize the PostgreSQL connection pool"""
    global _connection_pool
    
    if _connection_pool is not None:
        return
    
    try:
        # Build connection string
        connection_string = (
            f"host={settings.POSTGRES_HOST} "
            f"port={settings.POSTGRES_PORT} "
            f"dbname={settings.POSTGRES_DATABASE} "
            f"user={settings.POSTGRES_USER} "
            f"password={settings.POSTGRES_PASSWORD} "
            f"client_encoding=utf8"
        )
        
        _connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=settings.POSTGRES_POOL_SIZE,
            dsn=connection_string
        )
        
        logger.info(
            "database_pool_initialized",
            pool_size=settings.POSTGRES_POOL_SIZE,
            database=settings.POSTGRES_DATABASE
        )
        
    except psycopg2.Error as e:
        logger.error("database_pool_initialization_failed", error=str(e))
        raise DatabaseError(f"Failed to initialize database pool: {str(e)}")


def get_db_connection():
    """
    Get a connection from the pool
    
    Returns:
        PostgreSQL connection from pool
    """
    global _connection_pool
    
    if _connection_pool is None:
        initialize_pool()
    
    try:
        connection = _connection_pool.getconn()
        return connection
    except psycopg2.Error as e:
        logger.error("failed_to_get_connection", error=str(e))
        raise DatabaseError(f"Failed to get database connection: {str(e)}")


def close_db_connection(connection):
    """
    Return connection to pool
    
    Args:
        connection: PostgreSQL connection to return
    """
    global _connection_pool
    
    if connection and _connection_pool:
        _connection_pool.putconn(connection)


@contextmanager
def get_db_cursor(dictionary=True):
    """
    Context manager for database operations
    
    Args:
        dictionary: Return results as dictionaries (RealDictCursor)
        
    Yields:
        Database cursor
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        
        # Use RealDictCursor for dictionary results
        if dictionary:
            cursor = connection.cursor(cursor_factory=extras.RealDictCursor)
        else:
            cursor = connection.cursor()
            
        yield cursor
        connection.commit()
        
    except psycopg2.Error as e:
        if connection:
            connection.rollback()
        logger.error("database_operation_failed", error=str(e))
        raise DatabaseError(f"Database operation failed: {str(e)}")
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            close_db_connection(connection)


def close_pool():
    """Close all connections in the pool"""
    global _connection_pool
    
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
        logger.info("database_pool_closed")