"""
Database optimization utilities for the AI Executive Team application.
"""

import logging
import time
import functools
from sqlalchemy import event, inspect
from sqlalchemy.orm import joinedload, contains_eager, load_only
from sqlalchemy.ext.declarative import declared_attr
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)

class QueryProfiler:
    """
    Utility for profiling database queries.
    """
    
    def __init__(self, db):
        """
        Initialize the query profiler.
        
        Args:
            db: SQLAlchemy database instance
        """
        self.db = db
        self.enabled = False
        self.queries = []
        self.slow_threshold_ms = 100  # Threshold for slow queries in milliseconds
    
    def enable(self):
        """
        Enable query profiling.
        """
        if not self.enabled:
            event.listen(self.db.engine, 'before_cursor_execute', self._before_cursor_execute)
            event.listen(self.db.engine, 'after_cursor_execute', self._after_cursor_execute)
            self.enabled = True
            self.queries = []
    
    def disable(self):
        """
        Disable query profiling.
        """
        if self.enabled:
            event.remove(self.db.engine, 'before_cursor_execute', self._before_cursor_execute)
            event.remove(self.db.engine, 'after_cursor_execute', self._after_cursor_execute)
            self.enabled = False
    
    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """
        Event handler called before cursor execution.
        """
        context._query_start_time = time.time()
    
    def _after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """
        Event handler called after cursor execution.
        """
        execution_time = (time.time() - context._query_start_time) * 1000  # Convert to milliseconds
        
        query_info = {
            'statement': statement,
            'parameters': parameters,
            'execution_time_ms': execution_time,
            'timestamp': time.time()
        }
        
        self.queries.append(query_info)
        
        # Log slow queries
        if execution_time > self.slow_threshold_ms:
            logger.warning(f"Slow query ({execution_time:.2f}ms): {statement}")
    
    def get_stats(self):
        """
        Get statistics about the profiled queries.
        
        Returns:
            Dictionary of query statistics
        """
        if not self.queries:
            return {
                'total_queries': 0,
                'total_time_ms': 0,
                'avg_time_ms': 0,
                'min_time_ms': 0,
                'max_time_ms': 0,
                'slow_queries': 0
            }
        
        total_time = sum(q['execution_time_ms'] for q in self.queries)
        avg_time = total_time / len(self.queries)
        min_time = min(q['execution_time_ms'] for q in self.queries)
        max_time = max(q['execution_time_ms'] for q in self.queries)
        slow_queries = sum(1 for q in self.queries if q['execution_time_ms'] > self.slow_threshold_ms)
        
        return {
            'total_queries': len(self.queries),
            'total_time_ms': total_time,
            'avg_time_ms': avg_time,
            'min_time_ms': min_time,
            'max_time_ms': max_time,
            'slow_queries': slow_queries
        }
    
    def get_slow_queries(self):
        """
        Get a list of slow queries.
        
        Returns:
            List of slow query information
        """
        return [q for q in self.queries if q['execution_time_ms'] > self.slow_threshold_ms]
    
    def clear(self):
        """
        Clear the query history.
        """
        self.queries = []

class OptimizedQuery:
    """
    Utility for building optimized database queries.
    """
    
    def __init__(self, model_class, session):
        """
        Initialize the optimized query builder.
        
        Args:
            model_class: SQLAlchemy model class
            session: SQLAlchemy session
        """
        self.model_class = model_class
        self.session = session
        self.query = session.query(model_class)
        self._eager_loads = []
        self._only_loads = []
    
    def with_eager_load(self, *relationships):
        """
        Add eager loading for relationships.
        
        Args:
            *relationships: Relationship attributes to eager load
            
        Returns:
            Self for chaining
        """
        for rel in relationships:
            self._eager_loads.append(rel)
            self.query = self.query.options(joinedload(rel))
        
        return self
    
    def with_only_columns(self, *columns):
        """
        Specify which columns to load.
        
        Args:
            *columns: Column attributes to load
            
        Returns:
            Self for chaining
        """
        self._only_loads.extend(columns)
        self.query = self.query.options(load_only(*columns))
        
        return self
    
    def filter_by(self, **kwargs):
        """
        Add filter criteria.
        
        Args:
            **kwargs: Filter criteria
            
        Returns:
            Self for chaining
        """
        self.query = self.query.filter_by(**kwargs)
        return self
    
    def filter(self, *criterion):
        """
        Add filter criteria.
        
        Args:
            *criterion: Filter criteria
            
        Returns:
            Self for chaining
        """
        self.query = self.query.filter(*criterion)
        return self
    
    def order_by(self, *criterion):
        """
        Add order by criteria.
        
        Args:
            *criterion: Order by criteria
            
        Returns:
            Self for chaining
        """
        self.query = self.query.order_by(*criterion)
        return self
    
    def limit(self, limit):
        """
        Add limit.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            Self for chaining
        """
        self.query = self.query.limit(limit)
        return self
    
    def offset(self, offset):
        """
        Add offset.
        
        Args:
            offset: Offset for results
            
        Returns:
            Self for chaining
        """
        self.query = self.query.offset(offset)
        return self
    
    def all(self):
        """
        Execute the query and return all results.
        
        Returns:
            List of results
        """
        return self.query.all()
    
    def first(self):
        """
        Execute the query and return the first result.
        
        Returns:
            First result or None
        """
        return self.query.first()
    
    def one(self):
        """
        Execute the query and return exactly one result.
        
        Returns:
            Single result
            
        Raises:
            NoResultFound: If no results are found
            MultipleResultsFound: If multiple results are found
        """
        return self.query.one()
    
    def one_or_none(self):
        """
        Execute the query and return one result or None.
        
        Returns:
            Single result or None
            
        Raises:
            MultipleResultsFound: If multiple results are found
        """
        return self.query.one_or_none()
    
    def count(self):
        """
        Execute the query and return the count.
        
        Returns:
            Count of results
        """
        return self.query.count()
    
    def paginate(self, page, per_page):
        """
        Get a page of results.
        
        Args:
            page: Page number (1-based)
            per_page: Number of items per page
            
        Returns:
            Dictionary with pagination information and results
        """
        total = self.count()
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get items for this page
        items = self.query.offset(offset).limit(per_page).all()
        
        # Calculate pagination info
        total_pages = (total + per_page - 1) // per_page  # Ceiling division
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev,
            'next_page': page + 1 if has_next else None,
            'prev_page': page - 1 if has_prev else None
        }

