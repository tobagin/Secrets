"""
Password strength calculation utility using zxcvbn.

This module provides utilities for calculating password strength scores
using the industry-standard zxcvbn library with custom thresholds and
easter egg functionality.
"""

from typing import Tuple, List
try:
    import zxcvbn
except ImportError:
    zxcvbn = None


class PasswordStrengthCalculator:
    """Password strength calculator using zxcvbn with custom enhancements."""
    
    @classmethod
    def calculate_strength(cls, password: str, exclude_ambiguous: bool = False) -> Tuple[int, str]:
        """
        Calculate password strength score using zxcvbn.
        
        Args:
            password: The password to analyze
            exclude_ambiguous: Currently unused, kept for API compatibility
            
        Returns:
            Tuple of (score, strength_text) where score is 0-4 and strength_text
            is one of: "Very Weak", "Weak", "Fair", "Good", "Strong"
        """
        if not password:
            return 0, "Very Weak"
        
        # Use zxcvbn if available, otherwise fall back to simple scoring
        if zxcvbn is not None:
            result = zxcvbn.zxcvbn(password)
            score = result['score']  # 0-4 scale
        else:
            # Simple fallback based on length only
            length = len(password)
            if length < 4:
                score = 0
            elif length < 8:
                score = 1
            elif length < 12:
                score = 2
            elif length < 16:
                score = 3
            else:
                score = 4
        
        # Convert score to text using zxcvbn's standard scale
        strength_text = cls._score_to_strength_text(score)
        
        return score, strength_text
    
    
    @classmethod
    def _score_to_strength_text(cls, score: int) -> str:
        """Convert zxcvbn score (0-4) to strength description."""
        strength_labels = [
            "Very Weak",  # 0
            "Weak",       # 1
            "Fair",       # 2
            "Good",       # 3
            "Strong"      # 4
        ]
        return strength_labels[min(max(score, 0), 4)]
    
    @classmethod
    def get_weakness_details(cls, password: str) -> List[str]:
        """
        Get detailed list of password weaknesses using zxcvbn feedback.
        
        Args:
            password: The password to analyze
            
        Returns:
            List of weakness descriptions and suggestions
        """
        if not password:
            return ["Password is empty"]
        
        weaknesses = []
        
        if zxcvbn is not None:
            result = zxcvbn.zxcvbn(password)
            
            # Add zxcvbn feedback
            feedback = result.get('feedback', {})
            warning = feedback.get('warning', '')
            suggestions = feedback.get('suggestions', [])
            
            if warning:
                weaknesses.append(warning)
            
            for suggestion in suggestions:
                weaknesses.append(suggestion)
        else:
            # Fallback feedback when zxcvbn not available
            length = len(password)
            
            if length < 8:
                weaknesses.append("Too short (minimum 8 characters recommended)")
            
            # Character variety checks
            if not any(c.islower() for c in password):
                weaknesses.append("Missing lowercase letters")
            if not any(c.isupper() for c in password):
                weaknesses.append("Missing uppercase letters")
            if not any(c.isdigit() for c in password):
                weaknesses.append("Missing numbers")
            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                weaknesses.append("Missing special characters")
        
        return weaknesses