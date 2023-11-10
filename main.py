import os
from enum import Enum
from typing import Optional

import requests


owner = os.environ.get('OWNER')
repo = os.environ.get('REPO')
pr_number = os.environ.get('PR_NUMBER')
github_token = os.environ.get('GITHUB_TOKEN')
llama_url = os.environ.get('LLAMA_URL')
repo_name = repo


class Category(Enum):
    BLUE = 'BLUE'
    RED = 'RED'
    BLACK = 'BLACK'


def get_diff(repo_name, pr, access_token):
    # The GitHub API URL for the pull request diff
    url = f'https://api.github.com/repos/{repo_name}/pulls/{pr}'

    # Set up the headers to get the diff format and to authenticate with your token
    headers = get_auth_header(access_token)

    # Make the GET request to the GitHub API
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        diff = response.text
        return diff
    else:
        print('Failed to retrieve diff:', response.status_code)


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


def query_llama(prompt: str) -> str:
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
        'temperature': 0.0,
    }

    try:
        # Make the POST request to the llama API
        response = requests.post(url, headers=headers, json=data)

        # Check if the request was successful
        if response.status_code == 200:
            # The response is a JSON object with the generated text under the 'text' key
            llama_text = response.json()['content']
            return llama_text
        else:
            return f'Failed to retrieve llama text: POST {response.status_code} {url}: {response.text}'
    except Exception as e:
        return f'Failed to retrieve llama text: {e}'


def query_and_parse_llama(prompt) -> (Optional[Category], str):
    llama_text = query_llama(prompt)
    # Find the first line with either 'blue', 'red' or 'black' in it
    category = None
    comment = None
    for i, line in enumerate(llama_text.split('\n')):
        if Category.BLUE.value in line or Category.RED.value in line or Category.BLACK.value in line.upper():
            category = Category(line.upper())
            comment = '\n'.join(llama_text.split('\n')[i+1:])
            break
    if not category:
        return None, llama_text
    return Category(category), comment


def create_label_if_not_exists(repo_name, label_name, label_color, access_token):
    headers = get_auth_header(access_token)

    # Check if the label already exists
    labels_url = f"https://api.github.com/repos/{repo_name}/labels"
    response = requests.get(labels_url, headers=headers)

    if response.status_code == 200:
        labels = response.json()
        label_names = [label["name"] for label in labels]

        if label_name not in label_names:
            # Create the label
            if label_name == "BLUE":
                description = "This PR is simple and straightforward."
            elif label_name == "RED":
                description = "This PR is complex and may require more time to review."
            elif label_name == "BLACK":
                description = "This PR has critical implications and must be reviewed by a senior engineer."
            else:
                description = None

            data = {
                "name": label_name,
                "color": label_color,
                "description": description
            }
            create_response = requests.post(labels_url, json=data, headers=headers)

            if create_response.status_code == 201:
                print(f"Label '{label_name}' created successfully.")
            else:
                print(f"Failed to create label '{label_name}': {create_response.content}")
        else:
            pass
    else:
        print(f"Failed to retrieve labels: {response.content}", labels_url)


def add_label_to_pr(repo, pr, label, access_token):
    headers = get_auth_header(access_token)

    # GitHub API URL for issue labels (PRs are considered issues in the API)
    labels_url = f"https://api.github.com/repos/{repo}/issues/{pr}/labels"

    # Data to add the label
    data = {
        "labels": [label]
    }

    # Make the POST request to add the label to the PR
    response = requests.post(labels_url, json=data, headers=headers)

    if response.status_code == 200:
        print(f"Label '{label}' added to PR #{pr_number} successfully.")
    else:
        print(f"Failed to add label '{label}' to PR #{pr_number}: {response.content}", labels_url)


def get_auth_header(access_token):
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
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


# Define labels and their respective colors
labels = {
    "BLUE": "2A3EDD",
    "RED": "DD2A2A",
    "BLACK": "000000"
}

# Create each label if it does not exist
for label, color in labels.items():
    create_label_if_not_exists(repo_name, label, color, github_token)

repo_desc = get_repo_desc(repo_name, github_token)
diff = get_diff(repo_name, pr_number, github_token)
rules = get_rules(repo_name, github_token)
pr_title, pr_description = get_pr_desc(repo_name, pr_number, github_token)

user_prompt = f"""
--- {repo} ---
{repo_desc}

Rules: {rules}

Diff:
{diff}
"""

with open("system_prompt.txt", "r") as f:
    system_prompt = f.read()

full_prompt = f"""### System Prompt
{system_prompt}

### User Message
{user_prompt}

### Assistant
"""

category, comment = query_and_parse_llama(full_prompt)

if category:
    print(f"Category: {category}")
    add_label_to_pr(repo_name, pr_number, category.value, github_token)
    print(f"Comment: {comment}")
    add_comment_to_pr(repo_name, pr_number, comment, github_token)
else:
    print(f"Could not find category in response: {comment}")
    add_comment_to_pr(repo_name, pr_number, comment, github_token)
