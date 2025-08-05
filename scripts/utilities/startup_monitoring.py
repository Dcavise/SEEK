#!/usr/bin/env python3
"""
Simple monitoring for startup property search platform
Focus on essential metrics that matter for user experience
"""

import json
from supabase import create_client, Client
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SimpleMonitoring:
    """Lightweight monitoring focused on what matters for MVP"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    def check_system_health(self) -> dict:
        """Basic health checks that matter for user experience"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        try:
            # 1. Database connectivity
            result = self.supabase.table('properties').select('count').execute()
            health_status['checks']['database_connection'] = {
                'status': 'ok',
                'response_time_ms': 'measured_here'  # Implement timing if needed
            }
            
            # 2. Data availability
            property_count = len(result.data) if result.data else 0
            health_status['checks']['data_availability'] = {
                'status': 'ok' if property_count > 0 else 'warning',
                'total_properties': property_count,
                'message': f'{property_count} properties available'
            }
            
            # 3. Recent data updates
            recent_updates = self.supabase.table('foia_updates')\
                .select('*')\
                .gte('processed_at', (datetime.now() - timedelta(days=7)).isoformat())\
                .execute()
            
            health_status['checks']['data_freshness'] = {
                'status': 'ok' if recent_updates.data else 'warning',
                'recent_updates': len(recent_updates.data) if recent_updates.data else 0,
                'message': 'Data updated within last 7 days' if recent_updates.data else 'No recent updates'
            }
            
        except Exception as e:
            health_status['overall_status'] = 'error'
            health_status['error'] = str(e)
            logger.error(f"Health check failed: {e}")
        
        return health_status
    
    def get_usage_metrics(self) -> dict:
        """Simple usage metrics for understanding product traction"""
        try:
            # Search activity in last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            
            recent_searches = self.supabase.table('search_activity')\
                .select('*')\
                .gte('searched_at', yesterday.isoformat())\
                .execute()
            
            # Popular cities
            popular_cities = self.supabase.rpc('get_popular_search_cities', {
                'days_back': 7
            }).execute()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'searches_24h': len(recent_searches.data) if recent_searches.data else 0,
                'popular_cities': popular_cities.data if popular_cities.data else [],
                'total_properties_by_city': self._get_property_distribution()
            }
            
        except Exception as e:
            logger.error(f"Usage metrics failed: {e}")
            return {'error': str(e)}
    
    def _get_property_distribution(self) -> dict:
        """Get distribution of properties by city"""
        try:
            result = self.supabase.rpc('get_property_distribution').execute()
            return result.data if result.data else {}
        except:
            return {}
    
    def log_search_activity(self, city: str, results_count: int, user_id: str = None):
        """Simple search logging for analytics"""
        try:
            self.supabase.table('search_activity').insert({
                'user_id': user_id,
                'search_city': city,
                'results_count': results_count
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log search activity: {e}")

# Supporting database functions (add to your schema)
SQL_FUNCTIONS = """
-- Get popular search cities
CREATE OR REPLACE FUNCTION get_popular_search_cities(days_back INTEGER DEFAULT 7)
RETURNS TABLE(city TEXT, search_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        search_city as city,
        COUNT(*) as search_count
    FROM search_activity 
    WHERE searched_at > NOW() - (days_back || ' days')::interval
    GROUP BY search_city
    ORDER BY COUNT(*) DESC
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;

-- Get property distribution by city
CREATE OR REPLACE FUNCTION get_property_distribution()
RETURNS TABLE(city TEXT, property_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.city,
        COUNT(*) as property_count
    FROM properties p
    GROUP BY p.city
    ORDER BY COUNT(*) DESC;
END;
$$ LANGUAGE plpgsql;

-- Simple alerting function (call this from cron job)
CREATE OR REPLACE FUNCTION check_for_alerts()
RETURNS TABLE(alert_type TEXT, message TEXT, severity TEXT) AS $$
BEGIN
    -- Alert if no FOIA updates in 14 days
    IF NOT EXISTS (
        SELECT 1 FROM foia_updates 
        WHERE processed_at > NOW() - INTERVAL '14 days'
    ) THEN
        RETURN QUERY SELECT 
            'stale_data'::TEXT,
            'No FOIA updates in 14+ days'::TEXT,
            'warning'::TEXT;
    END IF;
    
    -- Alert if search volume drops significantly
    IF (
        SELECT COUNT(*) FROM search_activity 
        WHERE searched_at > NOW() - INTERVAL '24 hours'
    ) < (
        SELECT COUNT(*) * 0.3 FROM search_activity 
        WHERE searched_at BETWEEN NOW() - INTERVAL '48 hours' AND NOW() - INTERVAL '24 hours'
    ) THEN
        RETURN QUERY SELECT 
            'low_search_volume'::TEXT,
            'Search volume down 70% from yesterday'::TEXT,
            'warning'::TEXT;
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

if __name__ == "__main__":
    # Example usage
    monitor = SimpleMonitoring(
        supabase_url="your-supabase-url",
        supabase_key="your-supabase-key"
    )
    
    # Health check
    health = monitor.check_system_health()
    print("System Health:")
    print(json.dumps(health, indent=2))
    
    # Usage metrics
    usage = monitor.get_usage_metrics()
    print("\nUsage Metrics:")
    print(json.dumps(usage, indent=2))