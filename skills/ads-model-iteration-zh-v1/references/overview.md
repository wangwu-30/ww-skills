# 广告模型迭代参考资料

本文件是本技能完整知识集的导航页。

## 参考资料索引

- [stages.md](./stages.md)
  - 用于了解 `recall / rough rank / final rank / mix rank`
  - 说明各阶段目标、常见方法、关键取舍和常见错误
- [pipeline-and-serving.md](./pipeline-and-serving.md)
  - 用于了解特征系统、样本基础、数据流、在线服务和上线链路
  - 涵盖 `slot / FID / instance`、特征演进、`fast emit`、`Marine / Viking / Pilot / online PS`
- [objectives-and-methods.md](./objectives-and-methods.md)
  - 用于目标设计和方法选择
  - 涵盖 `CTR / CVR / PVR`、深度价值目标、`LTR`、`RECPM`、多任务学习、`Feature Mask`、`Meta Learning`、聚类和不确定性
- [special-topics.md](./special-topics.md)
  - 用于延迟反馈、冷启动、预测偏差、校准、稳定性和效率
- [tuning-and-validation.md](./tuning-and-validation.md)
  - 用于解释参数、诊断回归、解读实验和确定调参流程

## 快速路由

问题主要涉及以下内容时：

- 阶段职责或链路中的角色：读取 [stages.md](./stages.md)；
- 训练数据、特征栈或在线架构：读取 [pipeline-and-serving.md](./pipeline-and-serving.md)；
- 如何选择目标或方法类别：读取 [objectives-and-methods.md](./objectives-and-methods.md)；
- 延迟反馈、冷启动、校准、稳定性或效率：读取 [special-topics.md](./special-topics.md)；
- 下一步调什么、参数是什么意思或如何验证：读取 [tuning-and-validation.md](./tuning-and-validation.md)。

## 使用说明

默认不要加载全部参考资料。

- 从用户问题所属类别开始；
- 只加载准确回答问题所需的文件；
- 如果问题同时涉及阶段、方法和验证，只读准确回答所需的最少文件。
