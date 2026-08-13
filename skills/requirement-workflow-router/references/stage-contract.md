# 阶段合同

## 短路径

普通问答、状态查询、小修复和已批准路线图内的机械修改不占需求槽位，也不生成空壳阶段材料。

## 完整路径

允许的主路径：

`frame -> research? -> align -> plan -> execute -> close -> closed`

允许的返回：

- `research -> frame`：目标或边界被事实推翻；
- `align -> research`：出现会改变推荐的新未知量；
- `plan -> align`：路线图暴露未解决的业务取舍；
- `execute -> plan`：现实差异只改变执行设计但仍属于原方案；
- `execute -> align`：现实差异改变业务语义、成本、体验、安全、兼容、部署或范围；
- `close -> execute`：实现或验证不完整；
- `close -> align`：验收证明方案本身不成立。

不得跳过：

- 未完成 framing 就广泛调研；
- 未对齐 proposal 就制定可执行路线图；
- 未记录匹配路线图摘要的批准就进入 execution；
- 未满足独立验收就自称 closed。

## 阶段材料

- frame：`需求与边界.md`
- research：`调研结论.md`（只有需要时）
- align：`提案.md`、`决策记录.md`
- plan：`路线图.md`
- execute：产品变更和受控证据；不创建聊天流水文档
- close：`验收.md`

阶段材料只在有内容时创建。它们不保存机械阶段、槽位、owner-generation 或批准有效性。
