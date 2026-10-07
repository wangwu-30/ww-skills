# 方法依据与工具边界

调研结论：采用“共同基线 → 两侧意图变化链 → 交互分析 → 人裁定语义冲突 → 授权后的工程整合”。下列工具和研究补足取证与验证，不代替人的业务决定，也不要求引入专用引擎。

## 查对基线和变化链

按本次两个准确提交查询：

```sh
git merge-base --all A B
git log --graph --oneline A B
git log --reverse --topo-order base..A
git log --reverse --topo-order base..B
git diff --find-renames base A -- relevant/paths
git diff --find-renames base B -- relevant/paths
```

`A`、`B`、`base` 和路径是需替换的分析输入。大仓库先定位需求和路径，再按需展开；不默认一次输出完整大 diff。

[Git merge-base 官方文档](https://git-scm.com/docs/git-merge-base)明确允许多个最佳共同祖先。不带 `--all` 时，多基线历史中返回哪一个没有保证。曾同步另一分支时，有效合并基线可能晚于原始分叉点；历史意图和本次净变化要分别说明。`--fork-point` 依赖特定 ref 的 reflog，不是找任意两分支原始分叉点的通用命令。

若历史含移植或重放，按需用 `git log --left-right --cherry-mark A...B` 辅助识别等价补丁。它比较补丁等价，不证明意图或所有运行行为等价；`--first-parent` 可以了解整合主线，不能替代对被合入贡献的检查。[Git log 官方文档](https://git-scm.com/docs/git-log)

## 文字合并预检

先查当前 Git 版本及支持的参数。在允许创建 Git 对象的隔离仓库中，可用现代 `git merge-tree --write-tree A B` 估计文字合并结果。它使用真实 merge 的内容合并、重命名、目录/文件冲突和多祖先整合能力，不修改工作树或 index，也不创建 commit，**但会写入 Git 对象**。纯只读评估不能未经授权直接在共享对象库运行；linked worktree 通常仍共享对象库。

Git 已弃用三参数的 `--trivial-merge base A B`。该模式能力有限，不支持完整的内容合并、重命名及目录/文件冲突处理，输出难解析；其冲突标记统计不能当作正式合并冲突数或语义成本依据。现代模式的退出码和结构化冲突信息也只能证明 Git 合并层面的状态。[Git merge-tree 官方文档](https://git-scm.com/docs/git-merge-tree)

## 两个有用的研究补充

- **三路语义验证：** [Verified Three-Way Program Merge（OOPSLA 2018）](https://www.microsoft.com/en-us/research/publication/verified-three-way-program-merge/)研究验证组合程序是否引入不希望出现的新行为。借鉴其相对共同基线分析两侧变化、再验证组合的思路。论文中的 SafeMerge 不是本项目已验证的通用解冲器，不要求安装或把其特定实验结论外推到当前仓库。
- **变化影响比较：** [DeltaImpactFinder（2015）](https://arxiv.org/abs/1509.04207)比较一个改动在原分支和目标分支上的影响差异，用来发现潜在语义冲突。借鉴为检查共享消费者、数据和合同：即使两侧修改不同文件，也要核对影响是否相遇。静态依赖未找到交集不保证动态调用、配置或数据库没有交互。

这两点在本 Skill 中的应用是工程判断，不声称已经取得形式化的无冲突证明。AST/结构化合并与针对组合的测试可作辅助；用户意图、权限或外部承诺的互斥仍交给人裁定。

## 用来检验判断的短案例

- A 在一个文件增加凭据传播，B 在另一个文件改变任务归属：没有文字冲突，仍须检查同一消费者的授权合同。
- A 与 B 都修改同一个启动函数，分别装配独立能力：文字冲突本身不构成语义冲突；证明无相互影响后可在合并授权内整合。
- A 要求失效结果永不采用，B 要求同一场景允许采用：明确冲突和后果，交人裁定，不自行选一边或同时保留两个矛盾分支。
- 用户只要求成本评估：交付变化链、关系、缺口和成本，不能通过实际 merge 或跑完整 Gate 来扩大任务。

这些案例用于作者自查和实际使用反馈，不设置按措辞匹配的专用测试或固定评审轮次。
