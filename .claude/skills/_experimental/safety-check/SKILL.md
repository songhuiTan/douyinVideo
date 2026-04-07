---
name: safety-check
description: |
  技能安全审查。在执行任何非只读 skill 前，检查内容是否安全。
  借鉴 OpenSpace 的 regex 安全规则，检测恶意模式、敏感信息泄露、危险命令等。
  当 skill 被修改或新建时自动触发。
category: tool_guide
---

# Safety Check — 技能安全审查

## 触发条件

- 新建或修改 SKILL.md 文件时
- 用户说"检查安全"或"/safety-check"
- Skill Evolution 产生新 skill 后

## 安全规则（借鉴 OpenSpace）

### 阻断级（发现即阻止）

| 规则 ID | 检测内容 | 正则 |
|---------|---------|------|
| `blocked.malware` | 恶意软件工具 | `ClawdAuthenticatorTool` |
| `blocked.destructive` | 破坏性命令 | `rm -rf /`、`rm -rf ~` |
| `blocked.data_exfil` | 数据外泄 | 上传 `/etc/shadow`、`~/.ssh/` |

### 警告级（发现即提示）

| 规则 ID | 检测内容 | 正则 |
|---------|---------|------|
| `suspicious.keyword` | 恶意关键词 | `malware\|stealer\|phishing\|keylogger` |
| `suspicious.secrets` | 敏感信息 | `api[-_ ]?key\|token\|password\|private key\|secret` |
| `suspicious.webhook` | 外部钩子 | `discord\.gg\|webhook\|hooks\.slack` |
| `suspicious.script` | 管道脚本 | `curl\| bash`、`wget\| sh` |
| `suspicious.url_short` | 短链接 | `bit\.ly\|tinyurl\|t\.co\|goo\.gl` |
| `suspicious.eval` | 动态执行 | `eval(\|exec(\|Function(` |

## 执行流程

### Step 1: 读取 Skill 内容

读取目标 SKILL.md 的完整内容。

### Step 2: 逐条检查安全规则

```
对每条规则：
├── 匹配到阻断级 → ❌ 阻止，报告具体匹配内容
├── 匹配到警告级 → ⚠️ 记录，继续检查
└── 无匹配 → ✅ 通过
```

### Step 3: 输出安全报告

```markdown
## 安全审查报告

**目标**：.claude/skills/sprint/SKILL.md
**结果**：✅ 通过 / ❌ 阻断 / ⚠️ 有警告

### 检查结果
| 规则 ID | 级别 | 匹配内容 | 行号 |
|---------|------|---------|------|
| blocked.malware | ❌ | ... | 42 |

### 建议
（如果有警告或阻断，给出修复建议）
```

### Step 4: 阻断处理

```
发现阻断级问题？
├── 是 → 不执行该 skill，向用户报告具体问题
│        等待用户明确说"忽略安全检查并继续"
└── 否 → 正常执行
```

## 在 Skill Evolution 中的角色

当 FIX/DERIVED/CAPTURED 产生新的 skill 内容时：
1. 在写入文件前自动运行 safety-check
2. 阻断级问题 → 不写入，报告给用户
3. 警告级问题 → 写入但标记，在 skill-metrics.md 中记录
