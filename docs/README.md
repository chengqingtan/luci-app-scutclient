# 文档导航

[返回项目首页](../README.md)

| 想完成的事情 | 阅读入口 |
| --- | --- |
| 了解功能、选择系统和架构、下载和安装 | [新用户说明](../README.md) |
| 使用 Actions 或本地 SDK 构建、排查构建错误 | [构建指南](BUILD.md) |
| 找到要修改的文件、运行检查、维护 Git 仓库 | [开发与目录指南](DEVELOPMENT.md) |
| 确认哪些检查已完成、安排 SDK 与设备验收 | [当前验证状态](VALIDATION.md) |
| 核对上游来源、核心打包文件和许可证 | [来源与许可](PROVENANCE.md) |
| 回顾早期排错及验证结果 | [2026 年 9 月验证历史](history/VALIDATION-2026-09.md) |

## 文档维护约定

- README 面向使用者，集中维护选包、安装、离线使用和常见问题。
- BUILD 面向构建者，维护 SDK 流程、环境、命令和故障诊断；不重复整套安装说明。
- DEVELOPMENT 维护目录职责、源码到安装路径的映射、检查命令和版本扩展步骤。
- VALIDATION 维护当前证据与待验证项；历史日志放入 history，明确对应的提交或阶段。
- PROVENANCE 维护来源、版权和第三方打包边界。

版本、架构和 SDK 校验值以 [SDK 清单](../scripts/sdks.json) 为准，Actions 的选项与行为以 [工作流](../.github/workflows/build-packages.yml) 为准，界面版本与依赖以 [Makefile](../Makefile) 为准。修改这些文件时，同步相关说明；文档中的示例和历史记录不能代替构建配置。