class ConnectionPoolMonitor:
    """
    Utility for monitoring the database connection pool.
    """
    
    def __init__(self, db):
        """
        Initialize the connection pool monitor.
        
        Args:
            db: SQLAlchemy database instance
        """
        self.db = db
    
    def get_stats(self):
        """
        Get statistics about the connection pool.
        
        Returns:
            Dictionary of connection pool statistics
        """
        engine = self.db.engine
        
        if not hasattr(engine, 'pool'):
            return {
                'pool_size': 0,
                'checkedin': 0,
                'checkedout': 0
            }
        
        pool = engine.pool
        
        return {
            'pool_size': pool.size(),
            'checkedin': pool.checkedin(),
            'checkedout': pool.checkedout()
        }

class IndexRecommender:
    """
    Utility for recommending database indexes based on query patterns.
    """
    
    def __init__(self, db):
        """
        Initialize the index recommender.
        
        Args:
            db: SQLAlchemy database instance
        """
        self.db = db
        self.query_patterns = {}
    
    def analyze_query(self, statement, parameters):
        """
        Analyze a SQL query to identify potential index opportunities.
        
        Args:
            statement: SQL statement
            parameters: Query parameters
            
        Returns:
            List of index recommendations
        """
        # This is a simplified implementation
        # In a real application, this would use more sophisticated analysis
        
        recommendations = []
        statement_lower = statement.lower()
        
        # Look for WHERE clauses
        if 'where' in statement_lower:
            # Extract table name
            from_match = re.search(r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)', statement_lower)
            if from_match:
                table_name = from_match.group(1)
                
                # Extract column names in WHERE clause
                where_clause = statement_lower.split('where')[1].split('order by')[0].split('group by')[0].split('limit')[0]
                column_matches = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*[=<>]', where_clause)
                
                for column in column_matches:
                    # Skip common indexed columns
                    if column == 'id' or column.endswith('_id'):
                        continue
                    
                    # Add to query patterns
                    pattern_key = f"{table_name}.{column}"
                    self.query_patterns[pattern_key] = self.query_patterns.get(pattern_key, 0) + 1
                    
                    # Recommend index if this pattern is seen frequently
                    if self.query_patterns[pattern_key] >= 5:
                        recommendations.append({
                            'table': table_name,
                            'column': column,
                            'frequency': self.query_patterns[pattern_key]
                        })
        
        return recommendations

def optimize_query(model_class, session):
    """
    Create an optimized query builder.
    
    Args:
        model_class: SQLAlchemy model class
        session: SQLAlchemy session
        
    Returns:
        OptimizedQuery instance
    """
    return OptimizedQuery(model_class, session)

def with_profiling(func):
    """
    Decorator to profile a function that executes database queries.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        from flask import current_app
        
        # Get database instance
        db = current_app.extensions['sqlalchemy'].db
        
        # Create profiler
        profiler = QueryProfiler(db)
        profiler.enable()
        
        try:
            # Call the function
            result = func(*args, **kwargs)
            
            # Log query stats
            stats = profiler.get_stats()
            logger.debug(f"Query stats for {func.__name__}: {stats}")
            
            return result
        finally:
            profiler.disable()
    
    return wrapped

class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.
    """
    
    @declared_attr
    def created_at(cls):
        from sqlalchemy import Column, DateTime
        from datetime import datetime
        return Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @declared_attr
    def updated_at(cls):
        from sqlalchemy import Column, DateTime
        from datetime import datetime
        from sqlalchemy import event
        
        # Add event listener to update timestamp on change
        @event.listens_for(cls, 'before_update', propagate=True)
        def timestamp_before_update(mapper, connection, target):
            target.updated_at = datetime.utcnow()
        
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

def setup_connection_pooling(app, db, pool_size=10, max_overflow=20, pool_recycle=3600):
    """
    Configure database connection pooling.
    
    Args:
        app: Flask application
        db: SQLAlchemy database instance
        pool_size: Base pool size
        max_overflow: Maximum number of connections to allow above pool_size
        pool_recycle: Number of seconds after which a connection is recycled
    """
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': pool_size,
        'max_overflow': max_overflow,
        'pool_recycle': pool_recycle,
        'pool_pre_ping': True
    }
    
    # Log connection pool configuration
    logger.info(f"Configured database connection pool: size={pool_size}, max_overflow={max_overflow}, recycle={pool_recycle}")

def optimize_database(app, db):
    """
    Apply database optimizations.
    
    Args:
        app: Flask application
        db: SQLAlchemy database instance
    """
    # Configure connection pooling
    setup_connection_pooling(app, db)
    
    # Create query profiler
    profiler = QueryProfiler(db)
    app.extensions['query_profiler'] = profiler
    
    # Create connection pool monitor
    pool_monitor = ConnectionPoolMonitor(db)
    app.extensions['pool_monitor'] = pool_monitor
    
    # Create index recommender
    index_recommender = IndexRecommender(db)
    app.extensions['index_recommender'] = index_recommender
    
    # Log optimization setup
    logger.info("Database optimizations applied")
