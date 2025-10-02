#!/usr/bin/env python3
"""
Test different JQL queries to find issues with specific version
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
        sys.exit(1)
    
    return jira_url, jira_username, jira_token


def search_jql(jira_url: str, auth: HTTPBasicAuth, jql: str):
    """Search using JQL"""
    url = f"{jira_url}/rest/api/3/search/jql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "jql": jql,
        "maxResults": 10,
        "fields": ["key", "summary", "fixVersions", "project"]
    }
    
    response = requests.post(url, headers=headers, auth=auth, json=payload)
    return response


def main():
    jira_url, username, token = get_jira_credentials()
    auth = HTTPBasicAuth(username, token)
    
    project = "PP"
    version_name = "43.68.5"
    version_id = "21261"  # From your output
    
    print("="*80)
    print(f"🧪 Testing JQL queries for {project} / {version_name}")
    print("="*80)
    
    # Test different JQL variations
    queries = [
        # Using version name
        f'project = {project} AND fixVersion = "{version_name}"',
        f'project = "{project}" AND fixVersion = "{version_name}"',
        f'project = {project} AND "Fix Version/s" = "{version_name}"',
        f'fixVersion = "{version_name}"',
        
        # Using version ID
        f'project = {project} AND fixVersion = {version_id}',
        f'fixVersion = {version_id}',
        
        # Alternative fields
        f'project = {project} AND affectedVersion = "{version_name}"',
        
        # Just project to see if any issues exist
        f'project = {project}',
        
        # Check issues updated recently in this project
        f'project = {project} AND updated >= -30d',
    ]
    
    for i, jql in enumerate(queries, 1):
        print(f"\n{i}. JQL: {jql}")
        
        try:
            response = search_jql(jira_url, auth, jql)
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                issues = data.get('issues', [])
                
                if total > 0:
                    print(f"   ✅ Found {total} issues!")
                    
                    # Show first 5 issues
                    print(f"\n   📝 First {min(5, len(issues))} issues:")
                    for issue in issues[:5]:
                        key = issue['key']
                        summary = issue['fields'].get('summary', 'N/A')[:60]
                        
                        # Show fixVersions
                        fix_versions = issue['fields'].get('fixVersions', [])
                        versions_str = ", ".join([v['name'] for v in fix_versions])
                        
                        print(f"      {key} - {summary}")
                        if versions_str:
                            print(f"         Fix Versions: {versions_str}")
                else:
                    print(f"   ⚠️  Found 0 issues")
                    
            else:
                print(f"   ❌ Error {response.status_code}")
                print(f"      {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n" + "="*80)
    print("💡 ANALYSIS")
    print("="*80)
    print("""
If query #8 (project = PP) finds issues but version-specific queries don't:
  → The version exists but no issues are assigned to it

If query #8 finds 0 issues:
  → Check if you have access to project PP
  → The project might be archived or you don't have permissions

If queries with version ID work but version name doesn't:
  → Use the version ID in your export script
    """)


if __name__ == '__main__':
    main()
