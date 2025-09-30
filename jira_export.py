#!/usr/bin/env python3
"""
Jira Release Notes Exporter
Exports issues by fixVersion to JSON format
"""

import os
import json
import sys
from typing import List, Dict, Any

try:
    from atlassian import Jira
except ImportError:
    print("Error: atlassian-python-api not installed")
    print("Install it with: pip install atlassian-python-api")
    sys.exit(1)


def get_jira_client() -> Jira:
    """Initialize Jira client from environment variables"""
    jira_url = os.getenv('JIRA_URL')
    jira_username = os.getenv('JIRA_USERNAME')
    jira_token = os.getenv('JIRA_API_TOKEN')
    
    if not all([jira_url, jira_username, jira_token]):
        print("Error: Missing environment variables")
        print("Required: JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN")
        sys.exit(1)
    
    return Jira(
        url=jira_url,
        username=jira_username,
        password=jira_token
    )


def export_issues_by_version(project_key: str, fix_version: str, output_file: str = None) -> Dict[str, Any]:
    """
    Export Jira issues by fixVersion to JSON grouped by issue type
    
    Args:
        project_key: Jira project key (e.g., 'PROJ')
        fix_version: Fix version name (e.g., '1.0.0')
        output_file: Optional output file path (default: release_notes_{version}.json)
    
    Returns:
        Dictionary with issues grouped by type and list of components
    """
    jira = get_jira_client()
    
    # JQL query to find issues
    jql = f'project = {project_key} AND fixVersion = "{fix_version}" ORDER BY issuetype ASC, key ASC'
    
    print(f"Searching for issues with JQL: {jql}")
    
    # Search issues with specific fields
    issues = jira.jql(jql, fields='key,summary,components,issuetype', limit=1000)
    
    # Group issues by type and collect all components
    grouped_data = {}
    all_components = set()
    
    for issue in issues.get('issues', []):
        # Extract issue type
        issue_type = issue['fields']['issuetype']['name']
        
        # Extract components
        components = [comp['name'] for comp in issue['fields'].get('components', [])]
        all_components.update(components)
        
        # Normalize issue type name for grouping
        # Story, Task, Improvement -> improvements
        # Bug -> bug fixes
        # Epic -> epics
        if issue_type.lower() in ['story', 'task', 'improvement']:
            group_name = 'improvements'
        elif issue_type.lower() == 'bug':
            group_name = 'bug fixes'
        elif issue_type.lower() == 'epic':
            group_name = 'epics'
        else:
            group_name = issue_type.lower() + 's'
        
        # Initialize group if not exists
        if group_name not in grouped_data:
            grouped_data[group_name] = []
        
        # Add issue to group
        grouped_data[group_name].append(f"{issue['key']} - {issue['fields']['summary']}")
    
    # Create final export structure
    export_data = grouped_data.copy()
    export_data['components'] = sorted(list(all_components))
    
    # Set default output file name if not provided
    if not output_file:
        output_file = f"release_notes_{fix_version.replace('.', '_').replace(' ', '_')}.json"
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    total_issues = sum(len(issues) for key, issues in export_data.items() if key != 'components')
    print(f"\nExported {total_issues} issues to {output_file}")
    
    return export_data


def print_summary(export_data: Dict[str, Any]):
    """Print a brief summary of exported issues"""
    print(f"\n{'='*60}")
    print(f"RELEASE NOTES SUMMARY")
    print(f"{'='*60}")
    
    # Count total issues
    total_issues = sum(len(issues) for key, issues in export_data.items() if key != 'components')
    print(f"Total issues: {total_issues}\n")
    
    # Print issues by type
    for group_name, issues in export_data.items():
        if group_name == 'components':
            continue
        print(f"{group_name.upper()}:")
        for issue in issues:
            print(f"  - {issue}")
        print()
    
    # Print components
    if 'components' in export_data and export_data['components']:
        print("COMPONENTS:")
        for component in export_data['components']:
            print(f"  - {component}")
    
    print(f"\n{'='*60}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python jira_export.py <PROJECT_KEY> <FIX_VERSION> [output_file.json]")
        print("\nExample: python jira_export.py PROJ 1.0.0")
        print("         python jira_export.py PROJ '1.0.0' my_release_notes.json")
        print("\nEnvironment variables required:")
        print("  JIRA_URL - Your Jira instance URL (e.g., https://your-domain.atlassian.net)")
        print("  JIRA_USERNAME - Your Jira username/email")
        print("  JIRA_API_TOKEN - Your Jira API token")
        sys.exit(1)
    
    project = sys.argv[1]
    version = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        issues = export_issues_by_version(project, version, output)
        print_summary(issues)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
