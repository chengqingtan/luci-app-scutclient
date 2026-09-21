# 来源与边界

- 上游：https://github.com/scutclient/luci-app-scutclient
- 基线：727235341e2cb89150fec7e7b9223ea8fc19058a
- 整理日期：2026-09-21
- 依据：原会话「原厂安装翻墙软件」。未将会话全文和设备私密信息保存进仓库。

原会话的 ImmortalWrt 打包源码与 GitHub 原版不同。本仓库以原版为基线移植验证过的修复方向，未整体复制 plus 版。

可见菜单只由 JSON 管理，固定顺序为状态、设置、日志、关于。旧 mainorder/configured 不控制本版菜单；未添加旧路径 alias。原版遗留 move_tag 行为保留，后续可单独清理。

安装检测改用 Lua 模式解析，避免 sed 的多层转义；fetch 增加 HTTP 错误显示、textarea.value 和串行轮询。这些整理差异需要上机回归。

构建规则参考 https://github.com/immortalwrt/luci/blob/master/luci.mk ，Makefile 引用 SDK 的 feeds/luci/luci.mk，适合独立放入 package/luci-app-scutclient。最终以对应 SDK 为准。
