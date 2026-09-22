# luci-app-scutclient：ImmortalWrt 25 兼容版

基于 [scutclient/luci-app-scutclient](https://github.com/scutclient/luci-app-scutclient)，保留状态、设置、日志、关于四个页面。核心认证程序使用对应 ImmortalWrt 官方 feed 的 scutclient 源码，Actions 可同时编译核心与本仓库修改后的界面。

已整理：函数内 local require、服务菜单 JSON、APK/opkg/可执行文件安装检测、分段 build_url、新路径、fetch 日志刷新、Lua 兼容依赖和 RPCD ACL。

**这是根据原会话重建的源码，不是设备最终文件的逐字备份；尚未完成本仓库 SDK 编译和上机回归。** 详见 [验证记录](docs/VALIDATION.md)、[构建说明](docs/BUILD.md)、[来源](docs/PROVENANCE.md)。

## GitHub Actions 构建

在自己的仓库 **Actions → Build scutclient packages → Run workflow** 中选择：

- 系统版本：ImmortalWrt `25.12.2`（APK）或 `24.10.6`（IPK）。
- CPU 架构：`aarch64_cortex-a53`、`aarch64_generic`、`x86_64`、`mipsel_24kc`、`mips_24kc`，或 `all`。

默认为当前路由器对应的 `25.12.2 / aarch64_cortex-a53`。每个组合产生一个包含 **scutclient + luci-app-scutclient** 的下载附件；只手动构建，不自动发布 Release。附件保留 30 天，详细日志单独保存。

首次使用需将工作流提交并推送到 GitHub 默认分支；fork 仓库可能还需在 Actions 页启用工作流。完整步骤、安装命令与新增版本方法见 [构建说明](docs/BUILD.md)。完整 SDK 编译与上机验收状态见 [验证记录](docs/VALIDATION.md)。

## Git / GitHub

个人仓库为 [chengqingtan/luci-app-scutclient](https://github.com/chengqingtan/luci-app-scutclient)，本地保留原版历史。提交或推送前用 `git remote -v` 确认目标为自己的仓库。

后续用 git diff 审阅、git add / git commit 保存修改。不要提交真实账号、密码、设备配置或调试包。

包名保持 luci-app-scutclient，自定义版本为 26.264.1-r1；不承诺高于未来官方版本，安装前检查设备版本。上游 Makefile 声明 Apache-2.0，原作者版权注释保留。
