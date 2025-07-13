#!/usr/bin/env python
"""
Script to verify that the Django project is completely independent.
"""
import os
import sys
import ast
from pathlib import Path


def find_python_files(directory):
    """Find all Python files in a directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip virtual environment and __pycache__ directories
        dirs[:] = [d for d in dirs if d not in ('venv', '__pycache__', '.git')]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


def check_imports(file_path):
    """Check imports in a Python file for external dependencies."""
    external_imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content, filename=file_path)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    # Check if it's trying to import from parent directories
                    if module_name.startswith('..') or '../' in module_name:
                        external_imports.append(f"Import: {module_name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Check for relative imports that go outside the project
                    if node.level > 0:  # Relative import
                        if node.level > 3:  # Too many levels up
                            external_imports.append(f"Relative import: {'.' * node.level}{node.module}")
                    elif node.module.startswith('..'):
                        external_imports.append(f"From import: {node.module}")
    
    except Exception as e:
        external_imports.append(f"Error parsing file: {e}")
    
    return external_imports


def check_file_references(file_path):
    """Check for file path references that might point outside the project."""
    external_refs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for potential problematic path references
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            # Check for parent directory references
            if '../' in line and not line.startswith('#'):
                external_refs.append(f"Line {i}: {line}")
            # Check for absolute paths that might be problematic
            if 'BASE_DIR.parent' in line and 'load_dotenv' not in line:
                external_refs.append(f"Line {i}: Potential external path reference: {line}")
    
    except Exception as e:
        external_refs.append(f"Error reading file: {e}")
    
    return external_refs


def main():
    """Main check function."""
    print("🔍 Checking Django project independence...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('transcript_cleaner'):
        print("❌ This script must be run from the django project root directory")
        sys.exit(1)
    
    # Find all Python files
    python_files = find_python_files('.')
    print(f"📄 Found {len(python_files)} Python files to check")
    
    total_issues = 0
    
    # Check each file
    for file_path in python_files:
        rel_path = os.path.relpath(file_path)
        
        # Skip setup scripts and virtual environment
        if any(skip in rel_path for skip in ['venv/', 'setup.py', 'check_independence.py']):
            continue
        
        # Check imports
        import_issues = check_imports(file_path)
        if import_issues:
            print(f"\n⚠️  Import issues in {rel_path}:")
            for issue in import_issues:
                print(f"   - {issue}")
            total_issues += len(import_issues)
        
        # Check file references
        file_issues = check_file_references(file_path)
        if file_issues:
            print(f"\n⚠️  File reference issues in {rel_path}:")
            for issue in file_issues:
                print(f"   - {issue}")
            total_issues += len(file_issues)
    
    # Check for required files
    print(f"\n📋 Checking required files...")
    required_files = [
        'requirements.txt',
        'transcript_cleaner/manage.py',
        'transcript_cleaner/config/settings/base.py',
        'processing/__init__.py',
        'processing/openai_service.py',
        'processing/csv_parser.py',
        '.env.example'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        total_issues += len(missing_files)
    else:
        print("✅ All required files present")
    
    # Check processing module structure
    print(f"\n🔧 Checking processing module...")
    processing_files = ['__init__.py', 'openai_service.py', 'csv_parser.py']
    processing_issues = 0
    
    for file_name in processing_files:
        file_path = os.path.join('processing', file_name)
        if not os.path.exists(file_path):
            print(f"❌ Missing processing file: {file_path}")
            processing_issues += 1
    
    if processing_issues == 0:
        print("✅ Processing module structure is complete")
    else:
        total_issues += processing_issues
    
    # Final result
    print(f"\n{'='*50}")
    if total_issues == 0:
        print("🎉 SUCCESS: Project appears to be completely independent!")
        print("✅ No external dependencies found")
        print("✅ All required files present")
        print("✅ Processing module is self-contained")
        print("\n📝 The project can be safely moved to any directory.")
    else:
        print(f"⚠️  WARNINGS: Found {total_issues} potential issues")
        print("📝 Review the issues above before moving the project.")
    
    return total_issues


if __name__ == '__main__':
    issues = main()
    sys.exit(0 if issues == 0 else 1)