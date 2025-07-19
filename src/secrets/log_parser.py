#!/usr/bin/env python3
"""
Log Parser for Secrets application structured logs.
Provides tools for parsing, analyzing, and querying structured log files.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator, Union
from collections import defaultdict, Counter
from dataclasses import dataclass


@dataclass
class LogEntry:
    """Structured representation of a log entry."""
    timestamp: datetime
    level: str
    message: str
    logger_name: str
    module: str
    function: str
    line: int
    category: Optional[str] = None
    user_action: bool = False
    security_event: bool = False
    data: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    exception: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None


class LogParser:
    """Parser for structured log files."""
    
    def __init__(self):
        self.entries: List[LogEntry] = []
    
    def parse_file(self, log_file: Union[str, Path]) -> List[LogEntry]:
        """Parse a structured log file."""
        log_file = Path(log_file)
        entries = []
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = self.parse_line(line)
                    if entry:
                        entries.append(entry)
                except Exception as e:
                    print(f"Error parsing line {line_num}: {e}")
                    continue
        
        self.entries = entries
        return entries
    
    def parse_line(self, line: str) -> Optional[LogEntry]:
        """Parse a single log line."""
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            # Handle non-JSON lines (human readable format)
            return self._parse_human_readable(line)
        
        # Parse structured JSON log
        return self._parse_structured(data)
    
    def _parse_structured(self, data: Dict[str, Any]) -> LogEntry:
        """Parse structured JSON log data."""
        # Handle timestamp
        timestamp_str = data.get('@timestamp', data.get('timestamp'))
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)
        
        # Extract logger information
        logger_info = data.get('logger', {})
        if isinstance(logger_info, str):
            logger_name = logger_info
            module = 'unknown'
            function = 'unknown'
            line = 0
        else:
            logger_name = logger_info.get('name', 'unknown')
            module = logger_info.get('module', 'unknown')
            function = logger_info.get('function', 'unknown')
            line = logger_info.get('line', 0)
        
        return LogEntry(
            timestamp=timestamp,
            level=data.get('level', 'INFO'),
            message=data.get('message', ''),
            logger_name=logger_name,
            module=module,
            function=function,
            line=line,
            category=data.get('category'),
            user_action=data.get('user_action', False),
            security_event=data.get('security_event', False),
            data=data.get('data'),
            metrics=data.get('metrics'),
            tags=data.get('tags'),
            exception=data.get('exception'),
            raw_data=data
        )
    
    def _parse_human_readable(self, line: str) -> Optional[LogEntry]:
        """Parse human-readable log format."""
        # Pattern for human readable logs: 2025-01-01 12:00:00 [    INFO] module:name: message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[([A-Z\s]+)\] ([^:]+): (.*)'
        match = re.match(pattern, line)
        
        if not match:
            return None
        
        timestamp_str, level, logger_name, message = match.groups()
        
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        except ValueError:
            timestamp = datetime.now(timezone.utc)
        
        return LogEntry(
            timestamp=timestamp,
            level=level.strip(),
            message=message,
            logger_name=logger_name,
            module='unknown',
            function='unknown',
            line=0
        )
    
    def filter_by_level(self, level: str) -> List[LogEntry]:
        """Filter entries by log level."""
        return [entry for entry in self.entries if entry.level == level.upper()]
    
    def filter_by_category(self, category: str) -> List[LogEntry]:
        """Filter entries by category."""
        return [entry for entry in self.entries if entry.category == category]
    
    def filter_by_time_range(self, start: datetime, end: datetime) -> List[LogEntry]:
        """Filter entries by time range."""
        return [entry for entry in self.entries 
                if start <= entry.timestamp <= end]
    
    def filter_user_actions(self) -> List[LogEntry]:
        """Get only user action entries."""
        return [entry for entry in self.entries if entry.user_action]
    
    def filter_security_events(self) -> List[LogEntry]:
        """Get only security event entries."""
        return [entry for entry in self.entries if entry.security_event]
    
    def filter_errors(self) -> List[LogEntry]:
        """Get only error and critical entries."""
        return [entry for entry in self.entries 
                if entry.level in ['ERROR', 'CRITICAL']]
    
    def search_messages(self, pattern: str, case_sensitive: bool = False) -> List[LogEntry]:
        """Search log messages using regex pattern."""
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        
        return [entry for entry in self.entries 
                if regex.search(entry.message)]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive log statistics."""
        if not self.entries:
            return {}
        
        # Level distribution
        level_counts = Counter(entry.level for entry in self.entries)
        
        # Category distribution
        category_counts = Counter(entry.category for entry in self.entries 
                                if entry.category)
        
        # Module distribution
        module_counts = Counter(entry.module for entry in self.entries)
        
        # Time range
        timestamps = [entry.timestamp for entry in self.entries]
        time_range = {
            'start': min(timestamps),
            'end': max(timestamps),
            'duration': max(timestamps) - min(timestamps)
        }
        
        # Error analysis
        errors = self.filter_errors()
        error_modules = Counter(entry.module for entry in errors)
        
        # User actions
        user_actions = len(self.filter_user_actions())
        security_events = len(self.filter_security_events())
        
        return {
            'total_entries': len(self.entries),
            'level_distribution': dict(level_counts),
            'category_distribution': dict(category_counts),
            'module_distribution': dict(module_counts),
            'time_range': time_range,
            'error_count': len(errors),
            'error_modules': dict(error_modules),
            'user_actions': user_actions,
            'security_events': security_events
        }
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a comprehensive log analysis report."""
        stats = self.get_statistics()
        
        if not stats:
            return "No log entries found."
        
        report_lines = [
            "# Secrets Application Log Analysis Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            f"- Total log entries: {stats['total_entries']:,}",
            f"- Time range: {stats['time_range']['start']} to {stats['time_range']['end']}",
            f"- Duration: {stats['time_range']['duration']}",
            f"- Error count: {stats['error_count']}",
            f"- User actions: {stats['user_actions']}",
            f"- Security events: {stats['security_events']}",
            "",
            "## Log Level Distribution"
        ]
        
        for level, count in sorted(stats['level_distribution'].items()):
            percentage = (count / stats['total_entries']) * 100
            report_lines.append(f"- {level}: {count:,} ({percentage:.1f}%)")
        
        if stats['category_distribution']:
            report_lines.extend([
                "",
                "## Category Distribution"
            ])
            for category, count in sorted(stats['category_distribution'].items()):
                percentage = (count / stats['total_entries']) * 100
                report_lines.append(f"- {category}: {count:,} ({percentage:.1f}%)")
        
        if stats['error_modules']:
            report_lines.extend([
                "",
                "## Top Error Modules"
            ])
            for module, count in sorted(stats['error_modules'].items(), 
                                      key=lambda x: x[1], reverse=True)[:10]:
                report_lines.append(f"- {module}: {count:,} errors")
        
        # Recent errors
        recent_errors = sorted(self.filter_errors(), 
                             key=lambda x: x.timestamp, reverse=True)[:10]
        if recent_errors:
            report_lines.extend([
                "",
                "## Recent Errors (Last 10)"
            ])
            for error in recent_errors:
                report_lines.append(f"- {error.timestamp}: {error.message}")
        
        report = "\\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report


class LogAnalyzer:
    """Advanced log analysis tools."""
    
    def __init__(self, parser: LogParser):
        self.parser = parser
    
    def find_patterns(self, time_window_minutes: int = 5) -> Dict[str, List[LogEntry]]:
        """Find common error patterns within time windows."""
        patterns = defaultdict(list)
        errors = self.parser.filter_errors()
        
        # Group errors by message pattern
        for error in errors:
            # Create a pattern by removing variable parts
            pattern = re.sub(r'\\b\\d+\\b', 'NUMBER', error.message)
            pattern = re.sub(r'\\b[a-f0-9]{8,}\\b', 'HASH', pattern)
            pattern = re.sub(r'/[^\\s]+', 'PATH', pattern)
            patterns[pattern].append(error)
        
        # Filter patterns with multiple occurrences
        return {pattern: entries for pattern, entries in patterns.items() 
                if len(entries) > 1}
    
    def performance_analysis(self) -> Dict[str, Any]:
        """Analyze performance-related metrics."""
        entries_with_metrics = [entry for entry in self.parser.entries 
                              if entry.metrics]
        
        if not entries_with_metrics:
            return {"message": "No performance metrics found"}
        
        # Aggregate metrics
        all_metrics = defaultdict(list)
        for entry in entries_with_metrics:
            for key, value in entry.metrics.items():
                if isinstance(value, (int, float)):
                    all_metrics[key].append(value)
        
        # Calculate statistics
        metric_stats = {}
        for metric, values in all_metrics.items():
            metric_stats[metric] = {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'total': sum(values)
            }
        
        return metric_stats
    
    def security_audit(self) -> Dict[str, Any]:
        """Generate security audit summary."""
        security_events = self.parser.filter_security_events()
        user_actions = self.parser.filter_user_actions()
        
        # Analyze security events by type
        event_types = defaultdict(int)
        for event in security_events:
            if event.data and 'event' in event.data:
                event_types[event.data['event']] += 1
        
        # Analyze user actions by type  
        action_types = defaultdict(int)
        for action in user_actions:
            if action.data and 'action' in action.data:
                action_types[action.data['action']] += 1
        
        return {
            'total_security_events': len(security_events),
            'total_user_actions': len(user_actions),
            'security_event_types': dict(event_types),
            'user_action_types': dict(action_types),
            'timeline': [
                {
                    'timestamp': event.timestamp.isoformat(),
                    'type': 'security' if event.security_event else 'user_action',
                    'message': event.message
                }
                for event in sorted(security_events + user_actions, 
                                  key=lambda x: x.timestamp)[-20:]  # Last 20 events
            ]
        }


def main():
    """Command line interface for log analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Secrets application logs')
    parser.add_argument('log_file', help='Path to log file')
    parser.add_argument('--output', '-o', help='Output report file')
    parser.add_argument('--format', choices=['json', 'text'], default='text',
                       help='Output format')
    parser.add_argument('--filter-level', help='Filter by log level')
    parser.add_argument('--filter-category', help='Filter by category')
    parser.add_argument('--errors-only', action='store_true', 
                       help='Show only errors')
    parser.add_argument('--security-only', action='store_true',
                       help='Show only security events')
    
    args = parser.parse_args()
    
    # Parse log file
    log_parser = LogParser()
    try:
        entries = log_parser.parse_file(args.log_file)
        print(f"Parsed {len(entries)} log entries")
    except FileNotFoundError:
        print(f"Error: Log file '{args.log_file}' not found")
        return 1
    except Exception as e:
        print(f"Error parsing log file: {e}")
        return 1
    
    # Apply filters
    if args.filter_level:
        entries = log_parser.filter_by_level(args.filter_level)
    elif args.filter_category:
        entries = log_parser.filter_by_category(args.filter_category)
    elif args.errors_only:
        entries = log_parser.filter_errors()
    elif args.security_only:
        entries = log_parser.filter_security_events()
    
    # Generate output
    if args.format == 'json':
        output = {
            'entries': [
                {
                    'timestamp': entry.timestamp.isoformat(),
                    'level': entry.level,
                    'message': entry.message,
                    'module': entry.module,
                    'category': entry.category
                }
                for entry in entries
            ],
            'statistics': log_parser.get_statistics()
        }
        output_text = json.dumps(output, indent=2, default=str)
    else:
        # Generate text report
        output_text = log_parser.generate_report()
    
    # Output results
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"Report saved to {args.output}")
    else:
        print(output_text)
    
    return 0


if __name__ == '__main__':
    exit(main())