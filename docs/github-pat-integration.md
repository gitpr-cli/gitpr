# Technical Documentation: GitHub Token (PAT) Integration and Security

For the direct Issue creation feature (`gitpr --issue`) to work automatically, GitPR needs to communicate with the **GitHub REST API**. This documentation explains how this authentication occurs and how your credentials are protected locally.

📖 **Related documentation:** [`--issue` option guide (gitpr-issue-option.md)](gitpr-issue-option.md)

## 1. Why do we need a Token (PAT)?
Creating issues in remote repositories programmatically requires authentication. GitHub recommends using a **Personal Access Token (PAT)** so that command-line tools (CLI) can interact with your developer account securely.

## 2. Required Scope (`repo`)
GitPR only needs the **`repo`** scope enabled when creating your PAT. This guarantees permission to read metadata and create the Issue in the correct project (whether private or public).
To speed up this process, the CLI itself generates a dynamic configuration URL. It extracts your local repository name and builds a link that opens in your browser with the correct options already pre-selected.

## 3. Local Security and Encryption (Design Patterns)
The security of your credentials is treated with the utmost seriousness. GitPR **never** sends your key to third-party servers other than the GitHub API itself.

* **Symmetric Encryption (Fernet):** As soon as you paste your Token in the terminal, GitPR uses the native `cryptography` library to encrypt the string in real time.
* **Secure Storage:** The encrypted token is permanently saved in the global file `~/.gitpr/.env` (in your user's root folder, inaccessible to other operating system users).
* **Master Decryption Key:** The master key required to reverse this encryption is isolated on your local machine (`~/.gitpr/secret.key`).

Thanks to this architecture, if a local leak occurs and a malicious script reads your `.env` file, your GitHub Token will remain completely unreadable and protected.
