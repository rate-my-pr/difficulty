# pr-rating-action
A GitHub workflow designed to rate and tag your PRs by complexity.

Provides a difficulty rating for PRs based on content diffs. Ratings are

- `BLUE`: Simple, low risk changes, such as documentation, comments, etc.
- `RED`: Complex, high risk changes, such as refactors, new features, etc.
- `BLACK`: Very complex, very high risk changes, such as large refactors, modifications to core functionality, etc.

The action adds a label and comment explaining the decision and important aspects of the PR.

## Usage

You need to have a [CodeLlama](https://huggingface.co/Phind/Phind-CodeLlama-34B-v2) model running somewhere and provide the URL to the model as a secret to the action:
```yaml
name: PR Rating

on:
  pull_request:
    types: [opened, reopened, ]  # good for most use cases

jobs:
    rate:
        runs-on: ubuntu-latest
        steps:
        - uses: actions/checkout@v2
        - uses: pr-rating-action/gh-action@v1
            with:
                GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
                LLAMA_URL: ${{ secrets.LLAMA_URL }}
    ```