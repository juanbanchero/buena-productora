# BuenaLive Automation CLAUDE.md

## Purpose
Automated ticket purchasing system for BuenaLive events with secure credential management and GUI interface.

## Architecture Overview
Single-purpose Python application that combines web automation, credential management, and Google Sheets integration. The application provides both GUI and headless modes for ticket purchasing automation.

## Module Structure
- `main.py` - Main application with GUI and automation core
- `credential_manager.py` - Secure credential storage and encryption
- `credentials.json` - Google Sheets API credentials
- `sessions/` - Claude Code session management

## Key Components

### Main Application (main.py)
- `TicketAutomation:21-622` - Core automation engine
  - Web scraping with Selenium WebDriver
  - Event detection and ticket purchasing
  - Google Sheets integration for data tracking
- `AutomationGUI:623-900+` - Tkinter-based user interface
  - Credential input with auto-save functionality
  - Event selection and automation controls
  - Real-time logging and status updates

### Credential Manager (credential_manager.py)
- `CredentialManager:10-115` - Secure credential handling
  - Automatic encryption using Fernet (cryptography library)
  - User/machine/app-specific key generation
  - Transparent save/load functionality
  - Credential validation and updates

## Key Features

### Security Implementation
- Transparent credential encryption with user-specific keys
- Automatic credential detection and loading
- Secure file storage in user home directory
- Machine-specific encryption keys prevent credential sharing

### Automation Capabilities
- Chrome WebDriver automation with headless mode support
- Event detection and ticket availability monitoring
- Automated purchasing with form filling
- Google Sheets logging for purchase tracking

### User Interface
- Credential management with save/clear options
- Event selection from detected available events
- Real-time automation status and logging
- Headless mode toggle for production use

## Integration Points

### External Dependencies
- `selenium` - Web automation framework
- `cryptography` - Credential encryption
- `gspread` - Google Sheets API client
- `tkinter` - GUI framework
- `google-oauth2` - Google authentication

### File Dependencies
- `credentials.json` - Google Sheets service account credentials
- User home directory encrypted credential storage
- Chrome WebDriver executable

## Configuration

### Required Setup
- Chrome browser and ChromeDriver installation
- Google Sheets API credentials file
- Target website access credentials

### Environment Variables
- No environment variables required (uses file-based configuration)

### Credential Storage
- Location: `~/.buena-live_{username}_{project}/user_credentials.enc`
- Encryption: Fernet with SHA256-derived keys
- Scope: User/machine/project specific

## Usage Patterns

### GUI Mode
- Launch application through main.py execution
- Input credentials with optional auto-save
- Select events and configure automation parameters
- Monitor real-time logging during automation

### Headless Mode
- Set `headless_mode=True` in TicketAutomation initialization
- Suitable for production/server deployment
- Faster execution without browser window

## Related Documentation
- sessions/ - Claude Code session management and protocols

# Session Management

This section provides collaborative guidance for Claude Code Sessions.

## Collaboration Philosophy

**Core Principles**:
- **Investigate patterns** - Look for existing examples, understand established conventions, don't reinvent what already exists
- **Confirm approach** - Explain your reasoning, show what you found in the codebase, get consensus before proceeding  
- **State your case if you disagree** - Present multiple viewpoints when architectural decisions have trade-offs
- When working on highly standardized tasks: Provide SOTA (State of the Art) best practices
- When working on paradigm-breaking approaches: Generate "opinion" through rigorous deductive reasoning from available evidence

## Task Management

### Best Practices
- One task at a time (check .claude/state/current_task.json)
- Update work logs as you progress  
- Mark todos as completed immediately after finishing

### Quick State Checks
```bash
cat .claude/state/current_task.json  # Shows current task
git branch --show-current             # Current branch/task
```

### current_task.json Format

**ALWAYS use this exact format for .claude/state/current_task.json:**
```json
{
  "task": "task-name",        // Just the task name, NO path, NO .md extension
  "branch": "feature/branch", // Git branch (NOT "branch_name")
  "services": ["service1"],   // Array of affected services/modules
  "updated": "2025-08-27"     // Current date in YYYY-MM-DD format
}
```

