# SDK 编译与安装

## GitHub Actions

1. 将本仓库源码、`.github/workflows/build-packages.yml`、`scripts/` 和 `vendor/` 提交并推送到自己的 GitHub 仓库默认分支。
2. 打开 **Actions → Build scutclient packages → Run workflow**；选择包含所需修改的分支，再选择系统版本和架构。
3. 等待成功，打开该次运行的 **Artifacts**，分别下载 `scutclient-…apk/ipk` 和 `luci-app-scutclient-…apk/ipk`。使用 `upload-artifact v7` 的 `archive: false` 直接上传原文件，无需解压 ZIP。

工作流仅手动触发；无需 Secrets，权限为 `contents: read`；不创建 Release、不推送提交，也不连接路由器。附件保留 30 天，过期后可重新构建。

| 系统版本选项 | 软件包格式 |
| --- | --- |
| immortalwrt-25.12.2 | APK |
| immortalwrt-24.10.6 | IPK |
| immortalwrt-21.02.7 | IPK |
| openwrt-25.12.5 | APK |
| openwrt-24.10.8 | IPK |

默认仍为 `immortalwrt-25.12.2`。系统与版本绑定为一个选项，避免误用另一发行版的 SDK。请按设备实际安装的发行版选择，不要仅比较版本号或 CPU。

| 架构 | 选用 SDK target/subtarget |
| --- | --- |
| aarch64_cortex-a53 | 21.02.7：sunxi/cortexa53；其他版本：mediatek/filogic |
| aarch64_generic | rockchip/armv8 |
| x86_64 | x86/64 |
| mipsel_24kc | ramips/mt7621 |
| mips_24kc | ath79/generic |

选择 `all` 会为所选版本启动五个独立任务，允许五个架构同时构建，一个失败不会取消其他架构。此上限针对单次运行的构建矩阵；实际并行数量仍受账号额度和 runner 可用性影响。CPU 架构是系统的软件包 ABI 标识，不能只按芯片品牌判断。这里编译用户态软件包，不含固件、内核或 kmod；表中的 target 是该架构的 SDK 代表目标，不代表支持刷写所有同架构设备。

当前路由器已确认：ImmortalWrt **25.12.2**、target **mediatek/filogic**、架构 **aarch64_cortex-a53**、内核 **6.12.103**。在其他设备上安装前确认：

```sh
cat /etc/openwrt_release
ubus call system board
# 25.12:
apk --print-arch
# 24.10 / 21.02:
opkg print-architecture
```

## 构建行为与附件

工作流按所选发行版从 `downloads.immortalwrt.org` 或 `downloads.openwrt.org` 获取版本匹配的 Linux x86_64 SDK，并使用 `scripts/sdks.json` 固定的 SHA256 校验。保留 SDK 自带 feed URL/版本信息；本仓库的 LuCI 源码覆盖 SDK 的同名包入口。SDK 决定 IPK/APK 格式，不跨版本强制转换。

ImmortalWrt 的核心继续来自对应官方 packages feed。OpenWrt 这两个版本的 packages feed 没有 scutclient，脚本把 `vendor/scutclient` 复制到 SDK 的 `package/scutclient`，编译固定的 `3.1.3-r2`：包含来自固定 ImmortalWrt 提交的 Makefile 和 CMake 补丁，核心源码下载仍校验 `PKG_HASH`。只导入该包，不混入 ImmortalWrt 的其他 feeds；LuCI、运行库和工具链使用对应 OpenWrt SDK。来源和许可见 `docs/PROVENANCE.md`。

构建只请求两个目标包及其构建依赖。上传前检查软件包名称、版本、依赖和架构；检查 scutclient 的 ELF 类型及字节序；逐文件比较 LuCI 源码与包内文件。为便于核对，禁用 LuCI 源码压缩。LuCI 包的架构显示 `all` 是正常现象，仍应使用与系统版本匹配的附件。

每个版本/架构仅上传两个安装包，不附带日志、校验清单或说明文件。文件名格式为 `包名-包版本-发行版-系统版本-目标架构.apk/ipk`，例如 `luci-app-scutclient-26.264.1-r2-openwrt-25.12.5-aarch64_cortex-a53.apk`。目标架构后缀用于区分构建任务，不改变 LuCI 包内部的 `all` 架构元数据。选择 `all` 时共返回十个安装包。

