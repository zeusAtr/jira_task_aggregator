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


def list_all_projects(jira_url: str, auth: HTTPBasicAuth):
    """List all available projects"""
    url = f"{jira_url}/rest/api/3/project"
    headers = {"Accept": "application/json"}
    
    response = requests.get(url, headers=headers, auth=auth)
    response.raise_for_status()
    
    return response.json()


def search_by_version_only(jira_url: str, auth: HTTPBasicAuth, version_name: str):
    """Search issues by version without specifying project"""
    jql = f'fixVersion = "{version_name}"'
    
    url = f"{jira_url}/rest/api/3/search/jql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "jql": jql,
        "fields": ["key", "summary", "project"],
        "maxResults": 100
    }
    
    response = requests.post(url, headers=headers, auth=auth, json=payload)
    response.raise_for_status()
    
    return response.json()


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python debug_jira_version.py --list-projects")
        print("  python debug_jira_version.py --search-version <VERSION>")
        print("  python debug_jira_version.py <PROJECT_KEY> [VERSION_SEARCH]")
        print("\nExamples:")
        print("  python debug_jira_version.py --list-projects")
        print("  python debug_jira_version.py --search-version 43.68.5")
        print("  python debug_jira_version.py PP 43.68")
        print("  python debug_jira_version.py PP")
        sys.exit(1)
    
    jira_url, username, token = get_jira_credentials()
    auth = HTTPBasicAuth(username, token)
    
    # Handle --list-projects flag
    if sys.argv[1] == "--list-projects":
        print("📋 Fetching all projects...")
        print(f"{'='*70}\n")
        
        try:
            projects = list_all_projects(jira_url, auth)
            
            if not projects:
                print("❌ No projects found")
                return
            
            print(f"✅ Found {len(projects)} projects\n")
            print(f"{'KEY':<15} {'NAME':<40} {'TYPE':<15}")
            print(f"{'-'*15} {'-'*40} {'-'*15}")
            
            for project in sorted(projects, key=lambda x: x['key']):
                key = project.get('key', 'N/A')
                name = project.get('name', 'N/A')
                project_type = project.get('projectTypeKey', 'N/A')
                
                if len(name) > 37:
                    name = name[:37] + "..."
                
                print(f"{key:<15} {name:<40} {project_type:<15}")
            
            print(f"\n{'='*70}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
        
        return
    
    # Handle --search-version flag
    if sys.argv[1] == "--search-version":
        if len(sys.argv) < 3:
            print("❌ Error: Please provide version name")
            print("Usage: python debug_jira_version.py --search-version <VERSION>")
            sys.exit(1)
        
        version_name = sys.argv[2]
        print(f"🔍 Searching for version: {version_name}")
        print(f"{'='*70}\n")
        
        try:
            result = search_by_version_only(jira_url, auth, version_name)
            total = result.get('total', 0)
            issues = result.get('issues', [])
            
            if total == 0:
                print(f"❌ No issues found with fixVersion = \"{version_name}\"")
                print("\nTips:")
                print("  - Check if the version name is exactly correct")
                print("  - Try using --list-projects to see all projects")
                print("  - Try searching for part of the version name")
                return
            
            print(f"✅ Found {total} issues with this version\n")
            
            # Group by project
            projects_found = {}
            for issue in issues:
                project_key = issue['fields']['project']['key']
                project_name = issue['fields']['project']['name']
                
                if project_key not in projects_found:
                    projects_found[project_key] = {
                        'name': project_name,
                        'issues': []
                    }
                
                projects_found[project_key]['issues'].append(issue['key'])
            
            print(f"{'PROJECT':<15} {'PROJECT NAME':<30} {'ISSUES':<10}")
            print(f"{'-'*15} {'-'*30} {'-'*10}")
            
            for proj_key, proj_data in sorted(projects_found.items()):
                name = proj_data['name']
                count = len(proj_data['issues'])
                
                if len(name) > 27:
                    name = name[:27] + "..."
                
                print(f"{proj_key:<15} {name:<30} {count:<10}")
            
            print(f"\n{'='*70}")
            print("💡 To export release notes for a specific project, use:")
            first_project = list(projects_found.keys())[0]
            print(f"   python jira_export_v3_fixed.py {first_project} \"{version_name}\"")
            print(f"{'='*70}")
            
            # Show some example issues
            if issues:
                print(f"\n📝 Example issues (showing first 10):")
                for issue in issues[:10]:
                    key = issue['key']
                    summary = issue['fields']['summary']
                    if len(summary) > 50:
                        summary = summary[:50] + "..."
                    print(f"  {key} - {summary}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
        
        return
    
    # Original functionality - project-specific search
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
