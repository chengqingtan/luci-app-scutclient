# 来源与边界

- 上游：https://github.com/scutclient/luci-app-scutclient
- 基线：727235341e2cb89150fec7e7b9223ea8fc19058a
- 整理日期：2026-09-21
- 依据：原会话「原厂安装翻墙软件」。未将会话全文和设备私密信息保存进仓库。

原会话的 ImmortalWrt 打包源码与 GitHub 原版不同。本仓库以原版为基线移植验证过的修复方向，未整体复制 plus 版。

可见菜单只由 JSON 管理，固定顺序为状态、设置、日志、关于。旧 mainorder/configured 不控制本版菜单；未添加旧路径 alias。原版遗留 move_tag 行为保留，后续可单独清理。

安装检测改用 Lua 模式解析，避免 sed 的多层转义；fetch 增加 HTTP 错误显示、textarea.value 和串行轮询。这些整理差异需要上机回归。

构建规则参考 https://github.com/immortalwrt/luci/blob/master/luci.mk ，Makefile 引用 SDK 的 feeds/luci/luci.mk，适合独立放入 package/luci-app-scutclient。最终以对应 SDK 为准。

## OpenWrt 的 scutclient 核心打包文件

OpenWrt 25.12.5 与 24.10.8 的发行版 packages feed 均不含 scutclient，因此本仓库仅为 OpenWrt 构建保存以下打包文件，ImmortalWrt 继续使用自己的 SDK feed。

- `vendor/scutclient/Makefile` 和 `vendor/scutclient/patches/010-cmake.patch` 原样取自 [ImmortalWrt packages 固定提交](https://github.com/immortalwrt/packages/tree/84bd86384928955b568988ca0e09e2c78c75173d/net/scutclient)，包版本 `3.1.3-r2`。
- 核心源码为 [scutclient v3.1.3](https://github.com/scutclient/scutclient/tree/v3.1.3)，源码压缩包 SHA256：`5423d3444b950bf5a049d1bb9365b3dc90f4a75fe9bc5aef9239ea08c0b0030a`。
- 补丁将 CMake 最低版本从 2.4 调整为 3.10，以兼容新版 CMake，不修改认证逻辑。
- 该核心及打包文件保留原作者版权与 AGPL-3.0 声明；`vendor/scutclient/COPYING` 保存核心 v3.1.3 的 AGPLv3 许可全文。本仓库 LuCI 部分原有 Apache-2.0 声明不变。
- 工作流不添加整套 ImmortalWrt feed 到 OpenWrt；OpenWrt 的 LuCI、依赖和工具链仍由自己的 SDK 提供。
