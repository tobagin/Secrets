"""
Base compliance manager for regulatory compliance frameworks.

This module provides the foundation for implementing compliance with various
regulatory frameworks including HIPAA, PCI DSS, and GDPR.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..security import AuditLogger, EncryptedConfigManager


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    HIPAA = "HIPAA"
    PCI_DSS = "PCI_DSS"
    GDPR = "GDPR"


class ComplianceStatus(Enum):
    """Compliance status levels."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"


class RequirementCategory(Enum):
    """Categories of compliance requirements."""
    ADMINISTRATIVE = "administrative"
    TECHNICAL = "technical"
    PHYSICAL = "physical"
    ORGANIZATIONAL = "organizational"
    DATA_PROTECTION = "data_protection"
    ACCESS_CONTROL = "access_control"
    MONITORING = "monitoring"
    INCIDENT_RESPONSE = "incident_response"
    DOCUMENTATION = "documentation"


@dataclass
class ComplianceRequirement:
    """Represents a single compliance requirement."""
    id: str
    name: str
    description: str
    category: RequirementCategory
    priority: int  # 1 (highest) to 5 (lowest)
    framework: ComplianceFramework
    reference: str  # Reference to regulation section
    verification_method: str
    automated: bool = False
    implemented: bool = False
    last_verified: Optional[datetime] = None
    notes: str = ""
    controls: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)


@dataclass
class ComplianceViolation:
    """Represents a compliance violation."""
    id: str
    requirement_id: str
    severity: str  # critical, high, medium, low
    description: str
    detected_at: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    remediation_steps: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)


@dataclass
class ComplianceReport:
    """Compliance assessment report."""
    framework: ComplianceFramework
    assessment_date: datetime
    status: ComplianceStatus
    score: float  # 0.0 to 100.0
    total_requirements: int
    implemented_requirements: int
    violations: List[ComplianceViolation]
    recommendations: List[str]
    next_review_date: datetime
    auditor: Optional[str] = None
    notes: str = ""


