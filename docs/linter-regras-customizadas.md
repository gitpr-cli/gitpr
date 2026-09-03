# **Technical Documentation: Customizable Static Linter (--linter)**

The GitPR CLI has an ultra-fast static analysis engine that runs locally, without consuming AI quotas or requiring an internet connection. It analyzes only the **modified or added lines** in your git diff, ensuring instant feedback.

## **1. How to Run the Linter**

You can trigger the linter in three ways:

1. **Manually:** Running gitpr --linter in the terminal.
2. **Via Pre-commit Hook:** Automatically before each commit (installed via gitpr -ih).
3. **Via CI/CD:** In GitHub Actions, blocking the merge if the code returns exit code 1.

---

## **2. .gitpr.linter.yml File Structure**

The Linter rules live in the .gitpr.linter.yml file at the root of your project. The file is read on each execution and has the following YAML structure:

```YAML

rules:
  - name: "rule-identifier"
    extensions: ["js", "php", "py"] # Extensions where the rule applies
    regex: 'your-regular-expression-here'
    message: "🚨 Error message that will appear in the terminal ({file_name}, Line {line_number})"
    ignore_comments: true # Ignores if regex matches inside a comment (//, #, /*)
    ignore_paths: # Optional: Folders where this rule should NOT run
      - "vendor/*"
    require_paths: # Optional: Exclusive folders where this rule MUST run
      - "routes/*"

external_linters:
  - name: "ESLint (JavaScript/TypeScript)"
    extensions: ["js", "ts", "vue", "jsx", "tsx"]
    command: "npx eslint --format checkstyle"
```

---

## **3. Tutorial: Creating Rules with Regular Expressions (Regex)**

The GitPR engine uses Python's native Regex library (re). The secret of a good Linter rule is being restrictive enough to catch the error, but flexible enough to ignore extra whitespace.

### **Practical Example 1: Prohibiting Verbs in Routes (RESTful Standard)**

**The Problem:** In the REST standard, URLs should not contain verbs (e.g.: /api/search-users), but rather nouns and appropriate HTTP methods (GET /api/users).

See how to configure a rule in Laravel (PHP) to prevent this:

```YAML

  - name: "check-route-verbs"
    extensions: ["php"]
    require_paths:
      - "routes/*"
    regex: 'Route::[a-zA-Z]+\s*\(\s*[''"](get|get-|busca|buscar|procura|procurar|pesquisa|pesquisar|lista|listar)'
    message: "🚨 Inappropriate URI in {file_name} (Line {line_number}). Avoid verbs like 'search' or 'list' in the URL. Use RESTful standards."
    ignore_comments: true
```

#### **Dissecting the Regex above:**

To understand how to create your own, see how this one was built piece by piece:

* Route:: → Searches exactly for the Laravel Facade call.
* [a-zA-Z]+ → Captures any HTTP method that comes after (e.g.: get, post, put).
* \s*\(\s* → The \s* means "zero or more spaces". This ensures the Linter catches both Route::get(' and Route::get ( '.
* ['"] → Accepts both single and double quotes to open the URL string.
* (get|get-|busca|buscar...) → The main capture group. The pipe | works as an "OR". If any of these words right at the beginning of the URL is detected, the rule fails.

### **Practical Example 2: Blocking Forgotten Debug Logs**

**The Problem:** Developers frequently forget debug commands in the code before committing.

**Rule for PHP (dd or dump):**

```YAML

  - name: "check-php-debug"
    extensions: ["php"]
    regex: '\b(dd|dump|var_dump|print_r)\s*\('
    message: "🚨 Debug code left behind ({file_name}, Line {line_number})."
    ignore_comments: true
```

*Regex Tip:* The \b (Word Boundary) ensures the word is exact. It catches the dd() command, but ignores the word add(), avoiding false positives.

**Rule for JavaScript (console.log):**

```YAML

  - name: "check-js-console"
    extensions: ["js", "ts", "vue"]
    regex: 'console\.(log|debug|info)\s*\('
    message: "🚨 console.log usage not allowed in production ({file_name}, Line {line_number})."
    ignore_comments: true
```

*Regex Tip:* The dot \. needs a backslash (escape), because in Regex language, a standalone dot means "any character".

---

## **4. Golden Tips for Regex in the Linter**

1. **Escape special characters:** Symbols like ( ) [ ] { } . \* \+ ? ^ $ have mathematical functions in Regex. If you want to search for them in code, put a backslash before them (e.g.: \( to find an open parenthesis).
2. **Be careful with quotes in YAML:** In the .yml file, always wrap your regex with single quotes '...'. If your regex needs a single quote inside it, double it up '' or use double quotes on the outside "...".
3. **Use \s\* generously:** Never assume code formatting is perfect. Use \s\* to cover whitespace, tabs, and line breaks between commands.

---

## **5. Integration with External Linters (Bridge via Checkstyle)**

The GitPR CLI does not need to reinvent the wheel. If your project already uses tools like PHP_CodeSniffer, ESLint or Stylelint, GitPR can act as a bridge, running these tools in the background and filtering errors **only for the lines you changed in your current Pull Request**.

For this, the external linter must support report output in `checkstyle` format (universal standard in CI/CD).

### **External Linter Timeout**

Each external linter subprocess is bounded by a **120-second timeout**
(configurable via `GITPR_LINTER_TIMEOUT` in `~/.gitpr/.env`). If a linter
exceeds the bound, it is skipped — its violations are not included in the
report — instead of blocking the whole review. Invalid or non-positive values
fall back to the 120s default.

### **Quick Setup (--linter-setup)**

Instead of configuring the YAML manually, you can use our interactive wizard:
Run in the terminal:
`gitpr --linter-setup`

The wizard will show pre-configured options, guide you through the installation command for your project (e.g.: `npm install --save-dev eslint`) and automatically inject the correct configuration into your `.gitpr.linter.yml`.

The wizard presets are controlled remotely via `templates/gitpr.linter-presets.json` (cached locally at `~/.gitpr/conf/`), so new linters can be added without waiting for a GitPR release.

---

## **6. Analysis Reports (Markdown)**

Every time the linter runs (whether manually via `--linter` or automatically before the commit), it consolidates the errors generated by the Regex Rules and the External Linters into a single report.

This formatted Markdown report is saved automatically, keeping a history of your local audits.

**Default Location:** `.gitpr/reports/linter/`

**Customization:** You can change the name and folder of this file by setting the `OUTPUT_FILE_NAME_LINTER` variable in your `~/.gitpr/.env` file.