SDK 校验和包内容检查仍在上传前执行，失败时不会上传未验证的包。构建日志在 Actions 对应 job 的步骤中查看，不单独上传附件。其他运行依赖仍从路由器对应的软件源安装，不是完整离线安装套件；不缓存构建目录，避免不同 SDK 的中间产物混用。

## 安装

先备份 `/etc/config/scutclient` 和以前手工修改过的 LuCI 文件。将下载的两个安装包传到路由器 `/tmp`，下面的 `ACTUAL_FILENAME` 必须替换为实际文件名中的完整后缀（包含包版本、系统版本和架构）。若只更新界面而核心已满足依赖，也可只安装 LuCI 包。

ImmortalWrt 25.12.2 / OpenWrt 25.12.5（选用对应发行版的 APK）：

```sh
apk update
apk add --allow-untrusted /tmp/scutclient-ACTUAL_FILENAME.apk /tmp/luci-app-scutclient-ACTUAL_FILENAME.apk
/etc/init.d/rpcd restart
/etc/init.d/uhttpd restart
```

`--allow-untrusted` 用于这个没有配置路由器信任签名的自编译包，仅用于明确选择的本地文件。不要换用其他系统版本的软件源解决依赖；遇到版本或文件冲突先查看错误，不强制覆盖或降级。

ImmortalWrt 21.02.7 / 24.10.6 / OpenWrt 24.10.8（选用对应发行版、版本的 IPK）：

```sh
opkg update
opkg install /tmp/scutclient-ACTUAL_FILENAME.ipk /tmp/luci-app-scutclient-ACTUAL_FILENAME.ipk
/etc/init.d/rpcd restart
/etc/init.d/uhttpd restart
```

重新登录 LuCI，按 `docs/VALIDATION.md` 验证四个页面、日志、配置和校园网认证。编译成功不等于已经通过设备运行测试。

## 本地 Linux 构建

使用 x86_64 Linux 或 WSL2，在 Linux 文件系统中构建。Windows PowerShell、Git Bash 不能执行 SDK 内的 Linux 工具。21.02.7 的 CI 使用 Ubuntu 22.04，其他版本使用 Ubuntu 24.04。本地也使用对应 Ubuntu 版本，先安装公共依赖：

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends -y \
  build-essential clang flex bison g++ gawk gcc-multilib gettext git \
  libncurses-dev libssl-dev python3 python3-dev python3-pyelftools python3-setuptools rsync swig unzip \
  zlib1g-dev file wget curl zstd ca-certificates patch perl tar time xz-utils
