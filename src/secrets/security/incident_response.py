"""Security incident response system."""

import json
import logging
import os
import smtplib
import subprocess
import time
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import threading

from .audit_logger import AuditEventType, AuditLevel, get_audit_logger

logger = logging.getLogger(__name__)


class IncidentSeverity(Enum):
    """Incident severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    """Incident status values."""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class ResponseAction(Enum):
    """Types of automated response actions."""
    LOG_ONLY = "log_only"
    ALERT = "alert"
    LOCK_APPLICATION = "lock_application"
    DISABLE_FEATURES = "disable_features"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"


@dataclass
class SecurityIncident:
    """Security incident data structure."""
    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    detected_at: str
    source: str
    indicators: List[str]
    affected_resources: List[str]
    response_actions: List[ResponseAction]
    details: Dict[str, Any]
    resolved_at: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['status'] = self.status.value
        data['response_actions'] = [action.value for action in self.response_actions]
        return data


@dataclass
class IncidentRule:
    """Rule for detecting security incidents."""
    rule_id: str
    name: str
    description: str
    severity: IncidentSeverity
    conditions: Dict[str, Any]
    response_actions: List[ResponseAction]
    enabled: bool = True
    cooldown_seconds: int = 300  # 5 minutes


class IncidentDetector:
    """Detects security incidents based on rules."""
    
    def __init__(self):
        """Initialize incident detector."""
        self.rules: Dict[str, IncidentRule] = {}
        self._last_triggered: Dict[str, float] = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Set up default incident detection rules."""
        # Multiple failed authentication attempts
        self.add_rule(IncidentRule(
            rule_id="auth_bruteforce",
            name="Authentication Brute Force",
            description="Multiple failed authentication attempts detected",
            severity=IncidentSeverity.HIGH,
            conditions={
                "event_types": [AuditEventType.AUTH_FAILURE],
                "count_threshold": 5,
                "time_window_seconds": 300,
                "same_source": True
            },
            response_actions=[ResponseAction.ALERT, ResponseAction.LOCK_APPLICATION],
            cooldown_seconds=600
        ))
        
        # Suspicious file access patterns
        self.add_rule(IncidentRule(
            rule_id="suspicious_access",
            name="Suspicious File Access",
            description="Unusual password access patterns detected",
            severity=IncidentSeverity.MEDIUM,
            conditions={
                "event_types": [AuditEventType.PASSWORD_ACCESSED],
                "count_threshold": 20,
                "time_window_seconds": 60,
                "different_resources": True
            },
            response_actions=[ResponseAction.ALERT],
            cooldown_seconds=300
        ))
        
        # Application crashes
        self.add_rule(IncidentRule(
            rule_id="app_crash",
            name="Application Crash",
            description="Application crash detected",
            severity=IncidentSeverity.HIGH,
            conditions={
                "event_types": [AuditEventType.APP_CRASHED]
            },
            response_actions=[ResponseAction.ALERT],
            cooldown_seconds=60
        ))
        
        # Security violations
        self.add_rule(IncidentRule(
            rule_id="security_violation",
            name="Security Violation",
            description="Security violation detected",
            severity=IncidentSeverity.CRITICAL,
            conditions={
                "event_types": [AuditEventType.SECURITY_VIOLATION]
            },
            response_actions=[ResponseAction.ALERT, ResponseAction.EMERGENCY_SHUTDOWN],
            cooldown_seconds=0  # No cooldown for critical violations
        ))
        
        # Hardware key tampering
        self.add_rule(IncidentRule(
            rule_id="hardware_key_tamper",
            name="Hardware Key Tampering",
            description="Hardware key removed during authentication",
            severity=IncidentSeverity.HIGH,
            conditions={
                "event_types": [AuditEventType.TWO_FA_FAILURE],
                "details_contains": {"method": "hardware_key"}
            },
            response_actions=[ResponseAction.ALERT],
            cooldown_seconds=300
        ))
    
    def add_rule(self, rule: IncidentRule):
        """Add an incident detection rule."""
        self.rules[rule.rule_id] = rule
        logger.info(f"Added incident detection rule: {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove an incident detection rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed incident detection rule: {rule_id}")
            return True
        return False
    
    def check_for_incidents(self, recent_events: List[Dict[str, Any]]) -> List[SecurityIncident]:
        """
        Check recent events for incidents.
        
        Args:
            recent_events: List of recent audit events
            
        Returns:
            List of detected incidents
        """
        incidents = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # Check cooldown
            last_triggered = self._last_triggered.get(rule.rule_id, 0)
            if time.time() - last_triggered < rule.cooldown_seconds:
                continue
            
            incident = self._check_rule(rule, recent_events)
            if incident:
                incidents.append(incident)
                self._last_triggered[rule.rule_id] = time.time()
        
        return incidents
    
    def _check_rule(self, rule: IncidentRule, events: List[Dict[str, Any]]) -> Optional[SecurityIncident]:
        """Check a specific rule against events."""
        conditions = rule.conditions
        
        # Filter events by type
        matching_events = []
        for event in events:
            event_type = event.get('event_type')
            if event_type in [et.value for et in conditions.get('event_types', [])]:
                matching_events.append(event)
        
        if not matching_events:
            return None
        
        # Check time window
        time_window = conditions.get('time_window_seconds')
        if time_window:
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=time_window)
            cutoff_str = cutoff_time.isoformat()
            
            matching_events = [
                event for event in matching_events
                if event.get('timestamp', '') > cutoff_str
            ]
        
        # Check count threshold
        count_threshold = conditions.get('count_threshold', 1)
        if len(matching_events) < count_threshold:
            return None
        
        # Check additional conditions
        if conditions.get('same_source'):
            sources = set(event.get('source_ip') for event in matching_events)
            if len(sources) > 1:
                return None
        
        if conditions.get('different_resources'):
            resources = set(event.get('resource') for event in matching_events)
            if len(resources) < count_threshold // 2:  # At least half should be different
                return None
        
        # Check detail conditions
        details_contains = conditions.get('details_contains')
        if details_contains:
            matching_events = [
                event for event in matching_events
                if all(
                    event.get('details', {}).get(key) == value
                    for key, value in details_contains.items()
                )
            ]
            
            if not matching_events:
                return None
        
        # Create incident
        incident_id = f"{rule.rule_id}_{int(time.time())}"
        
        indicators = []
        affected_resources = set()
        
        for event in matching_events:
            indicators.append(f"{event.get('event_type')}: {event.get('message')}")
            if event.get('resource'):
                affected_resources.add(event.get('resource'))
        
        incident = SecurityIncident(
            incident_id=incident_id,
            title=rule.name,
            description=rule.description,
            severity=rule.severity,
            status=IncidentStatus.DETECTED,
            detected_at=datetime.now(timezone.utc).isoformat(),
            source="automated_detection",
            indicators=indicators[:10],  # Limit to 10 indicators
            affected_resources=list(affected_resources),
            response_actions=rule.response_actions,
            details={
                'rule_id': rule.rule_id,
                'matching_events_count': len(matching_events),
                'detection_conditions': conditions
            }
        )
        
        return incident


