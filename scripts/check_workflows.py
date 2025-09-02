#!/usr/bin/env python3
"""
GitHub Actions workflow monitor for checking build and test status
without needing local Docker installation.
"""

import requests
import time
import sys
import os
from typing import Dict, Any, List
import json


def get_github_workflows(owner: str, repo: str, token: str = None) -> List[Dict[str, Any]]:
    """Get recent workflow runs from GitHub API."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    params = {"per_page": 10, "status": "all"}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("workflow_runs", [])
    except Exception as e:
        print(f"❌ Error fetching workflows: {e}")
        return []


def get_workflow_jobs(owner: str, repo: str, run_id: int, token: str = None) -> List[Dict[str, Any]]:
    """Get jobs for a specific workflow run."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get("jobs", [])
    except Exception as e:
        print(f"❌ Error fetching workflow jobs: {e}")
        return []


def format_duration(start_time: str, end_time: str = None) -> str:
    """Format workflow duration."""
    try:
        from datetime import datetime
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        
        if end_time:
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            end = datetime.now().replace(tzinfo=start.tzinfo)
        
        duration = end - start
        minutes, seconds = divmod(duration.total_seconds(), 60)
        return f"{int(minutes)}m {int(seconds)}s"
    except:
        return "Unknown"


def monitor_workflows(owner: str, repo: str, token: str = None):
    """Monitor GitHub Actions workflows."""
    print(f"🔍 Monitoring GitHub Actions for {owner}/{repo}")
    print("=" * 60)
    
    workflows = get_github_workflows(owner, repo, token)
    
    if not workflows:
        print("No recent workflows found.")
        return
    
    # Show the most recent 5 workflows
    for i, workflow in enumerate(workflows[:5]):
        run_id = workflow["id"]
        name = workflow["name"]
        status = workflow["status"]
        conclusion = workflow.get("conclusion", "")
        created_at = workflow["created_at"]
        updated_at = workflow.get("updated_at", created_at)
        branch = workflow["head_branch"]
        commit_sha = workflow["head_sha"][:8]
        
        # Status icon
        if status == "completed":
            if conclusion == "success":
                icon = "✅"
            elif conclusion == "failure":
                icon = "❌"
            elif conclusion == "cancelled":
                icon = "⚪"
            else:
                icon = "⚠️"
        elif status == "in_progress":
            icon = "🔄"
        else:
            icon = "⏳"
        
        duration = format_duration(created_at, updated_at if status == "completed" else None)
        
        print(f"\n{i+1}. {icon} {name}")
        print(f"   Status: {status} {f'({conclusion})' if conclusion else ''}")
        print(f"   Branch: {branch} ({commit_sha})")
        print(f"   Duration: {duration}")
        print(f"   URL: https://github.com/{owner}/{repo}/actions/runs/{run_id}")
        
        # If this is the most recent workflow, show job details
        if i == 0:
            jobs = get_workflow_jobs(owner, repo, run_id, token)
            if jobs:
                print(f"   Jobs:")
                for job in jobs:
                    job_status = job["status"]
                    job_conclusion = job.get("conclusion", "")
                    job_name = job["name"]
                    
                    if job_status == "completed":
                        if job_conclusion == "success":
                            job_icon = "✅"
                        elif job_conclusion == "failure":
                            job_icon = "❌"
                        else:
                            job_icon = "⚠️"
                    elif job_status == "in_progress":
                        job_icon = "🔄"
                    else:
                        job_icon = "⏳"
                    
                    job_duration = format_duration(job["started_at"], job.get("completed_at")) if job.get("started_at") else "Not started"
                    print(f"     {job_icon} {job_name} - {job_duration}")


def main():
    """Main function."""
    # Get repository info from git remote
    try:
        import subprocess
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"], 
            capture_output=True, 
            text=True, 
            cwd="c:/dev/iptv-checker"
        )
        
        if result.returncode == 0:
            remote_url = result.stdout.strip()
            # Parse GitHub URL to get owner/repo
            if "github.com" in remote_url:
                # Handle both SSH and HTTPS formats
                if remote_url.startswith("git@github.com:"):
                    repo_part = remote_url.split("git@github.com:")[1]
                elif remote_url.startswith("https://github.com/"):
                    repo_part = remote_url.split("https://github.com/")[1]
                else:
                    raise ValueError("Unknown GitHub URL format")
                
                repo_part = repo_part.rstrip(".git")
                owner, repo = repo_part.split("/", 1)
                
                print(f"📦 Repository: {owner}/{repo}")
                
                # Check for GitHub token in environment
                token = os.environ.get("GITHUB_TOKEN")
                if not token:
                    print("💡 For detailed job information, set GITHUB_TOKEN environment variable")
                
                monitor_workflows(owner, repo, token)
            else:
                print("❌ Not a GitHub repository")
        else:
            print("❌ Could not determine repository from git remote")
    except Exception as e:
        print(f"❌ Error determining repository: {e}")
        print("\nUsage: python check_workflows.py")
        print("Or set repository manually in the script")


if __name__ == "__main__":
    main()
