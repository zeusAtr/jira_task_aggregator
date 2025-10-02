#!/usr/bin/env python3
"""
Jira Release Notes Exporter - Grouped by Release Announce Type
"""

import os
import json
import sys
from typing import Dict, Any
import requests
from requests.auth import HTTPBasicAuth


def get_jira_credentials():
    """Get Jira credentials from environment variables"""
    jira_url = os.getenv('JIRA_URL')
    jira_username = os.getenv('JIRA_USERNAME')
    jira_token = os.getenv('JIRA_API_TOKEN')
    
    if not all([jira_url, jira_username, jira_token]):
        print("Error: Missing environment variables")
        sys.exit(1)
    
    return jira_url, jira_username, jira_token


def find_custom_field_id(jira_url: str, auth: HTTPBasicAuth, field_name: str):
    """Find custom field ID by name"""
    url = f"{jira_url}/rest/api/3/field"
    headers = {"Accept": "application/json"}
    
    response = requests.get(url, headers=headers, auth=auth)
    response.raise_for_status()
    
    fields = response.json()
    
    for field in fields:
        if field.get('name', '').lower() == field_name.lower():
            return field['id']
    
    return None


def search_issues(jira_url: str, auth: HTTPBasicAuth, jql: str, fields: list, max_results: int = 1000) -> Dict[str, Any]:
    """Search Jira issues using API v3"""
    url = f"{jira_url}/rest/api/3/search/jql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "jql": jql,
        "fields": fields,
        "maxResults": max_results
    }
    
    response = requests.post(url, headers=headers, auth=auth, json=payload)
    response.raise_for_status()
    
    return response.json()