class IncidentResponder:
    """Handles automated responses to security incidents."""
    
    def __init__(self):
        """Initialize incident responder."""
        self.response_handlers: Dict[ResponseAction, Callable] = {
            ResponseAction.LOG_ONLY: self._log_only,
            ResponseAction.ALERT: self._send_alert,
            ResponseAction.LOCK_APPLICATION: self._lock_application,
            ResponseAction.DISABLE_FEATURES: self._disable_features,
            ResponseAction.EMERGENCY_SHUTDOWN: self._emergency_shutdown
        }
        self._email_config = None
        self._lock_callbacks: List[Callable] = []
        self._shutdown_callbacks: List[Callable] = []
    
    def configure_email_alerts(self, smtp_server: str, smtp_port: int,
                              username: str, password: str, recipients: List[str]):
        """Configure email alerting."""
        self._email_config = {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'username': username,
            'password': password,
            'recipients': recipients
        }
    
    def add_lock_callback(self, callback: Callable):
        """Add callback for application locking."""
        self._lock_callbacks.append(callback)
    
    def add_shutdown_callback(self, callback: Callable):
        """Add callback for emergency shutdown."""
        self._shutdown_callbacks.append(callback)
    
    def respond_to_incident(self, incident: SecurityIncident):
        """Execute response actions for an incident."""
        logger.warning(f"Responding to incident: {incident.title} ({incident.incident_id})")
        
        for action in incident.response_actions:
            handler = self.response_handlers.get(action)
            if handler:
                try:
                    handler(incident)
                except Exception as e:
                    logger.error(f"Failed to execute response action {action.value}: {e}")
            else:
                logger.warning(f"No handler for response action: {action.value}")
    
    def _log_only(self, incident: SecurityIncident):
        """Log incident without additional action."""
        audit_logger = get_audit_logger()
        audit_logger.log_security_event(
            AuditEventType.SUSPICIOUS_ACTIVITY,
            f"Security incident detected: {incident.title}",
            AuditLevel.HIGH,
            details=incident.to_dict()
        )
    
    def _send_alert(self, incident: SecurityIncident):
        """Send alert notification."""
        self._log_only(incident)  # Always log
        
        # Send email if configured
        if self._email_config:
            self._send_email_alert(incident)
        
        # Send desktop notification
        self._send_desktop_notification(incident)
    
    def _send_email_alert(self, incident: SecurityIncident):
        """Send email alert."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self._email_config['username']
            msg['To'] = ', '.join(self._email_config['recipients'])
            msg['Subject'] = f"SECURITY ALERT: {incident.title}"
            
            body = f"""
