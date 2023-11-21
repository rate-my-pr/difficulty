import os
import time
from enum import Enum
from typing import Optional

import requests


owner = os.environ.get('OWNER')
repo = os.environ.get('REPO')
pr_number = os.environ.get('PR_NUMBER')
github_token = os.environ.get('GITHUB_TOKEN')
llama_url = os.environ.get('LLAMA_URL')
dry_run = os.environ.get('DRY_RUN', False)
# strip trailing slash
llama_url = llama_url[:-1] if llama_url.endswith('/') else llama_url

repo_name = repo


class Category(Enum):
    BLUE = 'BLUE'
    RED = 'RED'
    BLACK = 'BLACK'


def get_diff(repo_name, pr, access_token):
    # The GitHub API URL for the pull request diff
    url = f'https://api.github.com/repos/{repo_name}/pulls/{pr}'

    # Set up the headers to get the diff format and to authenticate with your token
    headers = get_auth_header(access_token, accept_header="application/vnd.github.v3.diff")

    # Make the GET request to the GitHub API
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        diff = response.text
        return diff
    else:
        print('Failed to retrieve diff:', response.status_code)


def get_commit_messages(repo_name, pr, access_token) -> list:
    # The GitHub API URL for the pull request commits
    url = f'https://api.github.com/repos/{repo_name}/pulls/{pr}/commits'

    # Set up the headers to authenticate with your token
    headers = get_auth_header(access_token)

    # Make the GET request to the GitHub API
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        commits = response.json()
        commit_messages = [commit['commit']['message'] for commit in commits]
        return commit_messages
    else:
        print('Failed to retrieve commit messages:', response.status_code)


def get_repo_desc(repo_name, access_token):
    # The GitHub API URL for the repository details
    url = f'https://api.github.com/repos/{repo_name}'

    # The headers for authorization (if needed)
    headers = get_auth_header(access_token)

    # Make the GET request to the GitHub API
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        repo_data = response.json()
        # The description of the repository is under the 'description' key
        description = repo_data.get('description', 'No description provided.')
        return description
    else:
        print('Failed to retrieve repository information:', response.status_code, url)


def get_rules(repo_name, access_token, rules_override=None):
    if rules_override:
        return rules_override
    # The GitHub API URL for the file contents
    url = f'https://api.github.com/repos/{repo_name}/contents/code-rev-rules.txt'

    # Set up the headers for authorization (if needed) and to accept the content in JSON format
    headers = get_auth_header(access_token)

    # Make the GET request to the GitHub API
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        file_content = response.text  # You get the file content directly due to 'application/vnd.github.v3.raw' header
        return file_content
    else:
        return "No additional rules provided"


def get_pr_desc(repo_name, pr, access_token):
    # The GitHub API URL for the pull request
    url = f'https://api.github.com/repos/{repo_name}/pulls/{pr}'

    # Set up the headers for authorization (if needed)
    headers = get_auth_header(access_token)

    # Make the GET request to the GitHub API
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        pr_data = response.json()
        pr_title = pr_data.get('title', 'No title provided.')  # Get the PR title
        pr_description = pr_data.get('body', 'No description provided.')  # Get the PR description
        return pr_title, pr_description
    else:
        print('Failed to retrieve PR description:', response.status_code, url)


def query_llama(prompt: str, max_retries=3, delay=2) -> str:
    # The URL for the llama API
    url = f'{llama_url}/completion'

    # Set up the headers to accept JSON
    headers = {
        'Accept': 'application/json'
    }

    # Set up the data to send
    data = {
        'prompt': prompt,
        'stream': False,
        'temperature': 0.3,
    }

    for attempt in range(max_retries):
        try:
            # Make the POST request to the llama API
            response = requests.post(url, headers=headers, json=data)

            # Check if the request was successful
            if response.status_code == 200:
                # The response is a JSON object with the generated text under the 'content' key
                llama_text = response.json()['content']
                return llama_text
            else:
                error_message = f'Failed to retrieve llama text: POST {response.status_code} {url}: {response.text}'
                if attempt < max_retries - 1:
                    time.sleep(delay)  # Wait for some time before retrying
                else:
                    return error_message
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay)  # Wait for some time before retrying
            else:
                return f'Failed to retrieve llama text: {e}'


def get_auth_header(access_token, accept_header="application/vnd.github.v3+json"):
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": accept_header
    }
    return headers


def add_comment_to_pr(repo_name, pr, comment_body, access_token):
    """
    Add a comment to a pull request on GitHub.

    Parameters:
    repo_name (str): The full repository name (e.g., "owner/repo").
    pr_number (int): The number of the pull request to which the comment will be added.
    comment_body (str): The content of the comment to add to the pull request.
    access_token (str): Personal access token for GitHub API authentication.
    """
    headers = get_auth_header(access_token)

    # GitHub API URL for issue comments (PRs are treated as issues for comments)
    comments_url = f"https://api.github.com/repos/{repo_name}/issues/{pr}/comments"

    # Data with the comment content
    data = {
        "body": comment_body
    }

    # Make the POST request to add the comment to the PR
    response = requests.post(comments_url, json=data, headers=headers)

    if response.status_code == 201:
        print(f"Comment added to PR #{pr} successfully.")
    else:
        print(f"Failed to add comment to PR #{pr}: {response.content}", comments_url)


repo_desc = get_repo_desc(repo_name, github_token)
pr_title, pr_desc = get_pr_desc(repo_name, pr_number, github_token)
commit_messages = get_commit_messages(repo_name, pr_number, github_token)
message_list = "\n----------".join(commit_messages)

user_prompt = f"""
--- {repo} ---
{repo_desc}

--- PR #{pr_number}: {pr_title} ---
{pr_desc}

--- Commit Messages ---
{message_list}
"""

with open("system_prompt.txt", "r") as f:
    system_prompt = f.read()

full_prompt = f"""### System Prompt
{system_prompt}

### User Message
{user_prompt}

### Assistant
"""

print(f"Prompt: {full_prompt}")

comment = query_llama(full_prompt)

print(f"Comment: {comment}")

if not dry_run:
    add_comment_to_pr(repo_name, pr_number, comment, github_token)
