# 贡献指南

<div align="center">
  <a href="CONTRIBUTING_en.md"><img src="https://img.shields.io/badge/English-Contribution-11A683?style=for-the-badge" alt="English"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/%E4%B8%AD%E6%96%87-%E8%B4%A1%E7%8C%AE%E6%8C%87%E5%8D%97-59B390?style=for-the-badge" alt="中文贡献指南"></a>
</div>

欢迎通过 Issue 和 Pull Request 参与本项目。本项目处理的是手机备份和个人笔记数据，因此贡献前请特别注意隐私和密钥安全。

## 关于 Issue

涉及较大改动时，请优先开启 Issue 讨论，等待维护者确认方向后再提交 Pull Request。下面这些情况建议先开 Issue：

- 新增功能、兼容新机型或新 ColorOS 版本、修改导出结构、改变 GitHub 推送流程；
- 修复不确定的 Bug，例如不确定是导出器缺陷、备份格式差异，还是预期行为；
- 调整隐私、安全扫描、文件命名、附件匹配等会影响数据安全的逻辑。

提交 Issue 时请不要上传真实手机备份、导出的个人笔记、附件、截图中的隐私文本、API key、token、cookie 或密码。安全和隐私问题请按 [SECURITY.md](SECURITY.md) 私下报告。

## 提交变更

1. Fork 本仓库，从 `main` 创建语义清晰的分支，例如 `fix/todo-time-parser` 或 `docs/coloros-backup-path`。
2. 一个 Pull Request 只解决一个问题，避免把无关重构、格式化和功能变更混在一起。
3. 提交信息建议遵循 [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)，例如 `feat:`、`fix:`、`docs:`、`test:`、`refactor:`、`chore:`。
4. 提交前请阅读 [Pull Request 模板](PULL_REQUEST_TEMPLATE.md)，完成其中的检查项。
5. Pull Request 描述应说明改动内容、原因和验证方式；如果某项验证无法完成，请说明原因。

涉及用户可见行为时，请同步更新 `README.md` 和 `README.zh-CN.md`。涉及 skill 触发方式或操作流程时，也要更新 `SKILL.md`。

## 项目结构说明

- **Skill 入口**：`SKILL.md` 是 Codex 加载的技能说明，保持简洁，只放必要流程、安全边界和脚本入口。
- **导出脚本**：`scripts/export_coloros_notes.py` 是核心实现，只使用 Python 标准库，负责解析 `rich_note`、`todo`、`folder` 和 `file_backup.zip`。
- **文档**：`README.md` 和 `README.zh-CN.md` 分别面向英文和中文用户，必须保持功能说明一致。
- **GitHub 协作文件**：`.github/` 下放贡献指南、安全说明、Issue 模板和 PR 模板。
- **本地缓存**：`__pycache__`、`.pyc`、系统缩略图等生成物不应提交。

## 欢迎的贡献

- 修复 README、`SKILL.md`、帮助文本中的错别字、坏链接、路径说明错误或格式问题；
- 支持更多 ColorOS / OxygenOS / OPPO 备份格式，但必须提供无隐私的合成样例或字段说明；
- 改进 HTML 到 Markdown 的转换质量；
- 改进附件匹配、待办时间解析、分类映射或导出报告；
- 改进本地密钥扫描，同时确保不会打印密钥值；
- 增加不含真实个人数据的测试 fixture 或验证脚本。

## 不欢迎的贡献

- 提交真实手机备份、导出的个人笔记、照片附件或任何私人数据；
- 在仓库中写入 API key、GitHub token、cookie、密码、私钥或含凭据的 URL；
- 将脚本改为默认联网、自动上传、静默推送或自动调用外部服务；
- 删除 `.obsidian/workspace.json` 的排除规则；
- 把笔记标题或正文片段放回生成文件名中；
- 大规模无关格式化、换行、空白改动，或者只制造 diff 噪音的提交。

## 禁止无实质内容的提交

本项目不接受仅用于刷新提交记录或制造 diff 的改动。以下情况通常不会合并：

- 把一个正确表达替换为另一个等价表达；
- 只调整空格、空行、换行而不影响渲染或行为；
- 机械替换导致大量无关文件变化；
- 未说明实际影响的微小文案改动。

如果你发现确实会影响解析、渲染、隐私保护或用户理解的格式问题，请在 Pull Request 中说明影响范围和验证方式。

## 必须执行的验证

在仓库根目录运行：

```powershell
python "<codex-home>\skills\.system\skill-creator\scripts\quick_validate.py" .
python -c "import py_compile; py_compile.compile('scripts/export_coloros_notes.py', doraise=True)"
```

提交前还要审查暂存区文件列表和 diff，确认没有：

- API key、token、cookie、密码或携带凭据的 URL；
- 个人文件系统路径或私人笔记内容；
- 真实手机备份或生成的 Obsidian 导出文件；
- `.obsidian/workspace.json`。

导出器发现疑似密钥时会以退出码 `2` 停止。包含导出笔记的 Pull Request 不得绕过这个检查。

## 许可证

提交贡献即表示你同意该贡献按照 [MIT License](../LICENSE) 提供。
