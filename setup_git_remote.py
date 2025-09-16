#!/usr/bin/env python3
"""
Script to help set up Git remote repository for IsoFlicker project
"""

import os
import subprocess
import sys

def run_command(command):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def check_git_repo():
    """Check if we're in a git repository"""
    code, _, _ = run_command("git rev-parse --git-dir")
    return code == 0

def get_remote_url():
    """Get the remote URL if it exists"""
    code, stdout, _ = run_command("git remote get-url origin")
    if code == 0:
        return stdout.strip()
    return None

def add_remote(url):
    """Add a remote origin"""
    code, stdout, stderr = run_command(f"git remote add origin {url}")
    if code != 0:
        print(f"Error adding remote: {stderr}")
        return False
    return True

def set_upstream(branch="main"):
    """Set upstream tracking"""
    code, stdout, stderr = run_command(f"git branch --set-upstream-to=origin/{branch} {branch}")
    if code != 0:
        print(f"Warning: Could not set upstream tracking: {stderr}")
        return False
    return True

def main():
    print("IsoFlicker Git Remote Setup Script")
    print("==================================")
    
    # Check if we're in a git repository
    if not check_git_repo():
        print("Error: Not in a git repository. Please run 'git init' first.")
        return 1
    
    # Check if remote already exists
    remote_url = get_remote_url()
    if remote_url:
        print(f"Remote already configured: {remote_url}")
        response = input("Do you want to change it? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing remote configuration.")
            return 0
    
    # Get remote URL from user
    print("\nPlease provide your remote repository URL.")
    print("Examples:")
    print("  GitHub: https://github.com/username/repository.git")
    print("  GitLab: https://gitlab.com/username/repository.git")
    print("  Bitbucket: https://bitbucket.org/username/repository.git")
    
    remote_url = input("\nEnter remote URL: ").strip()
    
    if not remote_url:
        print("No URL provided. Exiting.")
        return 1
    
    # Add remote
    print(f"Adding remote origin: {remote_url}")
    if not add_remote(remote_url):
        return 1
    
    # Set upstream tracking
    branch = "main"  # Default to main
    code, stdout, _ = run_command("git branch --show-current")
    if code == 0 and stdout.strip():
        branch = stdout.strip()
    
    print(f"Setting upstream tracking for branch '{branch}'")
    set_upstream(branch)
    
    print("\nRemote setup complete!")
    print("You can now use 'git pull' and 'git push' commands.")
    print("\nTo verify:")
    print("  git remote -v")
    print("  git pull")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())