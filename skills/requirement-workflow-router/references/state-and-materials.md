# 状态与材料边界

## 唯一机械状态

默认根目录：`~/.codex/requirement-workflow/`。

- `state.sqlite3`：唯一机械状态权威；使用 rollback journal、短 `BEGIN IMMEDIATE` 写事务、外键和同步写。
- `materials/`：独立 Git 仓库；每个需求一个目录，保存可读、可检索、可版本化材料。

不要把数据库提交到 Git，不要裸复制活跃数据库，不要让 Markdown 保存当前 slot、owner-generation 或批准布尔值。

## 发布顺序

1. 在材料仓库编辑并校验内容。
2. 提交 Git。
3. 运行 `workflow_state.py publish-material`；脚本验证 HEAD 中的字节与工作树一致后，把 commit、路径和 SHA-256 写入 SQLite。
4. 只有 SQLite 指向的提交是当前材料。

Git 成功而 SQLite 失败只产生非 current 候选；不得反向让 SQLite 指向不存在的提交。

## Controller 命令

```bash
python3 scripts/workflow_state.py init
python3 scripts/workflow_state.py admit --id ID --title TITLE --project-root /abs/path --operation-id UUID
python3 scripts/workflow_state.py snapshot --id ID
python3 scripts/workflow_state.py publish-material --id ID --kind frame --path ID/需求与边界.md --operation-id UUID
python3 scripts/workflow_state.py transition --id ID --expected-stage frame --to-stage align --owner-generation 1 --operation-id UUID
python3 scripts/workflow_state.py approve-plan --id ID --roadmap-sha256 HEX --operation-id UUID
python3 scripts/workflow_state.py verify
```

首个试点 `max_active=1`。只有试点验收后，controller 才能将它提高到 2 或 3；数据库硬限制始终不超过 3。