class ComplianceManager(ABC):
    """
    Abstract base class for compliance management.
    
    This class provides the foundation for implementing specific compliance
    frameworks. Each framework (HIPAA, PCI DSS, GDPR) should extend this class.
    """
    
    def __init__(
        self,
        framework: ComplianceFramework,
        config_manager: EncryptedConfigManager,
        audit_logger: AuditLogger,
    ):
        """
        Initialize the compliance manager.
        
        Args:
            framework: The compliance framework this manager handles
            config_manager: Encrypted configuration manager
            audit_logger: Audit logger for compliance events
        """
        self.framework = framework
        self.config = config_manager
        self.audit = audit_logger
        self.logger = logging.getLogger(f"{__name__}.{framework.value}")
        
        # Initialize requirements and violations tracking
        self._requirements: Dict[str, ComplianceRequirement] = {}
        self._violations: List[ComplianceViolation] = []
        self._last_assessment: Optional[ComplianceReport] = None
        
        # Load compliance configuration
        self._load_config()
        
        # Initialize compliance requirements
        self._initialize_requirements()
    
    def _load_config(self) -> None:
        """Load compliance-specific configuration."""
        config_key = f"compliance.{self.framework.value.lower()}"
        self._config = self.config.get_config(config_key, {})
        
        # Set default configuration values
        defaults = {
            "enabled": True,
            "auto_assessment": True,
            "assessment_interval_days": 90,
            "violation_retention_days": 365,
            "require_evidence": True,
            "strict_mode": False,
        }
        
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value
                self.config.set_config(f"{config_key}.{key}", value)
    
    @abstractmethod
    def _initialize_requirements(self) -> None:
        """
        Initialize compliance requirements for the framework.
        
        This method should be implemented by each specific compliance manager
        to define all requirements for their framework.
        """
        pass
    
    def add_requirement(self, requirement: ComplianceRequirement) -> None:
        """Add a compliance requirement."""
        self._requirements[requirement.id] = requirement
        self.logger.info(f"Added requirement: {requirement.id} - {requirement.name}")
    
    def get_requirement(self, requirement_id: str) -> Optional[ComplianceRequirement]:
        """Get a specific requirement by ID."""
        return self._requirements.get(requirement_id)
    
    def get_all_requirements(self) -> List[ComplianceRequirement]:
        """Get all compliance requirements."""
        return list(self._requirements.values())
    
    def get_requirements_by_category(
        self, category: RequirementCategory
    ) -> List[ComplianceRequirement]:
        """Get requirements filtered by category."""
        return [
            req for req in self._requirements.values()
            if req.category == category
        ]
    
    @abstractmethod
    def verify_requirement(
        self, requirement_id: str, evidence: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify if a specific requirement is met.
        
        Args:
            requirement_id: The requirement to verify
            evidence: Optional evidence supporting compliance
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        pass
    
    def mark_requirement_implemented(
        self,
        requirement_id: str,
        evidence: Optional[List[str]] = None,
        notes: str = ""
    ) -> bool:
        """Mark a requirement as implemented."""
        requirement = self._requirements.get(requirement_id)
        if not requirement:
            return False
        
        requirement.implemented = True
        requirement.last_verified = datetime.now()
        requirement.notes = notes
        
        if evidence:
            requirement.evidence.extend(evidence)
        
        # Log the implementation
        self.audit.audit_compliance_event(
            framework=self.framework.value,
            event_type="requirement_implemented",
            requirement_id=requirement_id,
            details={"notes": notes, "evidence_count": len(evidence or [])}
        )
        
        return True
    
    def report_violation(
        self,
        requirement_id: str,
        severity: str,
        description: str,
        remediation_steps: Optional[List[str]] = None,
        evidence: Optional[List[str]] = None
    ) -> ComplianceViolation:
        """Report a compliance violation."""
        violation = ComplianceViolation(
            id=f"{requirement_id}_{datetime.now().timestamp()}",
            requirement_id=requirement_id,
            severity=severity,
            description=description,
            detected_at=datetime.now(),
            remediation_steps=remediation_steps or [],
            evidence=evidence or []
        )
        
        self._violations.append(violation)
        
        # Log the violation
        self.audit.audit_compliance_event(
            framework=self.framework.value,
            event_type="violation_detected",
            requirement_id=requirement_id,
            severity=severity,
            details={"description": description}
        )
        
        return violation
    
    def resolve_violation(
        self,
        violation_id: str,
        evidence: Optional[List[str]] = None
    ) -> bool:
        """Mark a violation as resolved."""
        for violation in self._violations:
            if violation.id == violation_id:
                violation.resolved = True
                violation.resolved_at = datetime.now()
                if evidence:
                    violation.evidence.extend(evidence)
                
                # Log the resolution
                self.audit.audit_compliance_event(
                    framework=self.framework.value,
                    event_type="violation_resolved",
                    violation_id=violation_id,
                    details={"evidence_count": len(evidence or [])}
                )
                
                return True
        return False
    
    def get_active_violations(self) -> List[ComplianceViolation]:
        """Get all active (unresolved) violations."""
        return [v for v in self._violations if not v.resolved]
    
    def assess_compliance(self) -> ComplianceReport:
        """
        Perform a comprehensive compliance assessment.
        
        Returns:
            ComplianceReport with current compliance status
        """
        self.logger.info(f"Starting {self.framework.value} compliance assessment")
        
        # Verify all requirements
        implemented_count = 0
        violations = []
        recommendations = []
        
        for req_id, requirement in self._requirements.items():
            if requirement.automated:
                # Verify automated requirements
                is_compliant, reason = self.verify_requirement(req_id)
                if is_compliant:
                    implemented_count += 1
                elif reason:
                    # Create violation for non-compliant automated check
                    violation = self.report_violation(
                        requirement_id=req_id,
                        severity="high" if requirement.priority <= 2 else "medium",
                        description=reason,
                        remediation_steps=[f"Address issue: {reason}"]
                    )
                    violations.append(violation)
            elif requirement.implemented:
                # Count manually verified requirements
                implemented_count += 1
            else:
                # Add recommendation for unimplemented requirements
                recommendations.append(
                    f"Implement {requirement.name} (Priority: {requirement.priority})"
                )
        
        # Calculate compliance score
        total_requirements = len(self._requirements)
        score = (implemented_count / total_requirements * 100) if total_requirements > 0 else 0.0
        
        # Determine overall status
        if score >= 95:
            status = ComplianceStatus.COMPLIANT
        elif score >= 80:
            status = ComplianceStatus.PARTIAL
        elif score >= 50:
            status = ComplianceStatus.IN_PROGRESS
        else:
            status = ComplianceStatus.NON_COMPLIANT
        
        # Add active violations to the report
        violations.extend(self.get_active_violations())
        
        # Create report
        report = ComplianceReport(
            framework=self.framework,
            assessment_date=datetime.now(),
            status=status,
            score=score,
            total_requirements=total_requirements,
            implemented_requirements=implemented_count,
            violations=violations,
            recommendations=recommendations[:10],  # Top 10 recommendations
            next_review_date=datetime.now() + timedelta(
                days=self._config.get("assessment_interval_days", 90)
            )
        )
        
        self._last_assessment = report
        
        # Log the assessment
        self.audit.audit_compliance_event(
            framework=self.framework.value,
            event_type="assessment_completed",
            details={
                "status": status.value,
                "score": score,
                "violations_count": len(violations),
                "implemented_requirements": implemented_count,
                "total_requirements": total_requirements
            }
        )
        
        return report
    
    def get_last_assessment(self) -> Optional[ComplianceReport]:
        """Get the last compliance assessment report."""
        return self._last_assessment
    
    def export_report(
        self,
        report: ComplianceReport,
        format: str = "json"
    ) -> str:
        """
        Export a compliance report in the specified format.
        
        Args:
            report: The report to export
            format: Export format (json, html, pdf)
            
        Returns:
            Exported report as string
        """
        if format == "json":
            return self._export_json_report(report)
        elif format == "html":
            return self._export_html_report(report)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json_report(self, report: ComplianceReport) -> str:
        """Export report as JSON."""
        data = {
            "framework": report.framework.value,
            "assessment_date": report.assessment_date.isoformat(),
            "status": report.status.value,
            "score": report.score,
            "total_requirements": report.total_requirements,
            "implemented_requirements": report.implemented_requirements,
            "violations": [
                {
                    "id": v.id,
                    "requirement_id": v.requirement_id,
                    "severity": v.severity,
                    "description": v.description,
                    "detected_at": v.detected_at.isoformat(),
                    "resolved": v.resolved,
                    "resolved_at": v.resolved_at.isoformat() if v.resolved_at else None,
                }
                for v in report.violations
            ],
            "recommendations": report.recommendations,
            "next_review_date": report.next_review_date.isoformat(),
            "auditor": report.auditor,
            "notes": report.notes,
        }
        return json.dumps(data, indent=2)
    
    def _export_html_report(self, report: ComplianceReport) -> str:
        """Export report as HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.framework.value} Compliance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; }}
                .status-{report.status.value} {{ 
                    color: {'green' if report.status == ComplianceStatus.COMPLIANT else 'red'};
                    font-weight: bold;
                }}
                .section {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .violation-critical, .violation-high {{ color: red; }}
                .violation-medium {{ color: orange; }}
                .violation-low {{ color: yellow; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report.framework.value} Compliance Report</h1>
                <p>Assessment Date: {report.assessment_date.strftime('%Y-%m-%d %H:%M')}</p>
                <p>Status: <span class="status-{report.status.value}">{report.status.value.upper()}</span></p>
                <p>Compliance Score: {report.score:.1f}%</p>
            </div>
            
            <div class="section">
                <h2>Summary</h2>
                <p>Total Requirements: {report.total_requirements}</p>
                <p>Implemented Requirements: {report.implemented_requirements}</p>
                <p>Active Violations: {len([v for v in report.violations if not v.resolved])}</p>
            </div>
            
            <div class="section">
                <h2>Violations</h2>
                <table>
                    <tr>
                        <th>Requirement ID</th>
                        <th>Severity</th>
                        <th>Description</th>
                        <th>Status</th>
                        <th>Detected</th>
                    </tr>
                    {''.join([
                        f'''<tr>
                            <td>{v.requirement_id}</td>
                            <td class="violation-{v.severity}">{v.severity.upper()}</td>
                            <td>{v.description}</td>
                            <td>{'Resolved' if v.resolved else 'Active'}</td>
                            <td>{v.detected_at.strftime('%Y-%m-%d')}</td>
                        </tr>'''
                        for v in report.violations
                    ])}
                </table>
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
                <ul>
                    {''.join([f'<li>{rec}</li>' for rec in report.recommendations])}
                </ul>
            </div>
            
            <div class="section">
                <p>Next Review Date: {report.next_review_date.strftime('%Y-%m-%d')}</p>
                {f'<p>Auditor: {report.auditor}</p>' if report.auditor else ''}
                {f'<p>Notes: {report.notes}</p>' if report.notes else ''}
            </div>
        </body>
        </html>
        """
        return html
    
    def cleanup_old_violations(self, days: Optional[int] = None) -> int:
        """
        Clean up old resolved violations.
        
        Args:
            days: Number of days to retain violations (uses config if not specified)
            
        Returns:
            Number of violations removed
        """
        retention_days = days or self._config.get("violation_retention_days", 365)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        original_count = len(self._violations)
        self._violations = [
            v for v in self._violations
            if not v.resolved or v.resolved_at > cutoff_date
        ]
        
        removed_count = original_count - len(self._violations)
        if removed_count > 0:
            self.logger.info(f"Cleaned up {removed_count} old violations")
            
        return removed_count