Security Incident Detected

Incident ID: {incident.incident_id}
Title: {incident.title}
Severity: {incident.severity.value.upper()}
Detected At: {incident.detected_at}

Description:
{incident.description}

Indicators:
{chr(10).join(f"- {indicator}" for indicator in incident.indicators)}

Affected Resources:
{chr(10).join(f"- {resource}" for resource in incident.affected_resources)}

Please investigate immediately.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self._email_config['smtp_server'], self._email_config['smtp_port'])
            server.starttls()
            server.login(self._email_config['username'], self._email_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent for incident {incident.incident_id}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _send_desktop_notification(self, incident: SecurityIncident):
        """Send desktop notification."""
        try:
            # Try different notification methods
            notification_commands = [
                ['notify-send', '--urgency=critical', 
                 f'Security Alert: {incident.title}', incident.description],
                ['zenity', '--warning', '--text', 
                 f'Security Alert: {incident.title}\n\n{incident.description}']
            ]
            
            for cmd in notification_commands:
                try:
                    subprocess.run(cmd, timeout=5, capture_output=True)
                    logger.info(f"Desktop notification sent for incident {incident.incident_id}")
                    break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
        except Exception as e:
            logger.error(f"Failed to send desktop notification: {e}")
    
    def _lock_application(self, incident: SecurityIncident):
        """Lock the application."""
        self._send_alert(incident)  # Always send alert
        
        logger.critical(f"Locking application due to incident: {incident.incident_id}")
        
        for callback in self._lock_callbacks:
            try:
                callback(incident)
            except Exception as e:
                logger.error(f"Lock callback failed: {e}")
    
    def _disable_features(self, incident: SecurityIncident):
        """Disable non-essential features."""
        self._send_alert(incident)  # Always send alert
        
        logger.warning(f"Disabling features due to incident: {incident.incident_id}")
        
        # This would disable features like:
        # - Git synchronization
        # - Password export
        # - Clipboard operations
        # Implementation depends on application architecture
    
    def _emergency_shutdown(self, incident: SecurityIncident):
        """Emergency shutdown of the application."""
        self._send_alert(incident)  # Always send alert
        
        logger.critical(f"Emergency shutdown due to incident: {incident.incident_id}")
        
        for callback in self._shutdown_callbacks:
            try:
                callback(incident)
            except Exception as e:
                logger.error(f"Shutdown callback failed: {e}")
        
        # Force exit after callbacks
        threading.Timer(5.0, lambda: os._exit(1)).start()


class IncidentManager:
    """Main incident response management system."""
    
    def __init__(self, config_dir: str):
        """Initialize incident manager."""
        self.config_dir = config_dir
        self.detector = IncidentDetector()
        self.responder = IncidentResponder()
        self.incidents: Dict[str, SecurityIncident] = {}
        self._monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()
    
    def start_monitoring(self, check_interval: int = 30):
        """
        Start continuous incident monitoring.
        
        Args:
            check_interval: Check interval in seconds
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        self._stop_event.clear()
        
        def monitor_loop():
            while not self._stop_event.is_set():
                try:
                    self._check_for_incidents()
                    self._stop_event.wait(check_interval)
                except Exception as e:
                    logger.error(f"Incident monitoring error: {e}")
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("Incident monitoring started")
    
    def stop_monitoring(self):
        """Stop incident monitoring."""
        if not self._monitoring:
            return
        
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        
        self._monitoring = False
        logger.info("Incident monitoring stopped")
    
    def _check_for_incidents(self):
        """Check for new incidents."""
        try:
            audit_logger = get_audit_logger()
            recent_events = audit_logger.get_recent_events(count=1000)
            
            incidents = self.detector.check_for_incidents(recent_events)
            
            for incident in incidents:
                self.handle_incident(incident)
                
        except Exception as e:
            logger.error(f"Failed to check for incidents: {e}")
    
    def handle_incident(self, incident: SecurityIncident):
        """Handle a detected incident."""
        # Store incident
        self.incidents[incident.incident_id] = incident
        
        logger.warning(f"Security incident detected: {incident.title} (ID: {incident.incident_id})")
        
        # Execute response
        self.responder.respond_to_incident(incident)
        
        # Update status
        incident.status = IncidentStatus.INVESTIGATING
    
    def resolve_incident(self, incident_id: str, resolution_notes: str = ""):
        """Mark an incident as resolved."""
        if incident_id in self.incidents:
            incident = self.incidents[incident_id]
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = datetime.now(timezone.utc).isoformat()
            incident.resolution_notes = resolution_notes
            
            logger.info(f"Incident resolved: {incident_id}")
            return True
        
        return False
    
    def mark_false_positive(self, incident_id: str):
        """Mark an incident as a false positive."""
        if incident_id in self.incidents:
            incident = self.incidents[incident_id]
            incident.status = IncidentStatus.FALSE_POSITIVE
            incident.resolved_at = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"Incident marked as false positive: {incident_id}")
            return True
        
        return False
    
    def get_incidents(self, status: Optional[IncidentStatus] = None,
                     severity: Optional[IncidentSeverity] = None) -> List[SecurityIncident]:
        """Get incidents with optional filtering."""
        incidents = list(self.incidents.values())
        
        if status:
            incidents = [i for i in incidents if i.status == status]
        
        if severity:
            incidents = [i for i in incidents if i.severity == severity]
        
        # Sort by detection time (newest first)
        incidents.sort(key=lambda x: x.detected_at, reverse=True)
        
        return incidents
    
    def get_incident_summary(self) -> Dict[str, Any]:
        """Get incident summary statistics."""
        incidents = list(self.incidents.values())
        
        # Count by status
        status_counts = {}
        for status in IncidentStatus:
            status_counts[status.value] = len([i for i in incidents if i.status == status])
        
        # Count by severity
        severity_counts = {}
        for severity in IncidentSeverity:
            severity_counts[severity.value] = len([i for i in incidents if i.severity == severity])
        
        # Recent incidents (last 24 hours)
        cutoff = datetime.now(timezone.utc) - timedelta(days=1)
        recent_incidents = [
            i for i in incidents
            if datetime.fromisoformat(i.detected_at.replace('Z', '+00:00')) > cutoff
        ]
        
        return {
            'total_incidents': len(incidents),
            'recent_incidents_24h': len(recent_incidents),
            'status_counts': status_counts,
            'severity_counts': severity_counts,
            'monitoring_active': self._monitoring
        }
    
    def configure_email_alerts(self, smtp_server: str, smtp_port: int,
                              username: str, password: str, recipients: List[str]):
        """Configure email alerting."""
        self.responder.configure_email_alerts(smtp_server, smtp_port, username, password, recipients)
    
    def add_response_callbacks(self, lock_callback: Optional[Callable] = None,
                              shutdown_callback: Optional[Callable] = None):
        """Add response callbacks."""
        if lock_callback:
            self.responder.add_lock_callback(lock_callback)
        
        if shutdown_callback:
            self.responder.add_shutdown_callback(shutdown_callback)
    
    def export_incidents(self, output_file: str) -> bool:
        """Export incidents to JSON file."""
        try:
            incidents_data = [incident.to_dict() for incident in self.incidents.values()]
            
            with open(output_file, 'w') as f:
                json.dump(incidents_data, f, indent=2)
            
            logger.info(f"Exported {len(incidents_data)} incidents to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export incidents: {e}")
            return False