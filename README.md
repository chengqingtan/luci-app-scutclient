# luci-app-scutclient

用于 ImmortalWrt / OpenWrt 的华南理工大学校园网认证管理界面。本项目基于 [原版 luci-app-scutclient](https://github.com/scutclient/luci-app-scutclient) 整理新版 LuCI 兼容修改，并提供 GitHub Actions，为指定系统和架构构建可安装的软件包。

**已有路由器系统即可安装，无需为使用本项目重新刷机。** 本仓库输出软件包，不输出路由器固件。

## 1. 先了解两个软件包

| 软件包 | 用途 | 什么时候需要安装 |
| --- | --- | --- |
| `scutclient` | 执行校园网认证的核心程序及服务 | 系统尚未安装核心时 |
| `luci-app-scutclient` | 在路由器网页后台管理核心的界面 | 首次使用本界面，或更新为本仓库修改版时 |

本项目没有修改核心的认证逻辑。ImmortalWrt 构建使用对应 SDK feed 中的核心打包规则；OpenWrt 构建使用仓库内固定来源的核心打包文件。界面保留 **状态、设置、日志、关于** 四个页面。

本仓库整理的兼容修改包括：

- 使用 `menu.d` 注册服务菜单，统一使用 `/admin/services/scutclient` 路径。
- 补充 Lua 兼容依赖和 RPCD 访问权限配置，调整 Lua 模块加载与页面 URL 生成。
- 兼容 APK、opkg 和可执行文件的核心安装检测。
- 使用 `fetch` 刷新日志，处理请求错误并避免轮询请求重叠。

源码根据原版和排错记录重建，并非设备最终文件的逐字备份。**提供构建选项不等于所有组合都已通过实机认证测试。** OpenWrt 新增组合仍需实际 SDK 构建和设备验证；已完成检查与验收方法见 [验证记录](docs/VALIDATION.md)。

## 2. 确认系统版本与架构

通过 SSH 登录路由器，执行：

```sh
cat /etc/openwrt_release
```

关注 `DISTRIB_ID`、`DISTRIB_RELEASE` 和 `DISTRIB_ARCH`，分别对应发行版、版本和软件包架构。也可按系统使用的包管理器进一步确认：

```sh
# 25.12 系列使用 APK
apk --print-arch
```

```sh
# 24.10 系列使用 opkg
opkg print-architecture
```

工作流当前提供以下版本：

| 路由器系统 | Actions 中的 release 选项 | 安装包格式 |
| --- | --- | --- |
| ImmortalWrt 25.12.2 | `immortalwrt-25.12.2` | `.apk` |
| ImmortalWrt 24.10.6 | `immortalwrt-24.10.6` | `.ipk` |
| OpenWrt 25.12.5 | `openwrt-25.12.5` | `.apk` |
| OpenWrt 24.10.8 | `openwrt-24.10.8` | `.ipk` |

每个版本均提供五种架构：

| architecture 选项 | 构建使用的 SDK target/subtarget |
| --- | --- |
| `aarch64_cortex-a53` | `mediatek/filogic` |
| `aarch64_generic` | `rockchip/armv8` |
| `x86_64` | `x86/64` |
| `mipsel_24kc` | `ramips/mt7621` |
| `mips_24kc` | `ath79/generic` |

例如，GL.iNet GL-MT3600BE 刷入 ImmortalWrt 25.12.2，且设备输出架构为 `aarch64_cortex-a53` 时，选择 `immortalwrt-25.12.2` 和 `aarch64_cortex-a53`。

请以设备输出为准，不能只根据“ARM64”或芯片品牌选包。同一发行版、系统版本和软件包架构下，这类用户态软件包通常可以跨设备使用，但仍须满足运行库依赖和 ABI 要求。表中的 SDK 目标不是通用刷机目标；该原则也不适用于固件或内核模块。

没有匹配选项时，不要用相近架构或另一发行版的包代替。新增组合的方法见 [构建说明](docs/BUILD.md)。

## 3. 下载或自行构建

### 下载已有构建

打开本仓库的 [Build scutclient packages 工作流](https://github.com/chengqingtan/luci-app-scutclient/actions/workflows/build-packages.yml)，进入版本和架构匹配的成功运行，在 **Artifacts** 中下载对应文件。下载 Actions 附件通常需要登录 GitHub。

每个版本与架构组合返回两个独立文件，命名规则为：

```text
scutclient-包版本-发行版-系统版本-架构.apk/ipk
luci-app-scutclient-包版本-发行版-系统版本-架构.apk/ipk
```

例如界面包可能为：

```text
luci-app-scutclient-26.264.1-r1-immortalwrt-25.12.2-aarch64_cortex-a53.apk
```

附件直接下载为 APK/IPK，无需解压 ZIP。文件名中的架构用于区分构建任务；LuCI 包内部的架构元数据显示为 `all` 是正常的，仍应下载与系统版本匹配的文件。

### 在自己的 GitHub 仓库构建

1. Fork 本仓库，进入自己的仓库。
2. 打开 **Actions**；如 GitHub 提示工作流未启用，先启用。
3. 选择 **Build scutclient packages → Run workflow**。
4. 选择包含所需修改的分支，再选择 `release` 和 `architecture`，点击运行。
5. 等待对应构建任务成功，在该次运行的 **Artifacts** 中下载软件包。

默认选项为 `immortalwrt-25.12.2 / aarch64_cortex-a53`。选择 `all` 会构建五种架构，全部成功时得到十个文件；单次运行最多并行五个架构，一个架构失败不会取消其他架构。实际并发还受 GitHub 账号额度及 runner 可用性影响。

侧栏的工作流名称固定为 **Build scutclient packages**，新运行的标题会包含选择的版本和架构，例如 `Build scutclient · immortalwrt-25.12.2 · all`。

工作流仅手动触发，无需配置 Secrets；不创建 Release、不连接路由器。附件保留 30 天，过期后可重新构建。日志在运行页面的各步骤中查看，不作为下载附件输出。

## 4. 安装到路由器

### 安装前准备

- 首次使用需能登录路由器的 SSH 和 LuCI 网页后台。
- 如已使用 scutclient，先将 `/etc/config/scutclient` 备份到电脑；以前手工修改过的 LuCI 文件也应另行保存。
- 使用 SCP 或 WinSCP 将安装包上传到路由器的 `/tmp`。若设备不支持 SFTP，可使用 SCP 模式。
- 以下命令在**路由器 SSH 终端**执行。将 `ACTUAL_FILENAME` 替换为下载文件中包名之后的完整后缀，包括包版本、发行版、系统版本和架构。

下面的常规安装方法要求路由器可访问其对应的软件源，以获取尚未安装的依赖。完全离线的情况见下一节。

### 25.12 系列：安装 APK

ImmortalWrt 和 OpenWrt 均需使用各自对应的包：

```sh
apk update
apk add --allow-untrusted /tmp/scutclient-ACTUAL_FILENAME.apk /tmp/luci-app-scutclient-ACTUAL_FILENAME.apk
```

`--allow-untrusted` 用于安装尚未配置路由器信任签名的自编译本地包，请仅用于确认来源的文件。

### 24.10 系列：安装 IPK

```sh
opkg update
opkg install /tmp/scutclient-ACTUAL_FILENAME.ipk /tmp/luci-app-scutclient-ACTUAL_FILENAME.ipk
```

如果系统已安装满足依赖的 `scutclient`，上述安装命令可以只保留 `luci-app-scutclient` 的文件路径，无需重复安装核心。

### 安装成功后

确认包管理器没有报错，再执行以下命令刷新后台服务，然后重新登录 LuCI：

```sh
/etc/init.d/rpcd restart
/etc/init.d/uhttpd restart
```

如出现缺少依赖、版本或文件冲突，先处理具体错误。不要通过混用其他版本软件源、忽略依赖或强制覆盖来继续安装。

## 5. 没有网络时怎样安装

**本地安装核心包本身并不必然要求联网。** 如果依赖已经在系统中，安装上传的 APK/IPK 可以离线完成；按包名执行 `apk add scutclient` 等命令，则通常需要从软件源下载包。

自定义 LuCI 包声明的直接依赖为：

```text
scutclient
luci-compat
luci-lib-nixio
luci-lua-runtime
```

这些依赖还可能依赖其他软件包。当前 Actions 只提供核心和界面两个文件，**尚未收集完整的离线依赖套件**。

可根据实际情况选择：

| 情况 | 安装方式 |
| --- | --- |
| 路由器可临时联网 | 按上一节安装，让包管理器获取缺少的依赖 |
| 核心和 LuCI 所需依赖都已预装 | 只上传并安装自定义 LuCI 包，无需执行 `apk update` / `opkg update` |
| 完全离线且缺少依赖 | 先准备匹配系统的完整依赖包，或在计划制作固件时预装它们；仅有本项目的两个文件不足以保证安装成功 |

如果本来就准备通过 [ImmortalWrt Firmware Selector](https://firmware-selector.immortalwrt.org/) 定制固件，可以在正确设备、版本的默认软件包列表后**追加**：

```text
scutclient luci-compat luci-lib-nixio luci-lua-runtime
```

保留原有默认包，由固件构建服务解析依赖。这样可将未修改的核心及界面依赖预装进固件，之后再安装本仓库的自定义 LuCI 包；无需同时添加官方 `luci-app-scutclient`。是否能构建，以所选版本的软件源和构建服务结果为准。

这个方法用于已有刷机计划的 ImmortalWrt 用户，并非本项目的安装前提。当前支持的两个 OpenWrt 版本，其原生 packages feed 不含 `scutclient`，不能直接照搬这个核心预装步骤。

## 6. 首次配置与使用

1. 打开 LuCI 的 **服务 → 华南理工大学客户端 → 设置**。
2. 填写校园网账号和密码，启用客户端并保存应用。
3. 认证服务器、客户端版本等参数按所在网络要求填写；没有明确要求时先保留默认值。
4. 在 **状态** 页检查运行与认证情况，在 **日志** 页查看失败原因。

若保存配置后服务未启动，可通过 SSH 执行：

```sh
/etc/init.d/scutclient enable
/etc/init.d/scutclient restart
```

菜单对应路径为 `/cgi-bin/luci/admin/services/scutclient`。例如路由器地址为 `192.168.1.1` 时，可访问 `http://192.168.1.1/cgi-bin/luci/admin/services/scutclient`。

本界面负责管理认证客户端，仍需先正确设置路由器的 WAN 接线和网络配置。页面能打开或软件包能安装，并不代表校园网认证已经成功。

**分享排错资料前请脱敏：原版保留的状态页会显示账号、密码，调试包也可能包含设备配置。** 不要公开完整截图、配置文件或未经检查的调试压缩包。

## 7. 常见问题

### 安装后找不到菜单

先确认两个包已正确安装、`/etc/config/scutclient` 存在，并完成上面的后台服务重启及重新登录。菜单依赖该配置文件和 RPCD 权限；核心安装失败时，单独复制界面文件不能解决问题。继续排查可参考 [验证清单](docs/VALIDATION.md)。

### 重启路由器会回到旧版本吗

正常通过包管理器安装后，文件保存在可写系统分区，普通重启通常不会回滚。`/tmp` 中的安装包和日志会丢失，但不影响已经安装的程序。恢复出厂、重刷固件或系统升级是不同操作，可能清除或替换自定义包，需要重新安装。

### 同名官方界面已经安装了，怎么办

本项目仍使用 `luci-app-scutclient` 包名，作为同名包进行安装或升级，不会生成第二套独立界面。先备份配置，比较已安装版本和待安装版本。当前自定义版本为 `26.264.1-r1`，不保证高于未来官方版本；遇到拒绝降级或文件冲突时，应先核对版本和文件来源。

### APK 是 Android 应用吗

这里的 APK 是路由器 `apk` 包管理器使用的软件包，不是 Android 应用。APK 与 IPK 也不能通过修改扩展名互换。

### all 构建中只有一个架构失败

成功架构的文件可分别下载。展开失败任务，查找实际的 `error` 和最终失败步骤，不能仅凭前面的 warning 判断原因。

例如 `aarch64_generic` 的 Rockchip SDK 可能触发 U-Boot 宿主依赖检查；`python3-pyelftools` 缺失应在构建机上解决，工作流已补充该依赖。更多诊断见 [构建说明](docs/BUILD.md)。

## 8. 本地开发与进一步阅读

源码可以在 Windows 或 macOS 上编辑。执行 SDK 构建需要 x86_64 Linux 环境；Windows 可使用 WSL2 并在 Linux 文件系统内构建，PowerShell 和 Git Bash 不能直接运行 SDK 内的 Linux 工具。依赖安装、本地构建命令和扩展版本的方法见 [SDK 构建说明](docs/BUILD.md)。

| 路径 | 内容 |
| --- | --- |
| [Makefile](Makefile) | 自定义 LuCI 包版本、依赖与打包入口 |
| [luasrc/](luasrc/) | 控制器、设置模型和页面模板 |
| [root/](root/) | 菜单、RPCD 权限和安装初始化文件 |
| [.github/workflows/build-packages.yml](.github/workflows/build-packages.yml) | Actions 选项与构建任务 |
| [scripts/](scripts/) | SDK 清单、构建和产物校验脚本 |
| [vendor/scutclient/](vendor/scutclient/) | OpenWrt 构建使用的核心打包文件及许可 |
| [docs/BUILD.md](docs/BUILD.md) | 完整构建、安装与故障诊断说明 |
| [docs/VALIDATION.md](docs/VALIDATION.md) | 验证记录和设备验收清单 |
| [docs/PROVENANCE.md](docs/PROVENANCE.md) | 修改来源、上游基线与许可边界 |

维护自己的版本时，先 Fork，再通过 SSH 克隆自己的仓库：

```sh
git clone git@github.com:YOUR_GITHUB_USERNAME/luci-app-scutclient.git
cd luci-app-scutclient
git remote -v
```

将 `YOUR_GITHUB_USERNAME` 替换为自己的 GitHub 用户名，并确保已配置 GitHub SSH key。提交和推送前使用 `git diff` 检查修改、确认远程地址指向自己的仓库；不要提交真实账号、密码或设备配置。

## 来源与许可

LuCI 界面基于 [scutclient/luci-app-scutclient](https://github.com/scutclient/luci-app-scutclient)，保留原作者版权和 Apache-2.0 声明。核心来自 [scutclient/scutclient](https://github.com/scutclient/scutclient)，按 AGPL-3.0 许可；OpenWrt 构建所用打包文件来源和 CMake 兼容补丁见 [来源说明](docs/PROVENANCE.md)，核心许可全文见 [COPYING](vendor/scutclient/COPYING)。
