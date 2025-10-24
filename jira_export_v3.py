#!/usr/bin/env python3
"""
Jira Release Notes Exporter (API v3)
Exports issues by fixVersion to JSON format using Jira REST API v3
Uses the correct /rest/api/3/search/jql endpoint
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
        print("Required: JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN")
        sys.exit(1)
    
    return jira_url, jira_username, jira_token


def search_issues(jira_url: str, auth: HTTPBasicAuth, jql: str, fields: list, max_results: int = 1000) -> Dict[str, Any]:
    """
    Search Jira issues using API v3 with the correct /rest/api/3/search/jql endpoint
    
    Args:
        jira_url: Jira instance URL
        auth: HTTPBasicAuth object
        jql: JQL query string
        fields: List of fields
        max_results: Maximum number of results
    
    Returns:
        Dictionary with search results
    """
    # Use the correct API v3 endpoint: /rest/api/3/search/jql
    url = f"{jira_url}/rest/api/3/search/jql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Use POST instead of GET for better JQL support
    payload = {
        "jql": jql,
        "fields": fields,
        "maxResults": max_results
    }
    
    response = requests.post(url, headers=headers, auth=auth, json=payload)
    response.raise_for_status()
    
    return response.json()


def parse_adf_to_text(adf_content: Dict[str, Any]) -> str:
    """
    Parse Atlassian Document Format (ADF) to plain text

    Args:
        adf_content: ADF document structure

    Returns:
        Plain text extracted from ADF
    """
    if not adf_content or not isinstance(adf_content, dict):
        return ""

    text_parts = []

    def extract_text(node):
        if isinstance(node, dict):
            # If it's a text node, extract the text
            if node.get('type') == 'text':
                text_parts.append(node.get('text', ''))

            # Recursively process content
            if 'content' in node:
                for child in node['content']:
                    extract_text(child)
        elif isinstance(node, list):
            for item in node:
                extract_text(item)

    extract_text(adf_content)
    return ' '.join(text_parts).strip()


def get_service_group(component_name: str) -> str:
    """
    Determine service group based on component name prefix

    Args:
        component_name: Component/service name

    Returns:
        Group name: 'GP', 'Jackpot system', 'SPE system', or 'Replay system'
    """
    if component_name.startswith('jackpot-'):
        return 'Jackpot system'
    elif component_name.startswith('spe-'):
        return 'SPE system'
    elif component_name.startswith('replay-'):
        return 'Replay system'
    else:
        return 'GP'


def export_issues_by_version(project_key: str, fix_version: str, output_file: str = None) -> Dict[str, Any]:
    """
    Export Jira issues by fixVersion to JSON grouped by Release announce type
    
    Args:
        project_key: Jira project key (e.g., 'PROJ')
        fix_version: Fix version name (e.g., '1.0.0')
        output_file: Optional output file path (default: release_notes_{version}.json)
    
    Returns:
        Dictionary with issues grouped by Release announce type and list of components
    """
    jira_url, username, token = get_jira_credentials()
    auth = HTTPBasicAuth(username, token)
    
    # JQL query to find issues
    jql = f'project = {project_key} AND fixVersion = "{fix_version}" ORDER BY key ASC'
    
    print(f"Searching for issues with JQL: {jql}")
    print(f"Using API endpoint: {jira_url}/rest/api/3/search/jql")
    
    # Search issues with specific fields including Release announce type (customfield_11823) and Short description (customfield_14958)
    fields_to_fetch = ["key", "summary", "components", "customfield_11823", "customfield_14958"]
    
    try:
        result = search_issues(jira_url, auth, jql, fields_to_fetch)
        issues = result.get('issues', [])
        
        print(f"Found {len(issues)} issues (Total: {result.get('total', 0)})")
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Group issues by Release announce type and collect all components
    grouped_data = {}
    all_components = set()
    ungrouped_count = 0

    # Group components by service groups
    service_groups = {
        'GP': set(),
        'Jackpot system': set(),
        'SPE system': set(),
        'Replay system': set()
    }

    # Group short descriptions by release announce type
    short_descriptions_by_announce_type = {}

    for issue in issues:
        # Extract components
        components = [comp['name'] for comp in issue['fields'].get('components', [])]
        all_components.update(components)

        # Classify components by service group
        for component in components:
            group = get_service_group(component)
            service_groups[group].add(component)

        # Get Release announce type value (customfield_11823)
        announce_type_field = issue['fields'].get('customfield_11823')
        
        # Determine group name based on Release announce type
        if announce_type_field:
            # Handle different field types (single select, multi-select, etc.)
            if isinstance(announce_type_field, dict):
                group_name = announce_type_field.get('value', announce_type_field.get('name', 'Other'))
            elif isinstance(announce_type_field, list) and len(announce_type_field) > 0:
                if isinstance(announce_type_field[0], dict):
                    group_name = announce_type_field[0].get('value', announce_type_field[0].get('name', 'Other'))
                else:
                    group_name = str(announce_type_field[0])
            else:
                group_name = str(announce_type_field)
        else:
            group_name = "No announce type"
            ungrouped_count += 1
        
        # Initialize group if not exists
        if group_name not in grouped_data:
            grouped_data[group_name] = []

        # Add issue to group
        grouped_data[group_name].append(f"{issue['key']} - {issue['fields']['summary']}")

        # Get Short description (customfield_14958) and add to the same group
        short_description_raw = issue['fields'].get('customfield_14958')
        if short_description_raw:
            # Parse ADF format to plain text
            if isinstance(short_description_raw, dict):
                short_description = parse_adf_to_text(short_description_raw)
            else:
                short_description = str(short_description_raw)

            if short_description:
                # Initialize short descriptions group if not exists
                if group_name not in short_descriptions_by_announce_type:
                    short_descriptions_by_announce_type[group_name] = []

                # Add short description to the same announce type group (same format as issues)
                short_descriptions_by_announce_type[group_name].append(
                    f"{issue['key']} - {short_description}"
                )
    
    if ungrouped_count > 0:
        print(f"\n⚠️  Warning: {ungrouped_count} issues without Release announce type")
    
    # Create final export structure with service groups
    export_data = grouped_data.copy()

    # Add short descriptions by release announce type
    if short_descriptions_by_announce_type:
        export_data['short_descriptions'] = short_descriptions_by_announce_type

    # Add service groups (only non-empty ones)
    services_data = {}
    for group_name, components in service_groups.items():
        if components:
            services_data[group_name] = sorted(list(components))

    export_data['services'] = services_data
    export_data['all_components'] = sorted(list(all_components))
    
    # Set default output file name if not provided
    if not output_file:
        output_file = f"release_notes_{fix_version.replace('.', '_').replace(' ', '_')}.json"
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    total_issues = sum(len(issues) for key, issues in export_data.items()
                       if key not in ['services', 'all_components', 'short_descriptions'])
    print(f"\nExported {total_issues} issues to {output_file}")
    
    return export_data


def print_summary(export_data: Dict[str, Any]):
    """Print a brief summary of exported issues"""
    print(f"\n{'='*60}")
    print(f"RELEASE NOTES SUMMARY (Grouped by Release announce type)")
    print(f"{'='*60}")

    # Count total issues
    total_issues = sum(len(issues) for key, issues in export_data.items()
                       if key not in ['services', 'all_components', 'short_descriptions'])
    print(f"Total issues: {total_issues}\n")

    # Print issues by Release announce type
    for group_name, issues in export_data.items():
        if group_name in ['services', 'all_components', 'short_descriptions']:
            continue
        print(f"{group_name.upper()}:")
        for issue in issues:
            print(f"  - {issue}")
        print()

    # Print short descriptions by release announce type
    if 'short_descriptions' in export_data and export_data['short_descriptions']:
        print("SHORT DESCRIPTIONS (by release announce type):")
        for announce_type, descriptions in export_data['short_descriptions'].items():
            print(f"\n  {announce_type}:")
            for desc in descriptions:
                print(f"    - {desc}")

    # Print service groups
    if 'services' in export_data and export_data['services']:
        print("\nSERVICE GROUPS:")
        for service_group, components in export_data['services'].items():
            print(f"\n  {service_group}:")
            for component in components:
                print(f"    - {component}")

    print(f"\n{'='*60}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python jira_export_v3_fixed.py <PROJECT_KEY> <FIX_VERSION> [output_file.json]")
        print("\nExample: python jira_export_v3_fixed.py PROJ 1.0.0")
        print("         python jira_export_v3_fixed.py PROJ '1.0.0' my_release_notes.json")
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
