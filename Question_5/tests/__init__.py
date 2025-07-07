"""
Question 5: Unhappy Flows Test Package

This package contains comprehensive tests for validating robustness against:
- Missing parameters
- API downtime scenarios  
- Malicious payload attempts
- Security vulnerabilities
- Service failures and recovery
"""

__version__ = "1.0.0"
__author__ = "ZUS Coffee AI Team"

# Test categories covered
TEST_CATEGORIES = [
    "Missing Parameters",
    "API Downtime Simulation", 
    "Malicious Payload Protection",
    "Network Failures",
    "Service Dependencies",
    "Input Validation",
    "Security Testing",
    "Concurrent Access",
    "State Management",
    "Error Recovery"
]

# Security test patterns
SECURITY_PATTERNS = {
    "sql_injection": [
        "'; DROP TABLE",
        "' OR 1=1",
        "' UNION SELECT",
        "'; DELETE FROM",
        "'; UPDATE SET"
    ],
    "code_injection": [
        "__import__('os')",
        "eval(",
        "exec(",
        "subprocess.call",
        "os.system"
    ],
    "xss_attempts": [
        "<script>",
        "javascript:",
        "data:text/html",
        "onload=",
        "onerror="
    ],
    "path_traversal": [
        "../",
        "..\\",
        "/etc/passwd",
        "\\windows\\system32",
        "\x00"
    ]
} 