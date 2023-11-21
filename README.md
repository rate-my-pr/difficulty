# difficulty
A GitHub workflow designed to rate and tag your PRs by complexity.

Provides a difficulty rating for PRs based on content diffs. Ratings are

- `BLUE`: Simple, low risk changes, such as documentation, comments, etc.
- `RED`: Complex, high risk changes, such as refactors, new features, etc.
- `BLACK`: Very complex, very high risk changes, such as large refactors, modifications to core functionality, etc.

The action adds a label and comment explaining the decision and important aspects of the PR.

## Usage

You need to have a [CodeLlama](https://huggingface.co/Phind/Phind-CodeLlama-34B-v2) model running somewhere and provide the URL to the model as a secret to the action:
```yaml
name: PR Difficulty Rating

permissions:
  pull-requests: write

on:
  pull_request:
    types: [opened, reopened, ready_for_review]  # only run on PRs that are ready for review

jobs:
  rate-me:
    runs-on: ubuntu-latest
    if: github.event.pull_request.draft == false  # only run on PRs that are not drafts
    steps:
    - uses: actions/checkout@v2
    - uses: pr-rating-action/difficulty@v1
      with:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        LLAMA_URL: ${{ secrets.LLAMA_URL }}
```

### Fine-tuning
You can fine-tune the prompt by adding "rules" in a `code-rev-rules.txt` of the project. These will be injected into the prompt before the diff.

A few examples:
```
If main.py is changed, then the PR is BLACK.

Python files are easier to review than C++ files.

Blue PRs are good for interns. Red PRs are good for juniors. Black PRs are good for seniors.
```