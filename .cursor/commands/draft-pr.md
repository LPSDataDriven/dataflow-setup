# Draft Pull Request Title and Description

This command helps you draft a pull request title and description by analyzing an existing PR's changes.

## Prerequisites

### Install GitHub MCP Server (if using Cursor)

If you're using Cursor IDE, install the GitHub MCP server for enhanced GitHub integration:

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Go to "Features" → "Model Context Protocol"
3. Click "Add Server"
4. Add the GitHub MCP server configuration:
   ```json
   "github": {
     "url": "https://api.githubcopilot.com/mcp/",
     "headers": {
       "Authorization": "Bearer <your_github_personal_access_token>"
     }
   }
   ```
5. Replace `your_github_personal_access_token` with your GitHub personal access token
   - [Create a GitHub personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
   - **Important**: Create a **classic token** with **repo** access permissions
   - **Organization Authorization**: After creating the token, you must authorize it with the organization:
     - Go to your [Personal access tokens page](https://github.com/settings/tokens)
     - Find your token in the list
     - Click **"Configure SSO"** next to your token
     - Select the organization that owns this repository
     - Click **"Authorize"** to grant access
6. Click "Save"

This will enable GitHub integration features like creating PRs, viewing issues, and more directly from Cursor.

## Usage
Type `/draft-pr` in the chat, optionally followed by a GitHub PR URL.

**Examples:**
- `/draft-pr` (command will ask for PR URL)
- `/draft-pr https://github.com/LPSDataDriven/dataflow-setup/pull/123` (provides URL directly)

## Instructions
1. The command will **first check if GitHub MCP server is available**
2. If MCP server is **not available**:
   - **Inform the user**: "GitHub MCP server is not available"
   - **Ask the user to choose**:
     - **Option A**: "Would you like to configure the GitHub MCP server?" (provide installation instructions)
     - **Option B**: "Would you like to use local git tools instead?" (ask for branches)
3. If MCP server is **available**:
   - If PR URL was provided with the command, use it directly
   - If no PR URL was provided, ask for the GitHub PR URL
   - Use the GitHub MCP server to fetch the PR diff and details
   - Analyze the changes made in the PR
 - Draft a title and description following the project's PR guidelines (@pull-requests.mdc)
   - Ask for your approval before making any updates to GitHub
4. If user chooses **local git tools**:
   - Ask for origin branch and destination branch
   - Use `git diff` to analyze changes between branches
   - Use `git log` to get commit messages and changes
   - Analyze the changes made between the branches
   - Draft a title and description following the project's PR guidelines (@pull-requests.mdc)
   - Ask for your approval before making any updates to GitHub

## Troubleshooting

### If GitHub MCP Server is Not Available
When the command detects that the GitHub MCP server is not available, it will:

1. **Inform you**: "GitHub MCP server is not available"
2. **Ask for your choice**:
   - **"Would you like to configure the GitHub MCP server?"**
   - **"Would you like to use local git tools instead?"**

**If you choose to configure MCP Server:**
1. **Check your MCP configuration** in Cursor Settings
2. **Verify your GitHub token** is valid and has proper permissions
3. **Ensure organization authorization** is completed (see Prerequisites)
4. **Restart Cursor** after making configuration changes
5. **Check the MCP server status** in Cursor's developer tools or logs

**If you choose local git tools:**
1. **Provide origin branch** (e.g., `feature/new-model`)
2. **Provide destination branch** (e.g., `main`)
3. **Command will use `git diff` and `git log`** to analyze changes
4. **Generate title and description** based on local git analysis

This local git method works without GitHub API access and can analyze any local git repository.

## Examples

### Option 1: Provide PR URL with command
1. Type `/draft-pr https://github.com/LPSDataDriven/dataflow-setup/pull/123` in the chat
2. Command checks if GitHub MCP server is available
3. If available: Proceeds directly to analyze the PR
4. Review the generated title and description
5. Approve or request changes before any GitHub updates are made

### Option 2: Provide PR URL after command
1. Type `/draft-pr` in the chat
2. Command checks if GitHub MCP server is available
3. If available: Provide a PR URL when prompted
4. Review the generated title and description
5. Approve or request changes before any GitHub updates are made

### Option 3: Git Fallback (when MCP server unavailable)
1. Type `/draft-pr` in the chat
2. Command detects MCP server is not available
3. Command informs: "GitHub MCP server is not available"
4. Command asks: "Would you like to configure the GitHub MCP server or use local git tools instead?"
5. Choose "use local git tools"
6. Provide origin branch (e.g., `feature/revenue-model-update`)
7. Provide destination branch (e.g., `main`)
8. Command analyzes changes using `git diff` and `git log`
9. Review the generated title and description
10. Approve or request changes before any GitHub updates are made

The command will generate a properly formatted PR title and description following the project's standards and guidelines.
