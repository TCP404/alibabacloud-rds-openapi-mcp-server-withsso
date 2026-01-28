# RDS Copilot Claude Skill

Alibaba Cloud [RDS AI Assistant](https://help.aliyun.com/zh/rds/apsaradb-rds-for-mysql/rds-copilot-overview) Claude Skill enables you to directly invoke RDS AI assistant capabilities within Claude conversations for SQL optimization, instance operations, troubleshooting, and more.

<img src="../assets/claude_skill.png" alt="Claude Skill Usage Example" width="800"/>


## Requirements

### Enable RDS AI Assistant Professional Edition
- [Alibaba Cloud RDS AI Assistant](https://rdsnext.console.aliyun.com/rdsCopilotProfessional/cn-hangzhou) Professional Edition must be enabled

### Python Version

- **Python 3.7+** (Python 3.8 or higher recommended)

Verify your Python version:
```bash
python3 --version
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/aliyun/alibabacloud-rds-openapi-mcp-server
cd alibabacloud-rds-openapi-mcp-server/skill
```

### 2. Install Dependencies

Install required Alibaba Cloud SDKs using `pip3`:

```bash
pip3 install -r alibabacloud-rds-copilot/requirements.txt
```

Dependency list:
- `alibabacloud_rdsai20250507>=1.0.0` - Alibaba Cloud RDS AI SDK
- `alibabacloud_tea_openapi>=0.3.0` - Alibaba Cloud OpenAPI Core Library
- `alibabacloud_tea_util>=0.3.0` - Alibaba Cloud Utility Library

### 3. Configure Environment Variables

Set up Alibaba Cloud access credentials (required):

**macOS / Linux:**
```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID="your-access-key-id"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your-access-key-secret"
```

**Windows (PowerShell):**
```powershell
$env:ALIBABA_CLOUD_ACCESS_KEY_ID="your-access-key-id"
$env:ALIBABA_CLOUD_ACCESS_KEY_SECRET="your-access-key-secret"
```

**Permanent Configuration (Recommended):**

Add the above commands to your shell configuration file:
- Bash: `~/.bashrc` or `~/.bash_profile`
- Zsh: `~/.zshrc`
- Windows: System Environment Variables

### 4. Deploy Skill to Claude

Copy the Skill files to Claude's skills directory:

**Method 1: Use Repository Structure Directly**

If you're using Claude Desktop or an environment that supports custom skills, this repository already includes the correct directory structure `alibabacloud-rds-copilot/` and can be used directly.

**Method 2: Copy to User-Level Skills Directory**

```bash
# macOS / Linux
mkdir -p ~/.claude/skills/
cp -r alibabacloud-rds-copilot ~/.claude/skills/

# Windows (PowerShell)
New-Item -ItemType Directory -Path "$env:USERPROFILE\.claude\skills\" -Force
Copy-Item -Recurse "alibabacloud-rds-copilot" "$env:USERPROFILE\.claude\skills\"
```

**Method 3: Create Symbolic Link (Recommended for Development)**

```bash
# macOS / Linux
mkdir -p ~/.claude/skills/
ln -s "$(pwd)/alibabacloud-rds-copilot" ~/.claude/skills/alibabacloud-rds-copilot

# Windows (Requires Administrator Privileges)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\skills\alibabacloud-rds-copilot" -Target "$(Get-Location)\alibabacloud-rds-copilot"
```

### 5. Verify Installation

Run the test script to verify the configuration:

```bash
python3 alibabacloud-rds-copilot/scripts/call_rds_ai.py "List RDS instances in Hangzhou region"
```

Expected output:
```
[Query] List RDS instances in Hangzhou region
[Region] cn-hangzhou | [Language] zh-CN
============================================================
[RDS Copilot Response]
<Actual response from RDS Copilot>

[Session ID] conv-xxxx-xxxx-xxxx
```

## Usage

### Basic Usage

Ask RDS-related questions directly in Claude conversations:

```
You: What MySQL instances are available in Hangzhou region?
Claude: [Calls RDS Copilot and returns results]

You: Help me optimize this SQL: SELECT * FROM users WHERE status=1 ORDER BY created_at
Claude: [Calls RDS Copilot for SQL optimization suggestions]

You: Continue analyzing the performance bottlenecks of this SQL
Claude: [Uses session ID for multi-turn conversation]
```

## Troubleshooting

### 1. Module `alibabacloud_rdsai20250507` Not Found

**Cause**: Dependencies not installed or using incorrect Python environment.

**Solution**:
```bash
# Use pip3 to ensure installation in Python 3 environment
pip3 install -r alibabacloud-rds-copilot/requirements.txt

# Verify installation
pip3 list | grep alibabacloud
```

### 2. Environment Variables Not Set

**Error message**:
```
Alibaba Cloud access credentials not found. Please set environment variables:
  ALIBABA_CLOUD_ACCESS_KEY_ID
  ALIBABA_CLOUD_ACCESS_KEY_SECRET
```

**Solution**:
Follow the "Configure Environment Variables" section to set AccessKey and Secret.

### 3. Claude Doesn't Recognize the Skill

**Cause**: Skill files not properly deployed to Claude skills directory.

**Solution**:
- Check if `alibabacloud-rds-copilot/SKILL.md` exists
- Confirm the Skill directory structure is complete
- Restart Claude application

### 4. Error Using `python` Command

**Cause**: System's `python` command points to Python 2 or is not configured.

**Solution**:
Use `python3` command consistently:
```bash
python3 alibabacloud-rds-copilot/scripts/call_rds_ai.py "your query"
```
