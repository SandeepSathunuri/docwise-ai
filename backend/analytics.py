import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
from collections import defaultdict, Counter
import sqlite3
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsManager:
    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Query analytics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        query TEXT NOT NULL,
                        response_time REAL,
                        model_used TEXT,
                        confidence REAL,
                        documents_used INTEGER,
                        session_id TEXT,
                        success BOOLEAN
                    )
                ''')
                
                # Document analytics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS document_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        document_name TEXT,
                        action TEXT,
                        user_session TEXT
                    )
                ''')
                
                # System performance table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL,
                        additional_data TEXT
                    )
                ''')
                
                # User sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        start_time TEXT NOT NULL,
                        last_activity TEXT NOT NULL,
                        query_count INTEGER DEFAULT 0,
                        total_response_time REAL DEFAULT 0
                    )
                ''')
                
                conn.commit()
                logger.info("Analytics database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing analytics database: {str(e)}")
    
    def log_query(self, query: str, response_time: float, model_used: str, 
                  confidence: float, documents_used: int, session_id: str, 
                  success: bool = True):
        """Log a query and its performance metrics"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO queries 
                        (timestamp, query, response_time, model_used, confidence, 
                         documents_used, session_id, success)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        datetime.now().isoformat(),
                        query,
                        response_time,
                        model_used,
                        confidence,
                        documents_used,
                        session_id,
                        success
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error logging query: {str(e)}")
    
    def log_document_action(self, document_id: str, document_name: str, 
                           action: str, session_id: str):
        """Log document-related actions"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO document_usage 
                        (timestamp, document_id, document_name, action, user_session)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        datetime.now().isoformat(),
                        document_id,
                        document_name,
                        action,
                        session_id
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error logging document action: {str(e)}")
    
    def log_system_metric(self, metric_name: str, metric_value: float, 
                         additional_data: Dict = None):
        """Log system performance metrics"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO system_performance 
                        (timestamp, metric_name, metric_value, additional_data)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        datetime.now().isoformat(),
                        metric_name,
                        metric_value,
                        json.dumps(additional_data) if additional_data else None
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error logging system metric: {str(e)}")
    
    def update_session(self, session_id: str, query_count_increment: int = 1, 
                      response_time: float = 0):
        """Update or create user session"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Check if session exists
                    cursor.execute('SELECT id FROM user_sessions WHERE session_id = ?', (session_id,))
                    exists = cursor.fetchone()
                    
                    if exists:
                        # Update existing session
                        cursor.execute('''
                            UPDATE user_sessions 
                            SET last_activity = ?, 
                                query_count = query_count + ?,
                                total_response_time = total_response_time + ?
                            WHERE session_id = ?
                        ''', (
                            datetime.now().isoformat(),
                            query_count_increment,
                            response_time,
                            session_id
                        ))
                    else:
                        # Create new session
                        cursor.execute('''
                            INSERT INTO user_sessions 
                            (session_id, start_time, last_activity, query_count, total_response_time)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            session_id,
                            datetime.now().isoformat(),
                            datetime.now().isoformat(),
                            query_count_increment,
                            response_time
                        ))
                    
                    conn.commit()
        except Exception as e:
            logger.error(f"Error updating session: {str(e)}")
    
    def get_query_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get query analytics for the specified number of days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total queries
                cursor.execute('''
                    SELECT COUNT(*) FROM queries 
                    WHERE timestamp > ? AND success = 1
                ''', (cutoff_date,))
                total_queries = cursor.fetchone()[0]
                
                # Average response time
                cursor.execute('''
                    SELECT AVG(response_time) FROM queries 
                    WHERE timestamp > ? AND success = 1
                ''', (cutoff_date,))
                avg_response_time = cursor.fetchone()[0] or 0
                
                # Average confidence
                cursor.execute('''
                    SELECT AVG(confidence) FROM queries 
                    WHERE timestamp > ? AND success = 1
                ''', (cutoff_date,))
                avg_confidence = cursor.fetchone()[0] or 0
                
                # Model usage
                cursor.execute('''
                    SELECT model_used, COUNT(*) FROM queries 
                    WHERE timestamp > ? AND success = 1
                    GROUP BY model_used
                ''', (cutoff_date,))
                model_usage = dict(cursor.fetchall())
                
                # Queries per day
                cursor.execute('''
                    SELECT DATE(timestamp) as date, COUNT(*) FROM queries 
                    WHERE timestamp > ? AND success = 1
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                ''', (cutoff_date,))
                daily_queries = dict(cursor.fetchall())
                
                # Most common query patterns
                cursor.execute('''
                    SELECT query FROM queries 
                    WHERE timestamp > ? AND success = 1
                ''', (cutoff_date,))
                queries = [row[0] for row in cursor.fetchall()]
                
                # Analyze query patterns
                query_words = []
                for query in queries:
                    query_words.extend(query.lower().split())
                
                common_words = Counter(query_words).most_common(10)
                
                return {
                    "total_queries": total_queries,
                    "avg_response_time": round(avg_response_time, 3),
                    "avg_confidence": round(avg_confidence, 3),
                    "model_usage": model_usage,
                    "daily_queries": daily_queries,
                    "common_query_words": common_words,
                    "period_days": days
                }
        except Exception as e:
            logger.error(f"Error getting query analytics: {str(e)}")
            return {}
    
    def get_document_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get document usage analytics"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Most accessed documents
                cursor.execute('''
                    SELECT document_name, COUNT(*) as access_count FROM document_usage 
                    WHERE timestamp > ?
                    GROUP BY document_name
                    ORDER BY access_count DESC
                    LIMIT 10
                ''', (cutoff_date,))
                popular_documents = dict(cursor.fetchall())
                
                # Document actions breakdown
                cursor.execute('''
                    SELECT action, COUNT(*) FROM document_usage 
                    WHERE timestamp > ?
                    GROUP BY action
                ''', (cutoff_date,))
                action_breakdown = dict(cursor.fetchall())
                
                # Daily document activity
                cursor.execute('''
                    SELECT DATE(timestamp) as date, COUNT(*) FROM document_usage 
                    WHERE timestamp > ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                ''', (cutoff_date,))
                daily_activity = dict(cursor.fetchall())
                
                return {
                    "popular_documents": popular_documents,
                    "action_breakdown": action_breakdown,
                    "daily_activity": daily_activity,
                    "period_days": days
                }
        except Exception as e:
            logger.error(f"Error getting document analytics: {str(e)}")
            return {}
    
    def get_session_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get user session analytics"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Active sessions
                cursor.execute('''
                    SELECT COUNT(*) FROM user_sessions 
                    WHERE last_activity > ?
                ''', (cutoff_date,))
                active_sessions = cursor.fetchone()[0]
                
                # Average queries per session
                cursor.execute('''
                    SELECT AVG(query_count) FROM user_sessions 
                    WHERE last_activity > ?
                ''', (cutoff_date,))
                avg_queries_per_session = cursor.fetchone()[0] or 0
                
                # Average session response time
                cursor.execute('''
                    SELECT AVG(total_response_time / query_count) FROM user_sessions 
                    WHERE last_activity > ? AND query_count > 0
                ''', (cutoff_date,))
                avg_session_response_time = cursor.fetchone()[0] or 0
                
                # Session duration distribution
                cursor.execute('''
                    SELECT 
                        session_id,
                        start_time,
                        last_activity,
                        query_count
                    FROM user_sessions 
                    WHERE last_activity > ?
                ''', (cutoff_date,))
                
                sessions = cursor.fetchall()
                session_durations = []
                
                for session_id, start_time, last_activity, query_count in sessions:
                    try:
                        start = datetime.fromisoformat(start_time)
                        end = datetime.fromisoformat(last_activity)
                        duration = (end - start).total_seconds() / 60  # minutes
                        session_durations.append(duration)
                    except:
                        continue
                
                avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0
                
                return {
                    "active_sessions": active_sessions,
                    "avg_queries_per_session": round(avg_queries_per_session, 2),
                    "avg_session_response_time": round(avg_session_response_time, 3),
                    "avg_session_duration_minutes": round(avg_session_duration, 2),
                    "period_days": days
                }
        except Exception as e:
            logger.error(f"Error getting session analytics: {str(e)}")
            return {}
    
    def get_system_performance(self, days: int = 7) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all performance metrics
                cursor.execute('''
                    SELECT metric_name, AVG(metric_value), COUNT(*) FROM system_performance 
                    WHERE timestamp > ?
                    GROUP BY metric_name
                ''', (cutoff_date,))
                
                metrics = {}
                for metric_name, avg_value, count in cursor.fetchall():
                    metrics[metric_name] = {
                        "average": round(avg_value, 3),
                        "samples": count
                    }
                
                return {
                    "metrics": metrics,
                    "period_days": days
                }
        except Exception as e:
            logger.error(f"Error getting system performance: {str(e)}")
            return {}
    
    def get_comprehensive_report(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive analytics report"""
        return {
            "query_analytics": self.get_query_analytics(days),
            "document_analytics": self.get_document_analytics(days),
            "session_analytics": self.get_session_analytics(days),
            "system_performance": self.get_system_performance(days),
            "generated_at": datetime.now().isoformat(),
            "report_period_days": days
        }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old analytics data"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Clean up old queries
                    cursor.execute('DELETE FROM queries WHERE timestamp < ?', (cutoff_date,))
                    queries_deleted = cursor.rowcount
                    
                    # Clean up old document usage
                    cursor.execute('DELETE FROM document_usage WHERE timestamp < ?', (cutoff_date,))
                    doc_usage_deleted = cursor.rowcount
                    
                    # Clean up old system performance
                    cursor.execute('DELETE FROM system_performance WHERE timestamp < ?', (cutoff_date,))
                    perf_deleted = cursor.rowcount
                    
                    # Clean up old sessions
                    cursor.execute('DELETE FROM user_sessions WHERE last_activity < ?', (cutoff_date,))
                    sessions_deleted = cursor.rowcount
                    
                    conn.commit()
                    
                    logger.info(f"Cleaned up old data: {queries_deleted} queries, "
                              f"{doc_usage_deleted} document actions, "
                              f"{perf_deleted} performance metrics, "
                              f"{sessions_deleted} sessions")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")

# Global analytics instance
analytics = AnalyticsManager()