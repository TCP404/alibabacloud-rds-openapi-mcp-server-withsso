---
name: alibabacloud-rds-copilot
description: >-
  使用阿里云 RDS Copilot API,帮助用户完成 RDS 相关的智能问答、SQL 优化、实例运维和故障排查,
  可直接调用 call_rds_ai.py 脚本获取实时结果。
---

## Skill 概览

本 Skill 用于在对话中充当 **阿里云 RDS Copilot 的智能代理**:

- **理解用户的自然语言需求**(中文或英文),识别是否与 RDS Copilot 相关;
- **直接调用内置脚本** `scripts/call_rds_ai.py` 实时查询 RDS Copilot 并获取结果;
- 当获取到结果或用户粘贴错误信息时,**进一步解释、诊断并给出后续建议**。

**工作模式**:
- 使用 `scripts/call_rds_ai.py` 脚本直接获取 RDS Copilot 的实时响应

## 触发条件

在对话中,满足以下任一条件时,应优先考虑使用本 Skill:

- 用户明确提到 **"RDS Copilot"**、**"RDS AI助手"**、**"RDS AI"**、**"阿里云数据库 AI 助手"**;
- 用户希望 **用阿里云的 AI 能力进行 SQL 优化、SQL 诊断、实例运维、排障、查询实例列表** 等操作;
- 用户给出或提到 `alibabacloud_rdsai20250507` 等 SDK、`ChatMessagesRequest`、`chat_messages_with_sse` 等关键词;
- 用户请求你 **"帮我写一个/改一个 RDS Copilot 调用脚本"** 或类似表述;
- 用户询问 **RDS 相关的运维、性能、诊断问题**,且这些问题适合通过 RDS Copilot 来回答。

**工作模式选择**:
- 如用户环境变量已配置(`ALIBABA_CLOUD_ACCESS_KEY_ID` 和 `ALIBABA_CLOUD_ACCESS_KEY_SECRET`),优先直接调用脚本获取结果;
- 如不确定,应先向用户确认是否希望直接调用 RDS Copilot 获取结果。

## 前置条件与环境假设

### 依赖安装

**Python 版本要求**：本 Skill 需要 **Python 3.7+**（推荐 Python 3.8 或更高版本）。

在使用本 Skill 前，需要安装阿里云 RDS Copilot SDK。系统会自动检测依赖是否已安装：

- **如已安装依赖**：直接调用 `call_rds_ai.py` 脚本执行查询
- **如未安装依赖**：自动使用 `requirements.txt` 安装所需依赖：
  ```bash
  # 使用 pip3 确保安装到 Python 3 环境
  pip3 install -r .claude/skills/alibabacloud-rds-copilot/requirements.txt
  # 或使用 pip（如系统默认已是 Python 3）
  pip install -r .claude/skills/alibabacloud-rds-copilot/requirements.txt
  ```

依赖包列表（定义在 `requirements.txt` 中）：
- `alibabacloud_rdsai20250507>=1.0.0`
- `alibabacloud_tea_openapi>=0.3.0`
- `alibabacloud_tea_util>=0.3.0`

**注意**：首次安装依赖可能需要几秒到几十秒，安装完成后即可正常使用。

### 其他环境要求

- 已配置阿里云访问凭证（优先通过环境变量）：
  - `ALIBABA_CLOUD_ACCESS_KEY_ID`
  - `ALIBABA_CLOUD_ACCESS_KEY_SECRET`
- 默认使用的 Endpoint 为：`rdsai.aliyuncs.com`。
- 若用户未指定地域，则默认 **`cn-hangzhou`**；未指定语言，则默认 **`zh-CN`**；时区默认 **`Asia/Shanghai`**。

## 标准使用流程

当用户环境已配置阿里云凭证时,按以下流程操作:

1. **确认任务类型与参数**
   - 判断用户意图:SQL 编写/优化、SQL 诊断、实例参数调优、故障排查、性能分析、查询实例列表等。
   - 收集必要参数(如未指定则使用默认值):
     - `--region`:地域 ID(默认 `cn-hangzhou`)
     - `--language`:语言(默认 `zh-CN`)
     - `--timezone`:时区(默认 `Asia/Shanghai`)
     - `--custom-agent-id`:专属 Agent ID(可选)
     - `--conversation-id`:会话 ID,用于多轮对话(可选)

