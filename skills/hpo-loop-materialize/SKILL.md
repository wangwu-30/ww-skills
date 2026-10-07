---
name: hpo-loop-materialize
description: Writes already-selected candidate values into the reference experiment's full config for the HpoLoopWorkflow capsule. Does not choose values.
---

# HPO Loop Provider Config Materializer

把**已经选定**的候选参数值，填进参考实验原始配置模板对应的槽位，产出一份结构与
模板完全一致的完整 treatment config。

**这项能力不做参数搜索。** 取什么值由搜参 Agent 决定并已经过确定性校验；这里只
负责放对位置。产出会被确定性代码逐条校验：整树结构一致、不可变路径逐字保留、每一
处变化的叶子取值必须精确等于某个候选值、每个候选参数都必须落地。

**代码证明不了的那部分**：没有 parameter→path 映射表时，代码无法证明参数被放到了
语义正确的位置（值写对了但放进了别的槽位，只要两个值都来自候选就看不出来）。那一
关由人在确认卡上对照两份结果和完整 diff 复核。
