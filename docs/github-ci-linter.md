# **Technical Documentation: Local Linter Integration with GitHub Actions**

This documentation describes the process of implementing `gitpr --linter` as a "Quality Gate" in the development lifecycle, preventing code that violates the project's static rules from being merged into the main branch.

---

## **1. Technical Functionality**

The `gitpr --linter` command is designed to operate with semantic **exit codes**:

* **Exit Code 0:** Success. No violations found.
* **Exit Code 1:** Failure. Violations detected (blocks the GitHub workflow).

Unlike AI modes, the linter mode does not require API keys, making it ideal for ephemeral execution environments.

---

## **2. Workflow Configuration (.yml)**

Create the `.github/workflows/gitpr-linter.yml` file in your repository with the configuration below. This action will trigger on all Pull Requests targeting `main` or `develop` branches.

```yaml
name: 🛡️ GitPR Static Analysis

on:  
  pull_request:  
    branches: [ "main", "develop" ]

jobs:  
  linter-validation:  
    runs-on: ubuntu-latest  
      
    steps:  
      - name: 📥 Checkout Repository  
        uses: actions/checkout@v4  
        with:  
          # Required to allow 'git diff' against base branch  
          fetch-depth: 0 

      - name: 🐍 Setup Python Environment  
        uses: actions/setup-python@v5  
        with:  
          python-version: '3.12'

      - name: ⚙️ Install Dependencies  
        run: |  
          git clone https://github.com/natanfiuza/gitpr.git /tmp/gitpr  
          pip install google-genai python-dotenv click cryptography pyyaml

      - name: 🚨 Execute Local Linter  
        # Workflow will fail automatically if exit code is 1  
        run: python /tmp/gitpr/src/main.py --linter
```

---

## **3. Locking the Merge Button (Branch Protection)**

Simply configuring the `.yml` file does not physically prevent merging; it only indicates failure. To "lock" the merge button, follow these steps in the GitHub interface:

1. Go to **Settings** > **Branches**.  
2. Under **Branch protection rules**, click **Add rule** (or Edit on the rule for `main`).  
3. Check the option: **"Require status checks to pass before merging"**.  
4. In the search box that appears, search for: `linter-validation` (or the job name defined in your YAML).  
5. Also check **"Require branches to be up to date before merging"** to ensure the diff tested is the latest.  
6. Click **Save changes**.

---

## **4. Benefits of Implementation**

* **Zero AI Latency:** Validation is based on local Regex, taking milliseconds.  
* **Zero Cost:** Does not consume Gemini API tokens.  
* **Security:** Blocks sensitive strings (passwords, test IPs, debug logs) before human Code Review.