2. **构造查询并调用脚本**
   - 将用户需求整理为清晰的 query 文本;
   - **自动检查并安装依赖**（如需要）:
     ```bash
     # 如检测到缺少依赖，先自动安装（使用 Python 3）
     pip3 install -r .claude/skills/alibabacloud-rds-copilot/requirements.txt
     ```
   - 使用 `scripts/call_rds_ai.py` 脚本调用 RDS Copilot:
     ```bash
     # 使用 python3 命令确保 Python 3 环境
     python3 .claude/skills/alibabacloud-rds-copilot/scripts/call_rds_ai.py "<用户查询>" [可选参数]
     ```
   - 示例:
     ```bash
     # 基础查询
     python3 .claude/skills/alibabacloud-rds-copilot/scripts/call_rds_ai.py "查询杭州地域的 RDS MySQL 实例列表"
     
     # 指定地域
     python3 .claude/skills/alibabacloud-rds-copilot/scripts/call_rds_ai.py "优化这条SQL" --region cn-beijing
     
     # 多轮对话
     python3 .claude/skills/alibabacloud-rds-copilot/scripts/call_rds_ai.py "继续分析" --conversation-id "<上次返回的会话ID>"
     ```

3. **解析结果并后续处理**
   - 将 RDS Copilot 的响应用自然语言解释给用户;
   - 如返回包含 SQL 或操作步骤,评估风险并提醒:
     - 避免在生产环境直接执行高风险语句(如大表 `DELETE` / `UPDATE` / 结构变更);
     - 建议在测试环境验证或加上备份/条件限制。
   - 如需继续对话,记录 `conversation_id` 用于下一轮查询。

## 工具脚本使用说明

### 脚本路径
```
.claude/skills/alibabacloud-rds-copilot/scripts/call_rds_ai.py
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 查询内容(必需),使用 `-` 从标准输入读取 | - |
| `--region` / `--region-id` | 阿里云地域 ID | `cn-hangzhou` |
| `--language` / `--lang` | 语言 | `zh-CN` |
| `--timezone` / `--tz` | 时区 | `Asia/Shanghai` |
| `--custom-agent-id` | 专属 Agent ID | 无 |
| `--conversation-id` / `--conv-id` | 会话 ID(多轮对话) | 无 |
| `--endpoint` | API 端点 | `rdsai.aliyuncs.com` |
| `--no-stream` | 禁用流式输出 | False(默认启用流式) |

### 使用示例

```bash
# 基础查询
python3 .claude/skills/alibabacloud-rds-copilot/scripts/call_rds_ai.py "查询杭州地域的 RDS MySQL 实例列表"

# 指定地域和语言
python3 .claude/skills/alibabacloud-rds-copilot/scripts/call_rds_ai.py "查询实例列表" --region cn-beijing --language en-US

# 使用专属 Agent
python3 .claude/skills/alibabacloud-rds-copilot/scripts/call_rds_ai.py "优化这条SQL:SELECT * FROM users WHERE status=1" --custom-agent-id "your-agent-id"

# 多轮对话(使用上次返回的会话ID)
python3 .claude/skills/alibabacloud-rds-copilot/scripts/call_rds_ai.py "继续上面的分析" --conversation-id "conv-xxx"

# 从标准输入读取查询
echo "帮我诊断慢SQL问题" | python3 .claude/skills/alibabacloud-rds-copilot/scripts/call_rds_ai.py -
```

### 输出格式

脚本会将查询信息输出到 `stderr`,将 RDS Copilot 的回答输出到 `stdout`,便于分离日志和结果:

```
[查询] 查询杭州地域实例列表
[地域] cn-hangzhou | [语言] zh-CN
============================================================
[RDS Copilot 回答]
<实际回答内容>

[会话ID] conv-xxxx-xxxx-xxxx
```

## 安全与合规边界

使用本 Skill 时，必须遵守以下约束：

- **不要编造或猜测任何阿里云 AccessKey、Secret 或账号信息**；
- 如用户在明文粘贴了敏感信息（AccessKey、密码等），应提示其进行脱敏并尽量不在回答中重复；
- 对涉及生产实例的操作建议，应尽量提供：
  - 备份/回滚建议；
  - 在测试环境验证的建议；
  - 对高风险操作（如大规模删除、结构变更）给出显式风险提示；
- 不建议用户在未充分验证的情况下，直接在生产环境执行由 RDS Copilot 生成的 SQL 或 DDL 语句。

## 与用户的交互风格

- 优先用 **中文** 与用户沟通；如检测到用户使用英文，可自动切换英文，并相应设置 `language` 字段；
- 回答时尽量 **结构化**：分清"需求理解 → 请求设计 → 风险提示 → 后续建议";
- 对于新手用户，可适当解释每个关键参数的含义（如 `region_id`、`custom_agent_id`、`conversation_id`）；
- 对于高级用户，可更侧重于参数选型、性能调优思路、以及如何将 RDS Copilot 集成进现有运维/开发流程。
