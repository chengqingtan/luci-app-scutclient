# 2026 年 9 月验证历史

[文档导航](../README.md) · [当前验证状态](../VALIDATION.md)

本文件保留目录整理前的验证记录。以下测试数量、版本状态、“未提交/推送”等描述均对应记录当时，不代表当前状态；后续结果请更新当前验证状态，并另行追加带提交号的历史记录。


## 21.02.7 首次 Actions 日志反馈与版本校验修复

- 用户提供的 aarch64_cortex-a53 日志显示 LuCI 已生成 `luci-app-scutclient_26.264.1-2_all.ipk`，随后产物校验在读取核心 Makefile 时退出：`Missing PKG_VERSION`。本次失败发生在编译后的校验环节，尚未通过最终产物验收。
- 原因：21.02 核心配方的 PKG_VERSION 是 `$(PKG_BASE_VERSION)-$(PKG_SOURCE_DATE)-$(call version_abbrev,$(PKG_SOURCE_VERSION))`，原解析器仅接受单个无空白字符串，遗漏了这种格式。相同配方供五种架构使用，因此其他 21.02.7 架构也可能触发同一错误。
- 校验器现支持该已知表达式，从配方独立计算版本并按 21.02 SDK 规则取提交号前八位；当前官方配方对应 `3.1.3-2021-11-26-b265ca8f-1`。固定版本规则保持不变，未知表达式、缺失字段及版本不匹配仍报错，不以包内自报版本代替预期值。
- 14 项离线测试通过；五个旧版架构的产物收集用例改用真实配方形式和独立写明的预期版本，并增加缺失字段、无效日期/提交号、未知表达式及错误版本测试。此前的简单版本模拟数据未覆盖此次缺陷。
- 本地未重新执行 Linux SDK 构建。推送修复后应从最新提交启动 `immortalwrt-21.02.7 / all`，重新验收五种架构；重跑旧提交的失败任务不会加载这次修改。

