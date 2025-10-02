#!/usr/bin/env python3
"""
Debug Jira Version Finder
Helps find the correct version name in Jira
"""

import os
import sys
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


def get_project_versions(jira_url: str, auth: HTTPBasicAuth, project_key: str):
    """Get all versions for a project"""
    url = f"{jira_url}/rest/api/3/project/{project_key}/versions"
    headers = {"Accept": "application/json"}
    
    response = requests.get(url, headers=headers, auth=auth)
    response.raise_for_status()
    
    return response.json()


def test_jql_query(jira_url: str, auth: HTTPBasicAuth, jql: str):
    """Test a JQL query"""
    url = f"{jira_url}/rest/api/3/search/jql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "jql": jql,
        "fields": ["key", "summary"],
        "maxResults": 10
    }
    
    response = requests.post(url, headers=headers, auth=auth, json=payload)
    response.raise_for_status()
    
    return response.json()


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_jira_version.py <PROJECT_KEY> [VERSION_SEARCH]")
        print("\nExample: python debug_jira_version.py PP 43.68")
        print("         python debug_jira_version.py PP")
        sys.exit(1)
    
    project_key = sys.argv[1]
    version_search = sys.argv[2] if len(sys.argv) > 2 else None
    
    jira_url, username, token = get_jira_credentials()
    auth = HTTPBasicAuth(username, token)
    
    print(f"🔍 Debugging Jira project: {project_key}")
    print(f"{'='*70}\n")
    
    # Get all versions
    print("📋 Fetching all versions for project...")
    try:
        versions = get_project_versions(jira_url, auth, project_key)
        
        if not versions:
            print("❌ No versions found for this project")
            return
        
        print(f"✅ Found {len(versions)} versions\n")
        
        # Filter versions if search term provided
        if version_search:
            filtered_versions = [v for v in versions if version_search in v['name']]
            print(f"🔎 Filtering by '{version_search}': {len(filtered_versions)} matches\n")
            versions = filtered_versions
        
        # Display versions
        print(f"{'ID':<10} {'NAME':<30} {'RELEASED':<10} {'ARCHIVED':<10}")
        print(f"{'-'*10} {'-'*30} {'-'*10} {'-'*10}")
        
        for v in sorted(versions, key=lambda x: x['name'], reverse=True)[:20]:
            vid = v.get('id', 'N/A')
            name = v.get('name', 'N/A')
            released = '✓' if v.get('released', False) else ''
            archived = '✓' if v.get('archived', False) else ''
            
            if len(name) > 27:
                name = name[:27] + "..."
            
            print(f"{vid:<10} {name:<30} {released:<10} {archived:<10}")
        
        if len(versions) > 20:
            print(f"\n... and {len(versions) - 20} more versions")
        
        # Test JQL with first matching version
        if versions:
            print(f"\n{'='*70}")
            print("🧪 Testing JQL queries with version:", versions[0]['name'])
            print(f"{'='*70}\n")
            
            test_version = versions[0]['name']
            
            # Try different JQL variations
            queries = [
                f'project = {project_key} AND fixVersion = "{test_version}"',
                f'project = "{project_key}" AND fixVersion = "{test_version}"',
                f'project = {project_key} AND fixVersion = {test_version}',
                f'fixVersion = "{test_version}"',
            ]
            
            for i, jql in enumerate(queries, 1):
                print(f"Query {i}: {jql}")
                try:
                    result = test_jql_query(jira_url, auth, jql)
                    total = result.get('total', 0)
                    print(f"  ✅ Result: {total} issues found")
                    
                    if total > 0 and result.get('issues'):
                        print(f"  First issue: {result['issues'][0]['key']}")
                    print()
                    
                except Exception as e:
                    print(f"  ❌ Error: {e}\n")
            
            # Suggest correct command
            print(f"{'='*70}")
            print("💡 To export release notes, use:")
            print(f"   python jira_export_v3_fixed.py {project_key} \"{test_version}\"")
            print(f"{'='*70}")
    
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