```

仅构建 21.02.7 时，在 Ubuntu 22.04 额外安装 `sudo apt-get install -y python3-distutils`。

进入本仓库，工作目录和输出目录都必须尚不存在：

```sh
bash scripts/build-packages.sh immortalwrt-25.12.2 aarch64_cortex-a53 /tmp/scut-sdk-build /tmp/scut-packages
# 21.02.7 示例，在 Ubuntu 22.04 中使用新的目录：
bash scripts/build-packages.sh immortalwrt-21.02.7 x86_64 /tmp/scut-2102-build /tmp/scut-2102-packages
# OpenWrt 示例，使用另两个尚不存在的目录：
bash scripts/build-packages.sh openwrt-25.12.5 aarch64_cortex-a53 /tmp/scut-openwrt-build /tmp/scut-openwrt-packages
```

原本只写 `25.12.2` 或 `24.10.6` 的本地命令仍作为 ImmortalWrt 的别名接受；OpenWrt 必须明确写 `openwrt-` 前缀。

结果位于 `/tmp/scut-packages/packages`，目录中只有两个安装包；构建过程输出到终端。重试时选择新的空路径，脚本不删除已有目录。

`aarch64_generic` 使用 Rockchip SDK，其全局软件包前置检查可能触发 U-Boot 的宿主依赖检查，即使本次只请求 scutclient 软件包。若出现 `Checking 'python3-pyelftools'... failed`，需要在构建机安装 `python3-pyelftools`，不是在路由器上安装。上面的依赖列表已包含它及 `python3-dev`。若安装后仍失败，检查 SDK 实际使用的解释器：在 SDK 目录运行 `staging_dir/host/bin/python3 -c 'import sys; print(sys.executable); import elftools'`，确认没有选到缺少该模块的其他 Python 环境。

## 检查与扩展

本地无需 SDK 的检查（需要 Python 3.9+ 和 GNU make；Windows 可使用 mingw32-make）：

```sh
python3 -m unittest discover -s tests -v
# 设置页模拟测试和源码语法检查需要 Lua 5.1（Ubuntu 包名 lua5.1）
lua5.1 tests/test_settings.lua
find luasrc -name '*.lua' -print0 | xargs -0 -r -n1 luac5.1 -p
bash -n scripts/build-packages.sh
shellcheck scripts/build-packages.sh
actionlint .github/workflows/build-packages.yml
```

新增版本时，先确认该版本所有目标的官方 SDK；从官方 `sha256sums` 核对文件名、GCC 版本和 SHA256，以 `发行版-版本` 为键添加到 `scripts/sdks.json`，填写 `compression`（xz/zst）、`version_style`（revision/revision-r）、`runner` 和 `luci_runtime`（builtin/split），再同步工作流版本选项。新增架构还需补充目标映射、ELF 验证表、工作流选项及测试。不要填写未验证的下载地址或用相近架构代替。

新增 OpenWrt 首次验收：先分别构建两个 OpenWrt 版本的 `aarch64_cortex-a53`；成功后分别选择 `all`，覆盖新增十个组合。原有 ImmortalWrt 两个版本保持十个组合，加上 ImmortalWrt 21.02.7 五个组合，共二十五个构建组合。离线测试不能替代 SDK 构建和设备安装验证。

## ImmortalWrt 21.02.7 兼容细节

21.02.7 使用官方 GCC 8.4.0 的 `.tar.xz` SDK，文件名与 SHA256 固定在清单中；现有版本仍使用 `.tar.zst`。SDK 先通过 SHA256 校验，再按声明的格式解压。五种架构均已核对官方 `profiles.json` 的 `arch_packages`；21.02.7 没有 mediatek/filogic，使用 sunxi/cortexa53 构建 aarch64_cortex-a53 用户态包，不提供跨设备固件。

核心仍使用 SDK 对应 feed 中的 scutclient。LuCI Makefile 根据 SDK 是否提供 `modules/luci-lua-runtime/Makefile` 添加独立运行时依赖，脚本同时检查实际 feed 布局是否符合版本清单，异常则停止。21.02.7 的直接依赖为 scutclient、luci-compat、luci-lib-nixio，Lua 支持由旧版 luci-base 依赖链提供。

设置页统一调用本项目的兼容入口，优先使用新版 `invoke_cbi_action`，旧版使用 `_cbi`；保留 `cbi.submit` 提交保护。两个接口都不存在时明确报错。源码仅维护一份，安装包仍逐文件比对仓库源码。

21.02.7 的包版本遵循 `版本-修订号`，例如 LuCI `26.264.1-2`；其他已支持版本遵循 `版本-r修订号`。旧版 luci.mk 不自动拼接修订号，因此本仓库 Makefile 在旧版路径显式拼接，避免更新丢失修订号。校验器按所选系统检查版本和依赖，不把两种格式无条件视为等价，也不允许旧版产物误依赖 luci-lua-runtime。

首次验收：先运行 `immortalwrt-21.02.7 / x86_64`，再验证其余四个架构（可用 all 覆盖）；现有四个系统版本各运行一个代表架构做回归。支持构建选项不等于已编译成功；实际进度和设备验收状态见 [验证记录](VALIDATION.md)。

21.02 的核心配方采用基础版本、源码日期和 Git 提交号生成版本，当前对应 `3.1.3-2021-11-26-b265ca8f-1`，与较新版的固定 `3.1.3-rN` 格式不同。校验脚本按配方计算该版本；若旧工作流在编译后报 `Missing PKG_VERSION`，需推送包含解析修复的提交，并通过 Run workflow 发起新运行，不能仅重跑旧提交。