配方来源：[21.02 scutclient Makefile](https://github.com/immortalwrt/packages/blob/openwrt-21.02/net/scutclient/Makefile)；提交号缩写规则：[21.02.7 rules.mk](https://github.com/immortalwrt/immortalwrt/blob/v21.02.7/rules.mk)。

## 2026-09-23 ImmortalWrt 21.02.7 支持

- 已新增五种架构及 all，保留原有四个系统版本；共 25 个构建组合。21.02.7 使用 GCC 8.4.0、XZ SDK 和 Ubuntu 22.04，其余版本保持原有 SDK、压缩格式和 Ubuntu 24.04。
- 五个官方 SDK 文件名、SHA256 及 profiles.json 的 arch_packages 已核对；aarch64_cortex-a53 映射为 sunxi/cortexa53，其余为 rockchip/armv8、x86/64、ramips/mt7621、ath79/generic。
- 13 项 Python 离线测试通过，覆盖全部组合、50 个模拟产物的收集、版本和依赖拒绝、ELF 字节序、文件内容比对及菜单提交保护。GNU make 实际解析测试验证旧新版运行时依赖和 LuCI 版本计算。
- Lua 5.1 执行设置页模拟测试：新版入口优先、旧版 _cbi 回退、接口缺失报错均通过；两个源码 Lua 文件及测试文件的语法检查通过。
- Actionlint、ShellCheck、Bash 语法检查和 git diff --check 通过。
- 本地 Lua 5.1.5 从官方源码构建，源码 SHA256 已核对。模拟接口测试不能替代真实 LuCI 页面测试。
- 原版 21.02 luci.mk 不自动将 PKG_RELEASE 加到界面包版本中，本仓库在旧版路径显式拼接，预期界面包为 26.264.1-2；24.10/25.12 仍为 26.264.1-r2。
- 本次环境为 Windows，没有可用 WSL/Linux 构建环境；没有运行真实 SDK 编译、GitHub Actions 或设备安装。未提交、推送或发布。

| 验收项目 | 当前状态 |
| --- | --- |
| 21.02.7 五架构选项、下载元数据、离线校验 | 已检查 |
| 21.02.7 / x86_64 实际 SDK 编译 | 待 Linux / GitHub runner 执行 |
| 21.02.7 其余四架构实际 SDK 编译 | 待 x86_64 验收后执行，可用 all 覆盖 |
| 现有四个系统版本各一个代表架构的 SDK 回归 | 待执行 |
| 21.02.7 设备安装、四页访问、配置保存、服务启停、日志刷新 | 待设备验证 |
| 真实校园网认证 | 待校园网环境验证 |

以下为历史检查记录，所记构建状态对应当时的源码与环境。

## 原会话的设备反馈

| 项目 | 状态 |
| --- | --- |
| 服务菜单、页面入口 | 用户明确确认菜单和界面恢复 |
| APK 安装检测 | 有包输出与后续修复反馈 |
| get_log、日志刷新 | 用户明确确认日志功能恢复 |
| 下线/重拨 | 路径已整理，缺独立成功操作反馈 |
| netstat、调试包下载 | 待验证 |
| 校园网认证 | 当时未配置认证信息，No Response 不代表 UI 故障 |

## 本仓库待验收

静态检查不能替代 SDK 编译和 LuCI 运行。

- [ ] 匹配 SDK 编译 APK，核对版本、依赖。
- [ ] 安装、重新登录后四页均可打开。
- [ ] 安装版本显示正确，无 WAN/无 IP 时页面正常。
- [ ] 设置保存和应用正确，服务按预期应用配置。
- [ ] 下线、重拨生效，无旧路径 404。
- [ ] 日志初始加载、刷新、错误显示正常；中文编码实测（上游声明 GBK，fetch.text 使用 UTF-8）。
- [ ] netstat 在无网络、未登录、已联网时返回合理 JSON。
- [ ] 调试包下载可解压。
- [ ] 配置真实参数后完成校园网认证。

保留的上游行为：下线/重拨使用 GET，状态页显示配置密码，调试包包含完整配置，网络探测依赖外部 HTTP 服务和旧 XHR。这些未重构，后续可逐项改进。调试包不应公开上传。

## 2026-09-21 本地检查结果

7 个 Lua/模板/JSON 文件通过 Lua 5.1 或 JSON 语法解析，模板内 JavaScript 语法通过。模拟日志 fetch 成功和 HTTP 503：文本正确写入、错误可见、每次完成后安排一次 3 秒刷新。git diff --check 通过。未运行 SDK 编译、真实 LuCI 或路由器认证测试。

## 2026-09-22 Actions 实现检查

- 7 项离线测试通过：十个 SDK 组合选择、未知输入拒绝、IPK 元数据/文件读取、版本和依赖拒绝、ELF 架构/字节序校验、原版页面替换检测、源码 JSON 解析。
- Actionlint 1.7.12、ShellCheck 0.11.0、Bash 语法检查和 `git diff --check` 通过。
- 两个版本 × 五个架构的 SDK 文件名与 SHA256 均已逐项比对官方 `sha256sums`。
- 尚未执行 GitHub Actions 或实际 SDK 编译；当前 Windows 环境没有可用的 WSL/Linux runner。测试使用合成 IPK/ELF 数据，不能替代真实 APK/IPK 和依赖构建验证。
- 工作流上传前会用 SDK 的 apk 工具或 IPK 解析器检查实际产物；此环节及路由器安装测试仍待首次运行验收。

| 构建验收 | 状态 |
| --- | --- |
| 25.12.2 / aarch64_cortex-a53 | 待 GitHub runner 执行 |
| 24.10.6 / aarch64_cortex-a53 | 待 GitHub runner 执行 |
| 25.12.2 / all | 待前述单架构验证后执行 |
| 24.10.6 / all | 待前述单架构验证后执行 |

## OpenWrt 25.12.5 / 24.10.8 支持扩展

- 新增 OpenWrt 十个 SDK 组合，文件名和 SHA256 已逐项核对官方下载目录；原有 ImmortalWrt 清单保持一致。
- scutclient 打包文件和 CMake 补丁与固定 ImmortalWrt 提交的 Git blob 一致；下载 v3.1.3 核心源码后核对 SHA256，并通过补丁应用检查。
- 9 项离线测试通过，覆盖四个系统版本 × 五种架构的选择、两个核心来源路径、产物收集与命名；每个组合仅产生两个原文件，各组合文件名不冲突。原有纯版本号 CLI 别名继续选择 ImmortalWrt，错误发行版/版本组合会被拒绝。
- 产物收集测试使用合成 IPK/ELF，APK 解码在测试中模拟；这些测试不代表已生成真实可安装的 OpenWrt 包。
- Actionlint、ShellCheck、Bash 语法检查和 `git diff --check` 通过。
- 新增两个 OpenWrt 版本尚未运行 GitHub SDK 构建或路由器安装验证：先分别运行 `aarch64_cortex-a53`，再分别运行 `all`，之后进行 LuCI 和认证功能上机回归。
