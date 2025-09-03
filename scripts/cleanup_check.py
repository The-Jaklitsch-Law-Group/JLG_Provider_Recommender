#!/usr/bin/env python3
"""
Repository cleanup verification script for public deployment.
This script checks for common issues before making a repository public.
"""

import os
import sys
from pathlib import Path
import re

def check_for_sensitive_patterns():
    """Check for potentially sensitive information in text files."""
    sensitive_patterns = [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
        r'token\s*=\s*["\'][^"\']+["\']',
        r'\b[A-Za-z0-9._%+-]+@(?!jaklitschlawgroup\.com|example\.com)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b',  # IP addresses
        r'\b[0-9a-fA-F]{32,}\b',  # Potential hashes/keys
    ]
    
    issues = []
    
    # Files to check
    text_files = [
        '*.py', '*.md', '*.txt', '*.yml', '*.yaml', 
        '*.json', '*.toml', '*.ini', '*.cfg'
    ]
    
    for pattern in text_files:
        for file_path in Path('.').rglob(pattern):
            if any(exclude in str(file_path) for exclude in ['.git', '__pycache__', '.venv', 'node_modules']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for i, line in enumerate(content.split('\n'), 1):
                    for j, regex_pattern in enumerate(sensitive_patterns):
                        matches = re.findall(regex_pattern, line, re.IGNORECASE)
                        if matches:
                            issues.append({
                                'file': str(file_path),
                                'line': i,
                                'pattern': f"Pattern {j+1}",
                                'content': line.strip()[:100] + '...' if len(line.strip()) > 100 else line.strip()
                            })
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")
    
    return issues

def check_file_permissions():
    """Check for files with unusual permissions."""
    issues = []
    
    for file_path in Path('.').rglob('*'):
        if file_path.is_file():
            try:
                stat = file_path.stat()
                # Check for world-writable files
                if stat.st_mode & 0o002:
                    issues.append(f"World-writable file: {file_path}")
                # Check for executable files that shouldn't be
                if stat.st_mode & 0o111 and file_path.suffix in ['.txt', '.md', '.json']:
                    issues.append(f"Unexpected executable file: {file_path}")
            except Exception:
                pass  # Skip files we can't check
    
    return issues

def check_gitignore_coverage():
    """Check if important file types are covered by .gitignore."""
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        return ["Missing .gitignore file"]
    
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    important_patterns = [
        '__pycache__',
        '*.pyc',
        '.env',
        '*.log',
        '.DS_Store',
        'Thumbs.db',
        '*.key',
        'secrets.json'
    ]
    
    missing_patterns = []
    for pattern in important_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)
    
    return missing_patterns

def main():
    """Run all cleanup checks."""
    print("🔍 Running repository cleanup verification...")
    print("=" * 50)
    
    # Check for sensitive patterns
    print("\n📋 Checking for sensitive information...")
    sensitive_issues = check_for_sensitive_patterns()
    if sensitive_issues:
        print("⚠️  Found potential sensitive information:")
        for issue in sensitive_issues[:10]:  # Show first 10 issues
            print(f"  - {issue['file']}:{issue['line']} - {issue['pattern']}")
        if len(sensitive_issues) > 10:
            print(f"  ... and {len(sensitive_issues) - 10} more issues")
    else:
        print("✅ No obvious sensitive information found")
    
    # Check file permissions
    print("\n🔒 Checking file permissions...")
    permission_issues = check_file_permissions()
    if permission_issues:
        print("⚠️  Found permission issues:")
        for issue in permission_issues:
            print(f"  - {issue}")
    else:
        print("✅ File permissions look good")
    
    # Check .gitignore coverage
    print("\n📝 Checking .gitignore coverage...")
    missing_gitignore = check_gitignore_coverage()
    if missing_gitignore:
        print("⚠️  Missing .gitignore patterns:")
        for pattern in missing_gitignore:
            print(f"  - {pattern}")
    else:
        print("✅ .gitignore coverage looks comprehensive")
    
    # Check for common deployment files
    print("\n📦 Checking deployment readiness...")
    deployment_files = {
        'LICENSE': Path('LICENSE').exists(),
        'README.md': Path('README.md').exists(),
        'requirements.txt': Path('requirements.txt').exists(),
        'CONTRIBUTING.md': Path('CONTRIBUTING.md').exists(),
        'SECURITY.md': Path('SECURITY.md').exists(),
        '.gitignore': Path('.gitignore').exists(),
    }
    
    missing_files = [name for name, exists in deployment_files.items() if not exists]
    if missing_files:
        print("⚠️  Missing recommended files:")
        for file in missing_files:
            print(f"  - {file}")
    else:
        print("✅ All recommended deployment files present")
    
    # Summary
    print("\n" + "=" * 50)
    total_issues = len(sensitive_issues) + len(permission_issues) + len(missing_gitignore) + len(missing_files)
    
    if total_issues == 0:
        print("🎉 Repository appears ready for public deployment!")
    else:
        print(f"⚠️  Found {total_issues} issues that should be addressed before public deployment")
        print("\nRecommended actions:")
        if sensitive_issues:
            print("  1. Review and remove any sensitive information")
        if permission_issues:
            print("  2. Fix file permissions")
        if missing_gitignore:
            print("  3. Update .gitignore with missing patterns")
        if missing_files:
            print("  4. Add missing deployment files")
    
    return total_issues == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