def export_issues_by_version(project_key: str, fix_version: str, release_announce_field: str = None, output_file: str = None) -> Dict[str, Any]:
    """
    Export Jira issues grouped by Release announce type
    
    Args:
        project_key: Jira project key (e.g., 'PP')
        fix_version: Fix version name (e.g., '43.68.5')
        release_announce_field: Custom field ID or name (e.g., 'customfield_10050' or 'Release announce type')
        output_file: Optional output file path
    
    Returns:
        Dictionary with issues grouped by Release announce type
    """
    jira_url, username, token = get_jira_credentials()
    auth = HTTPBasicAuth(username, token)
    
    # Find custom field ID if name was provided
    custom_field_id = release_announce_field
    
    if release_announce_field and not release_announce_field.startswith('customfield_'):
        print(f"Looking up field ID for '{release_announce_field}'...")
        custom_field_id = find_custom_field_id(jira_url, auth, release_announce_field)
        
        if custom_field_id:
            print(f"Found field ID: {custom_field_id}")
        else:
            print(f"⚠️  Could not find field '{release_announce_field}'")
            print("Will try to auto-detect from first issue...")
    
    # Build JQL query
    jql = f'project = {project_key} AND fixVersion = "{fix_version}" ORDER BY key ASC'
    
    print(f"\nSearching for issues with JQL: {jql}")
    print(f"Using API endpoint: {jira_url}/rest/api/3/search/jql")
    
    # Fields to fetch
    fields_to_fetch = ["key", "summary", "components", "issuetype"]
    if custom_field_id:
        fields_to_fetch.append(custom_field_id)
    else:
        # Fetch all fields to find the right one
        fields_to_fetch = "*all"
    
    # Search issues
    try:
        result = search_issues(jira_url, auth, jql, fields_to_fetch)
        issues = result.get('issues', [])
        
        print(f"Found {len(issues)} issues (Total: {result.get('total', 0)})")
        
        if len(issues) == 0:
            print("\n❌ No issues found")
            sys.exit(1)
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Auto-detect Release announce type field if not provided
    if not custom_field_id:
        print("\n🔍 Auto-detecting 'Release announce type' field...")
        first_issue_fields = issues[0]['fields']
        
        for field_id, value in first_issue_fields.items():
            if field_id.startswith('customfield_'):
                # Get all fields to find name
                all_fields_url = f"{jira_url}/rest/api/3/field"
                all_fields_resp = requests.get(all_fields_url, headers={"Accept": "application/json"}, auth=auth)
                all_fields = all_fields_resp.json()
                
                for field_def in all_fields:
                    if field_def['id'] == field_id:
                        field_name = field_def.get('name', '').lower()
                        if 'release' in field_name and 'announce' in field_name:
                            custom_field_id = field_id
                            print(f"✅ Found field: {field_def['name']} ({field_id})")
                            break
                
                if custom_field_id:
                    break
        
        if not custom_field_id:
            print("⚠️  Could not auto-detect 'Release announce type' field")
            print("Falling back to grouping by issue type")
    
    # Group issues by Release announce type
    grouped_data = {}
    all_components = set()
    ungrouped_count = 0
    
    for issue in issues:
        # Extract components
        components = [comp['name'] for comp in issue['fields'].get('components', [])]
        all_components.update(components)
        
        # Get Release announce type value
        group_name = "Other"
        
        if custom_field_id and custom_field_id in issue['fields']:
            announce_type = issue['fields'][custom_field_id]
            
            if announce_type:
                # Handle different field types
                if isinstance(announce_type, dict):
                    group_name = announce_type.get('value', announce_type.get('name', 'Other'))
                elif isinstance(announce_type, list) and len(announce_type) > 0:
                    if isinstance(announce_type[0], dict):
                        group_name = announce_type[0].get('value', announce_type[0].get('name', 'Other'))
                    else:
                        group_name = str(announce_type[0])
                else:
                    group_name = str(announce_type)
            else:
                ungrouped_count += 1
        else:
            # Fallback to issue type if field not found
            issue_type = issue['fields']['issuetype']['name']
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
    
    if ungrouped_count > 0:
        print(f"\n⚠️  {ungrouped_count} issues without Release announce type assigned")
    
    # Create final export structure
    export_data = grouped_data.copy()
    export_data['components'] = sorted(list(all_components))
    
    # Set default output file name if not provided
    if not output_file:
        safe_version = fix_version.replace('.', '_').replace(' ', '_')
        output_file = f"release_notes_{safe_version}.json"
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    total_issues = sum(len(issues) for key, issues in export_data.items() if key != 'components')
    print(f"\n✅ Exported {total_issues} issues to {output_file}")
    
    return export_data


def print_summary(export_data: Dict[str, Any]):
    """Print a brief summary of exported issues"""
    print(f"\n{'='*60}")
    print(f"RELEASE NOTES SUMMARY")
    print(f"{'='*60}")
    
    # Count total issues
    total_issues = sum(len(issues) for key, issues in export_data.items() if key != 'components')
    print(f"Total issues: {total_issues}\n")
    
    # Print issues by release announce type
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
        print("Usage: python jira_export_by_announce_type.py <PROJECT_KEY> <VERSION> [FIELD_ID_OR_NAME] [output_file.json]")
        print("\nExamples:")
        print("  # Auto-detect field:")
        print("  python jira_export_by_announce_type.py PP 43.68.5")
        print("")
        print("  # Specify field by name:")
        print("  python jira_export_by_announce_type.py PP 43.68.5 'Release announce type'")
        print("")
        print("  # Specify field by ID:")
        print("  python jira_export_by_announce_type.py PP 43.68.5 customfield_10050")
        print("")
        print("  # With custom output file:")
        print("  python jira_export_by_announce_type.py PP 43.68.5 'Release announce type' my_notes.json")
        print("\nTip: Run find_custom_field.py first to find the exact field ID")
        sys.exit(1)
    
    project = sys.argv[1]
    version = sys.argv[2]
    
    field_id_or_name = None
    output = None
    
    if len(sys.argv) > 3:
        field_id_or_name = sys.argv[3]
    
    if len(sys.argv) > 4:
        output = sys.argv[4]
    
    try:
        issues = export_issues_by_version(project, version, field_id_or_name, output)
        print_summary(issues)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
