# RDS Copilot Claude Skill

阿里云 [RDS AI助手](https://help.aliyun.com/zh/rds/apsaradb-rds-for-mysql/rds-copilot-overview) 的 Claude Skill，用于在 Claude 对话中直接调用 RDS AI 助手能力，完成 SQL 优化、实例运维、故障排查等任务。

<img src="../assets/claude_skill.png" alt="Claude Skill 使用示例" width="800"/>


## 环境要求

### 开通 RDS AI助手专业版
- [阿里云 RDS AI助手](https://rdsnext.console.aliyun.com/rdsCopilotProfessional/cn-hangzhou) 已经开通专业版


### Python 版本

- **Python 3.7+**（推荐 Python 3.8 或更高版本）

验证 Python 版本：
```bash
python3 --version
```

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/aliyun/alibabacloud-rds-openapi-mcp-server
cd alibabacloud-rds-openapi-mcp-server/skill
```

### 2. 安装依赖

使用 `pip3` 安装所需的阿里云 SDK：

```bash
pip3 install -r alibabacloud-rds-copilot/requirements.txt
```

依赖包列表：
- `alibabacloud_rdsai20250507>=1.0.0` - 阿里云 RDS AI SDK
- `alibabacloud_tea_openapi>=0.3.0` - 阿里云 OpenAPI 核心库
- `alibabacloud_tea_util>=0.3.0` - 阿里云工具库

### 3. 配置环境变量

设置阿里云访问凭证（必需）：

**macOS / Linux：**
```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID="your-access-key-id"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your-access-key-secret"
```

**Windows (PowerShell)：**
```powershell
$env:ALIBABA_CLOUD_ACCESS_KEY_ID="your-access-key-id"
$env:ALIBABA_CLOUD_ACCESS_KEY_SECRET="your-access-key-secret"
```

**永久配置（推荐）：**

将上述命令添加到你的 shell 配置文件中：
- Bash: `~/.bashrc` 或 `~/.bash_profile`
- Zsh: `~/.zshrc`
- Windows: 系统环境变量设置

### 4. 部署 Skill 到 Claude

将 Skill 文件复制到 Claude 的 skills 目录：

**方法一：直接使用本仓库结构**

如果你使用的是 Claude Desktop 或支持自定义 skills 的环境，本仓库已经包含正确的目录结构 `alibabacloud-rds-copilot/`，可以直接使用。

**方法二：复制到用户级 skills 目录**

```bash
# macOS / Linux
mkdir -p ~/.claude/skills/
cp -r alibabacloud-rds-copilot ~/.claude/skills/

# Windows (PowerShell)
New-Item -ItemType Directory -Path "$env:USERPROFILE\.claude\skills\" -Force
Copy-Item -Recurse ".claude\skills\aliyun-rds-copilot" "$env:USERPROFILE\.claude\skills\"
```

**方法三：创建符号链接（推荐开发环境）**

```bash
# macOS / Linux
mkdir -p ~/.claude/skills/
ln -s "$(pwd)/alibabacloud-rds-copilot" ~/alibabacloud-rds-copilot

# Windows (需管理员权限)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\skills\aliyun-rds-copilot" -Target "$(Get-Location)\.claude\skills\aliyun-rds-copilot"
```

### 5. 验证安装

运行claude，选择alibabacloud-rds-copilot skill：

```bash
claude
```
```bash
/alibabacloud-rds-copilot 我在杭州有多少实例？
```


预期输出：
```
[查询] 查询杭州地域的 RDS 实例列表
[地域] cn-hangzhou | [语言] zh-CN
============================================================
[RDS Copilot 回答]
<RDS Copilot 的实际回答内容>

[会话ID] conv-xxxx-xxxx-xxxx
```

## 使用说明

### 基础用法

在 Claude 对话中，直接提问 RDS 相关问题：

```
你：查询杭州地域有哪些 MySQL 实例？
Claude：[调用 RDS Copilot 并返回结果]

你：针对rm-xxx实例帮我分析和优化这条 SQL：SELECT * FROM users WHERE status=1 ORDER BY created_at
Claude：[调用 RDS Copilot 获取 SQL 优化建议]
```

## 常见问题

### 1. 提示找不到模块 `alibabacloud_rdsai20250507`

**原因**：未安装依赖包或使用了错误的 Python 环境。

**解决方法**：
```bash
# 使用 pip3 确保安装到 Python 3 环境
pip3 install -r alibabacloud-rds-copilot/requirements.txt

# 验证安装
pip3 list | grep alibabacloud
```

### 2. 提示环境变量未设置

**错误信息**：
```
未找到阿里云访问凭证。请设置环境变量:
  ALIBABA_CLOUD_ACCESS_KEY_ID
  ALIBABA_CLOUD_ACCESS_KEY_SECRET
```

**解决方法**：
按照"配置环境变量"章节设置 AccessKey 和 Secret。

### 3. Claude 未识别到 Skill

**原因**：Skill 文件未正确部署到 Claude skills 目录。

**解决方法**：
- 检查 `alibabacloud-rds-copilot/SKILL.md` 是否存在
- 确认 Skill 目录结构完整
- 重启 Claude 应用

### 5. 使用 `python` 命令报错

**原因**：系统中 `python` 命令指向 Python 2 或未配置。

**解决方法**：
统一使用 `python3` 命令：
```bash
python3 alibabacloud-rds-copilot/scripts/call_rds_ai.py "your query"
```
