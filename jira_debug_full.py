#!/usr/bin/env python3
"""
Comprehensive Jira Debug Tool
Finds projects, versions, and issues using multiple methods
"""

import os
import sys
import requests
from requests.auth import HTTPBasicAuth
import json


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


def test_connection(jira_url: str, auth: HTTPBasicAuth):
    """Test Jira connection"""
    url = f"{jira_url}/rest/api/3/myself"
    headers = {"Accept": "application/json"}
    
    response = requests.get(url, headers=headers, auth=auth)
    response.raise_for_status()
    
    return response.json()


def list_all_projects(jira_url: str, auth: HTTPBasicAuth):
    """List all available projects"""
    url = f"{jira_url}/rest/api/3/project"
    headers = {"Accept": "application/json"}
    
    response = requests.get(url, headers=headers, auth=auth)
    response.raise_for_status()
    
    return response.json()


def search_issues_raw(jira_url: str, auth: HTTPBasicAuth, jql: str, max_results: int = 100):
    """Raw JQL search"""
    url = f"{jira_url}/rest/api/3/search"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": "key,summary,project,fixVersions"
    }
    
    print(f"  Trying GET method with /rest/api/3/search")
    response = requests.get(url, headers=headers, auth=auth, params=params)
    
    return response


def search_issues_jql(jira_url: str, auth: HTTPBasicAuth, jql: str, max_results: int = 100):
    """JQL search using POST"""
    url = f"{jira_url}/rest/api/3/search/jql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "jql": jql,
        "maxResults": max_results,
        "fields": ["key", "summary", "project", "fixVersions"]
    }
    
    print(f"  Trying POST method with /rest/api/3/search/jql")
    response = requests.post(url, headers=headers, auth=auth, json=payload)
    
    return response


def get_project_versions(jira_url: str, auth: HTTPBasicAuth, project_key: str):
    """Get all versions for a project"""
    url = f"{jira_url}/rest/api/3/project/{project_key}/versions"
    headers = {"Accept": "application/json"}
    
    response = requests.get(url, headers=headers, auth=auth)
    
    return response


