# pr-rating-action
A GitHub workflow designed to rate and tag your PRs by complexity.

Provides a difficulty rating for PRs based on content diffs. Ratings are

- `BLUE`: Simple, low risk changes, such as documentation, comments, etc.
- `RED`: Complex, high risk changes, such as refactors, new features, etc.
- `BLACK`: Very complex, very high risk changes, such as large refactors, modifications to core functionality, etc.

The action adds a label and comment explaining the decision and important aspects of the PR.

## Usage

```yaml
name: PR Rating

on:
  pull_request:
    types: [opened, edited, synchronize, reopened]

jobs:
    rate:
        runs-on: ubuntu-latest
        steps:
        - uses: actions/checkout@v2
        - uses: pr-rating-action/gh-action@v1
    ```