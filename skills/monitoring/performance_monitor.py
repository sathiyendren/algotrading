# Author: sathiyendren
# Email: sathiyendren@gmail.com
# Created: 2026-07-01 01:39:00
# Description: Performance monitoring and alerting skill
# Project: Algo Trading System

import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.logger = logger
        self.performance_metrics = []
        self.alerts = []
        
    def collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_io': psutil.net_io_counters()._asdict()
            }
            
            self.performance_metrics.append(metrics)
            
            # Keep only last 100 metrics
            if len(self.performance_metrics) > 100:
                self.performance_metrics = self.performance_metrics[-100:]
            
            return metrics
        except Exception as e:
            self.logger.error("System metrics collection error: %s", str(e))
            return {'error': str(e)}
    
    def check_performance_alerts(self, metrics):
        """Check for performance alerts"""
        alerts = []
        
        if metrics.get('cpu_percent', 0) > 80:
            alerts.append({
                'type': 'CPU_HIGH',
                'message': f"CPU usage high: {metrics['cpu_percent']}%",
                'timestamp': datetime.now().isoformat()
            })
        
        if metrics.get('memory_percent', 0) > 85:
            alerts.append({
                'type': 'MEMORY_HIGH',
                'message': f"Memory usage high: {metrics['memory_percent']}%",
                'timestamp': datetime.now().isoformat()
            })
        
        if metrics.get('disk_usage', 0) > 90:
            alerts.append({
                'type': 'DISK_FULL',
                'message': f"Disk usage critical: {metrics['disk_usage']}%",
                'timestamp': datetime.now().isoformat()
            })
        
        self.alerts.extend(alerts)
        return alerts
    
    def generate_performance_report(self):
        """Generate performance monitoring report"""
        if not self.performance_metrics:
            return "No performance data available"
        
        latest_metrics = self.performance_metrics[-1]
        avg_cpu = sum(m['cpu_percent'] for m in self.performance_metrics) / len(self.performance_metrics)
        avg_memory = sum(m['memory_percent'] for m in self.performance_metrics) / len(self.performance_metrics)
        
        report = f"""
# Performance Monitoring Report
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Current Metrics
- **CPU Usage**: {latest_metrics['cpu_percent']:.1f}%
- **Memory Usage**: {latest_metrics['memory_percent']:.1f}%
- **Disk Usage**: {latest_metrics['disk_usage']:.1f}%

## Average Metrics (Last {len(self.performance_metrics)} samples)
- **Average CPU**: {avg_cpu:.1f}%
- **Average Memory**: {avg_memory:.1f}%

## Recent Alerts
"""
        
        recent_alerts = self.alerts[-5:] if self.alerts else []
        if recent_alerts:
            for alert in recent_alerts:
                report += f"- {alert['message']} ({alert['timestamp']})\n"
        else:
            report += "No recent alerts\n"
        
        return report

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    print("Performance Monitor skill initialized")
