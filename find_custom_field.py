#!/usr/bin/env python3
"""
Find custom field ID for Release announce type
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


def get_all_fields(jira_url: str, auth: HTTPBasicAuth):
    """Get all Jira fields"""
    url = f"{jira_url}/rest/api/3/field"
    headers = {"Accept": "application/json"}
    
    response = requests.get(url, headers=headers, auth=auth)
    response.raise_for_status()
    
    return response.json()


def search_sample_issue(jira_url: str, auth: HTTPBasicAuth, project: str, version: str):
    """Get a sample issue to see its fields"""
    url = f"{jira_url}/rest/api/3/search/jql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "jql": f'project = {project} AND fixVersion = "{version}"',
        "fields": "*all",
        "maxResults": 1
    }
    
    response = requests.post(url, headers=headers, auth=auth, json=payload)
    
    if response.status_code == 200:
        return response.json()
    return None


def main():
    if len(sys.argv) < 3:
        print("Usage: python find_custom_field.py <PROJECT_KEY> <VERSION>")
        print("\nExample: python find_custom_field.py PP 43.68.5")
        sys.exit(1)
    
    project = sys.argv[1]
    version = sys.argv[2]
    
    jira_url, username, token = get_jira_credentials()
    auth = HTTPBasicAuth(username, token)
    
    print("="*80)
    print("🔍 Finding 'Release announce type' custom field")
    print("="*80)
    
    # Step 1: Get all fields
    print("\n1️⃣ Fetching all Jira fields...")
    try:
        all_fields = get_all_fields(jira_url, auth)
        
        # Search for fields with "release" or "announce" in name
        matching_fields = []
        for field in all_fields:
            name = field.get('name', '').lower()
            field_id = field.get('id', '')
            
            if 'release' in name or 'announce' in name:
                matching_fields.append(field)
        
        if matching_fields:
            print(f"\n✅ Found {len(matching_fields)} fields with 'release' or 'announce':\n")
            print(f"{'FIELD ID':<25} {'NAME':<40} {'TYPE':<20}")
            print(f"{'-'*25} {'-'*40} {'-'*20}")
            
            for field in matching_fields:
                field_id = field.get('id', 'N/A')
                name = field.get('name', 'N/A')
                schema = field.get('schema', {})
                field_type = schema.get('type', 'N/A')
                
                if len(name) > 37:
                    name = name[:37] + "..."
                
                print(f"{field_id:<25} {name:<40} {field_type:<20}")
        else:
            print("\n⚠️  No fields found with 'release' or 'announce' in name")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    # Step 2: Get sample issue to see actual field values
    print(f"\n2️⃣ Fetching sample issue from {project} / {version}...")
    try:
        result = search_sample_issue(jira_url, auth, project, version)
        
        if result and result.get('issues'):
            issue = result['issues'][0]
            issue_key = issue['key']
            fields = issue['fields']
            
            print(f"\n✅ Found sample issue: {issue_key}")
            print(f"\n📋 Custom fields in this issue:\n")
            
            custom_fields = []
            for field_id, value in fields.items():
                if field_id.startswith('customfield_'):
                    # Find field name
                    field_name = "Unknown"
                    for f in all_fields:
                        if f['id'] == field_id:
                            field_name = f['name']
                            break
                    
                    # Check if field name contains release/announce
                    if value is not None and ('release' in field_name.lower() or 'announce' in field_name.lower()):
                        custom_fields.append({
                            'id': field_id,
                            'name': field_name,
                            'value': value
                        })
            
            if custom_fields:
                for cf in custom_fields:
                    print(f"Field ID: {cf['id']}")
                    print(f"Name: {cf['name']}")
                    print(f"Value: {cf['value']}")
                    print()
            else:
                print("⚠️  No custom fields with 'release' or 'announce' found in this issue")
                print("\n💡 Showing ALL custom fields in this issue:")
                
                for field_id, value in sorted(fields.items()):
                    if field_id.startswith('customfield_') and value is not None:
                        field_name = "Unknown"
                        for f in all_fields:
                            if f['id'] == field_id:
                                field_name = f['name']
                                break
                        
                        # Truncate long values
                        value_str = str(value)
                        if len(value_str) > 100:
                            value_str = value_str[:100] + "..."
                        
                        print(f"\n{field_id} ({field_name}):")
                        print(f"  {value_str}")
        else:
            print("❌ No issues found. Try different project/version.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*80)
    print("💡 Once you find the field ID, update the export script")
    print("="*80)


if __name__ == '__main__':
    main()
