# 一加备忘录导出到 Obsidian

[English](README.md)

这是一个 Codex skill 和仅使用 Python 标准库的导出脚本，用于把一加手机 / OPPO ColorOS 的备忘录备份转换为 Obsidian Markdown 笔记。

它读取 ColorOS / 一加备份工具常见的以下文件：

- `rich_note`
- `todo`
- `folder`
- `files/file_backup.zip`

脚本会把富文本备忘录转换成 Markdown，导出待办事项，复制实际引用的附件，生成导出报告，并扫描生成的文本中常见的密钥格式。扫描功能是为了防止把备忘录里的敏感内容误上传到开源仓库或 GitHub。Git 提交和推送是独立且必须明确请求的步骤。

## 功能

- 每篇富文本备忘录生成一个 Markdown 文件。
- 普通待办和已删除待办分别汇总。
- 支持常见 HTML 内容转换为 Markdown。
- 使用相对路径链接附件，兼容 Obsidian 和 GitHub。
- 保留备份中的文件夹分类，未分类笔记放入默认分类。
- 使用日期和记录 ID 生成稳定文件名，不把笔记正文放进文件路径。
- 本地扫描常见 API key、token 等格式，用于防止把备忘录里的敏感内容误上传到开源仓库或 GitHub，并且不会打印匹配到的密钥值。
- 明确排除 `.obsidian/workspace.json`，避免上传 Obsidian 工作区状态。
- 只依赖 Python 标准库，不需要安装第三方包。

## 安装

将本目录复制到 Codex 技能目录：

```text
<CODEX_HOME>/skills/oneplus-notes-to-obsidian/
```

目录结构应包含：

```text
oneplus-notes-to-obsidian/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── export_coloros_notes.py
```

重新加载 Codex 技能列表后，它会自动被发现；也可以显式使用 `$oneplus-notes-to-obsidian`。

## 获取一加 ColorOS 备忘录备份

不同机型和 ColorOS 版本的菜单名称可能略有差异。常见操作路径如下：

1. 打开 **设置**，搜索 **手机搬家**，或者直接打开系统应用 **手机搬家**。
2. 点击右上角的齿轮设置按钮。
3. 进入 **备份与恢复**。
4. 点击 **新建备份**。
5. 打开系统偏好设置的数据选择界面，勾选 **标签**。
6. 开始备份。

备份通常位于以下位置之一：

```text
手机存储/Android/data/com.oneplus.backuprestore/Backup
外置设备/Backup
```

将备份复制到电脑后，找到 `Data/<backup-id>/Note` 目录。脚本要求该目录中存在 `rich_note`、`todo` 和 `folder`；附件通常位于 `files/file_backup.zip`。

以上获取方式参考知乎用户阿微Alvin的回答：[一加手机便签备份及导出方法藏的好深额](https://www.zhihu.com/question/340704022/answer/3428351233)。不同机型、地区和 ColorOS 版本可能使用不同的菜单名称或备份路径，请以手机实际界面为准。

## 使用方法

根据当前电脑上的实际路径运行脚本：

```powershell
python "<skill-root>\scripts\export_coloros_notes.py" `
  --backup-dir "<backup-root>\Data\<backup-id>\Note" `
  --vault-dir "<obsidian-vault>" `
  --backup-id "<backup-id>" `
  --replace
```

`--replace` 只会删除并重新生成 Obsidian 库中本次导出的目标目录。如果目标目录中有手动修改过的内容，请不要直接使用这个参数。

脚本会打印 JSON 统计摘要，退出码含义如下：

- `0`：导出完成，密钥扫描没有发现匹配。
- `1`：输入无效或导出失败。
- `2`：导出完成，但密钥扫描发现疑似密钥。审查前不要提交或推送。

`--no-secret-scan` 只适用于特殊的本地场景。发布或推送导出内容前不应使用它。

## 输出结构

默认输出结构如下：

```text
<obsidian-vault>/
└── 手机备份/
    └── 一加备忘录/
        └── <backup-id>/
            ├── 备忘录/
            │   └── <分类>/
            │       └── YYYY-MM-DD-note-<record-id>.md
            ├── 待办/
            │   ├── 待办.md
            │   └── 待办-已删除.md
            ├── 附件/
            └── 导出报告.md
```

导出报告包含数量统计和附件匹配情况，不会写入密钥值。

## GitHub 安全要求

推送到 GitHub 是独立且必须明确请求的步骤。执行时必须：

1. 使用用户提供的远端地址，但不能在 URL 中嵌入凭据。
2. 使用本机已有的 Git Credential Manager 或用户正常的认证流程。
3. 将 `.obsidian/workspace.json` 加入 `.gitignore`。
4. 验证 `.obsidian/workspace.json` 既没有被跟踪，也没有进入暂存区。
5. 提交前运行导出脚本的密钥扫描。
6. 发现疑似密钥时停止提交和推送。

绝不要把 API key、个人访问令牌、cookie 或密码粘贴到对话、命令参数、URL、README、提交信息或本技能目录中。

## 开源发布检查

发布本技能前建议完成以下检查：

- 使用 Codex `skill-creator` 技能中的 `quick_validate.py`。
- 执行 `python -m py_compile scripts/export_coloros_notes.py`。
- 搜索凭据、个人文件系统路径和未完成的占位文本。
- 同时审查暂存区中的文件名和文件内容，不能让笔记标题或正文片段成为文件路径。
- 检查 README 中的外部链接。
- 保留项目中的 MIT 许可证、贡献指南和安全报告说明。

## 署名

备份获取方法参考了上述知乎回答，并在本 README 中保留了原作者和来源链接。导出脚本本身设计为本地运行，不会自动访问一加、OPPO、知乎、GitHub API 或其他外部服务。

## 参与贡献

提交 Issue 或 Pull Request 前请先阅读[贡献指南](.github/CONTRIBUTING.md)。贡献内容中不得包含手机备份、导出的个人笔记、API key、token、cookie 或其他个人隐私文本。

## 许可证

本项目使用 [MIT License](LICENSE)。