**Common mistakes to avoid:**
- ❌ Using `"task_file"` instead of `"task"`
- ❌ Using `"branch_name"` instead of `"branch"`  
- ❌ Including path like `"tasks/m-task.md"`
- ❌ Including `.md` file extension

## Using Specialized Agents

You have specialized subagents for heavy lifting. Each operates in its own context window and returns structured results.

### Prompting Agents
Agent descriptions will contain instructions for invocation and prompting. In general, it is safer to issue lightweight prompts. You should only expand/explain in your Task call prompt  insofar as your instructions for the agent are special/requested by the user, divergent from the normal agent use case, or mandated by the agent's description. Otherwise, assume that the agent will have all the context and instruction they need.

Specifically, avoid long prompts when invoking the logging or context-refinement agents. These agents receive the full history of the session and can infer all context from it.

### Available Agents

1. **context-gathering** - Creates comprehensive context manifests for tasks
   - Use when: Creating new task OR task lacks context manifest
   - ALWAYS provide the task file path so the agent can update it directly

2. **code-review** - Reviews code for quality and security
   - Use when: After writing significant code, before commits
   - Provide files and line ranges where code was implemented

3. **context-refinement** - Updates context with discoveries from work session
   - Use when: End of context window (if task continuing)

4. **logging** - Maintains clean chronological logs
   - Use when: End of context window or task completion

5. **service-documentation** - Updates service CLAUDE.md files
   - Use when: After service changes

### Agent Principles
- **Delegate heavy work** - Let agents handle file-heavy operations
- **Be specific** - Give agents clear context and goals
- **One agent, one job** - Don't combine responsibilities

## Code Philosophy

### Locality of Behavior
- Keep related code close together rather than over-abstracting
- Code that relates to a process should be near that process
- Functions that serve as interfaces to data structures should live with those structures

### Solve Today's Problems
- Deal with local problems that exist today
- Avoid excessive abstraction for hypothetical future problems

### Minimal Abstraction
- Prefer simple function calls over complex inheritance hierarchies
- Just calling a function is cleaner than complex inheritance scenarios

### Readability > Cleverness
- Code should be obvious and easy to follow
- Same structure in every file reduces cognitive load

## Protocol Management

### CRITICAL: Protocol Recognition Principle

**When the user mentions protocols:**

1. **EXPLICIT requests → Read protocol first, then execute**
   - Clear commands like "let's compact", "complete the task", "create a new task"
   - Read the relevant protocol file immediately and proceed

2. **VAGUE indications → Confirm first, read only if confirmed**
   - Ambiguous statements like "I think we're done", "context seems full"
   - Ask if they want to run the protocol BEFORE reading the file
   - Only read the protocol file after they confirm

**Never attempt to run protocols from memory. Always read the protocol file before executing.**

### Protocol Files and Recognition

These protocols guide specific workflows:

1. **sessions/protocols/task-creation.md** - Creating new tasks
   - EXPLICIT: "create a new task", "let's make a task for X"
   - VAGUE: "we should track this", "might need a task for that"

2. **sessions/protocols/task-startup.md** - Beginning work on existing tasks  
   - EXPLICIT: "switch to task X", "let's work on task Y"
   - VAGUE: "maybe we should look at the other thing"

3. **sessions/protocols/task-completion.md** - Completing and closing tasks
   - EXPLICIT: "complete the task", "finish this task", "mark it done"
   - VAGUE: "I think we're done", "this might be finished"

4. **sessions/protocols/context-compaction.md** - Managing context window limits
   - EXPLICIT: "let's compact", "run context compaction", "compact and restart"
   - VAGUE: "context is getting full", "we're using a lot of tokens"

### Behavioral Examples

**Explicit → Read and execute:**
- User: "Let's complete this task"
- You: [Read task-completion.md first] → "I'll complete the task now. Running the logging agent..."

**Vague → Confirm before reading:**
- User: "I think we might be done here"
- You: "Would you like me to run the task completion protocol?"
- User: "Yes"
- You: [NOW read task-completion.md] → "I'll complete the task now..."