def main():
    print("="*80)
    print("🔍 COMPREHENSIVE JIRA DEBUG TOOL")
    print("="*80)
    
    jira_url, username, token = get_jira_credentials()
    auth = HTTPBasicAuth(username, token)
    
    # Step 1: Test connection
    print("\n1️⃣ Testing Jira connection...")
    try:
        user_info = test_connection(jira_url, auth)
        print(f"   ✅ Connected as: {user_info.get('displayName', 'Unknown')} ({user_info.get('emailAddress', 'N/A')})")
        print(f"   URL: {jira_url}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        sys.exit(1)
    
    # Step 2: List all projects
    print("\n2️⃣ Fetching all accessible projects...")
    try:
        projects = list_all_projects(jira_url, auth)
        print(f"   ✅ Found {len(projects)} projects\n")
        
        if not projects:
            print("   ❌ No projects found. Check your permissions.")
            return
        
        print(f"   {'KEY':<20} {'NAME':<50}")
        print(f"   {'-'*20} {'-'*50}")
        
        for project in sorted(projects, key=lambda x: x['key'])[:30]:
            key = project.get('key', 'N/A')
            name = project.get('name', 'N/A')
            
            if len(name) > 47:
                name = name[:47] + "..."
            
            print(f"   {key:<20} {name:<50}")
        
        if len(projects) > 30:
            print(f"   ... and {len(projects) - 30} more projects")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)
    
    # Step 3: Ask user for input
    print("\n" + "="*80)
    print("3️⃣ Let's search for your version!")
    print("="*80)
    
    project_key = input("\nEnter PROJECT KEY (or press Enter to search all projects): ").strip().upper()
    version_name = input("Enter VERSION name (e.g., 43.68.5): ").strip()
    
    if not version_name:
        print("❌ Version name is required!")
        return
    
    print("\n" + "="*80)
    print(f"4️⃣ Searching for version: {version_name}")
    if project_key:
        print(f"   In project: {project_key}")
    else:
        print(f"   In all projects")
    print("="*80)
    
    # Step 4: Try different search methods
    search_methods = []
    
    if project_key:
        search_methods = [
            f'project = {project_key} AND fixVersion = "{version_name}"',
            f'project = "{project_key}" AND fixVersion = "{version_name}"',
            f'project = {project_key} AND fixVersion = {version_name}',
            f'fixVersion = "{version_name}" AND project = {project_key}',
        ]
    else:
        search_methods = [
            f'fixVersion = "{version_name}"',
            f'fixVersion = {version_name}',
        ]
    
    results = {}
    
    for i, jql in enumerate(search_methods, 1):
        print(f"\n🧪 Method {i}: {jql}")
        
        # Try GET method
        try:
            response = search_issues_raw(jira_url, auth, jql, 100)
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                issues = data.get('issues', [])
                
                print(f"  ✅ GET /search - Found {total} issues")
                
                if total > 0:
                    results[jql] = {
                        'method': 'GET /search',
                        'total': total,
                        'issues': issues
                    }
            else:
                print(f"  ❌ GET /search - Status {response.status_code}")
                print(f"     {response.text[:200]}")
        except Exception as e:
            print(f"  ❌ GET /search - Error: {e}")
        
        # Try POST method
        try:
            response = search_issues_jql(jira_url, auth, jql, 100)
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                issues = data.get('issues', [])
                
                print(f"  ✅ POST /search/jql - Found {total} issues")
                
                if total > 0 and jql not in results:
                    results[jql] = {
                        'method': 'POST /search/jql',
                        'total': total,
                        'issues': issues
                    }
            else:
                print(f"  ❌ POST /search/jql - Status {response.status_code}")
                print(f"     {response.text[:200]}")
        except Exception as e:
            print(f"  ❌ POST /search/jql - Error: {e}")
    
    # Step 5: Check versions in project
    if project_key:
        print(f"\n" + "="*80)
        print(f"5️⃣ Checking all versions in project {project_key}")
        print("="*80)
        
        try:
            response = get_project_versions(jira_url, auth, project_key)
            
            if response.status_code == 200:
                versions = response.json()
                print(f"\n✅ Found {len(versions)} versions in project {project_key}")
                
                # Look for similar versions
                matching = [v for v in versions if version_name.lower() in v['name'].lower()]
                
                if matching:
                    print(f"\n📋 Versions containing '{version_name}':")
                    for v in matching[:20]:
                        name = v.get('name', 'N/A')
                        vid = v.get('id', 'N/A')
                        released = '✓ Released' if v.get('released', False) else ''
                        print(f"   - {name:<30} (ID: {vid}) {released}")
                else:
                    print(f"\n⚠️  No versions found containing '{version_name}'")
                    print(f"\n📋 All versions in {project_key} (showing first 20):")
                    for v in sorted(versions, key=lambda x: x['name'], reverse=True)[:20]:
                        name = v.get('name', 'N/A')
                        print(f"   - {name}")
            else:
                print(f"❌ Error getting versions: {response.status_code}")
                print(f"   {response.text[:200]}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Step 6: Show results
    print("\n" + "="*80)
    print("6️⃣ SUMMARY")
    print("="*80)
    
    if not results:
        print("\n❌ No issues found with any search method")
        print("\n💡 Suggestions:")
        print("   1. Double-check the version name spelling")
        print("   2. Check if the version exists in Project Settings → Versions")
        print("   3. Verify the version is set as 'Fix Version' in the issues")
        print("   4. Try searching in Jira UI first to confirm the version exists")
    else:
        print(f"\n✅ Found issues using {len(results)} search method(s)!")
        
        for jql, data in results.items():
            print(f"\n🎯 Working JQL: {jql}")
            print(f"   Method: {data['method']}")
            print(f"   Total issues: {data['total']}")
            
            if data['issues']:
                print(f"\n   📝 Sample issues (first 5):")
                for issue in data['issues'][:5]:
                    key = issue['key']
                    summary = issue['fields'].get('summary', 'N/A')
                    if len(summary) > 60:
                        summary = summary[:60] + "..."
                    print(f"      {key} - {summary}")
                
                # Extract project from first issue
                first_issue = data['issues'][0]
                found_project = first_issue['fields']['project']['key']
                
                print(f"\n   💡 To export release notes:")
                print(f"      python jira_export_v3_fixed.py {found_project} \"{version_name}\"")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    main()
