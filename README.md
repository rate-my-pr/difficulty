# clarity
A github workflow designed to rate commit message clarity.

Devs love to write bad commit messages. This action will analyze the commit messages of a PR and rate them on a scale of 1 to 10, where 1 is the worst and 10 is the best, in a humorous way.

## Usage

You need to have a [CodeLlama](https://huggingface.co/Phind/Phind-CodeLlama-34B-v2) model running somewhere and provide the URL to the model as a secret to the action:
```yaml
name: Commit Message Clarity Rating

permissions:
  pull-requests: write

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  rate-me:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: pr-rating-action/clarity@v1
      with:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        LLAMA_URL: ${{ secrets.LLAMA_URL }}
```
