# 构建指南

[文档导航](README.md) · [新用户说明](../README.md) · [开发指南](DEVELOPMENT.md) · [验证状态](VALIDATION.md)

本文说明构建流程、SDK 环境和报错诊断。支持的系统与架构、软件下载和路由器安装步骤集中在 [项目首页](../README.md)，避免两处说明不同步。

## GitHub Actions

在自己的仓库启用 Actions，进入 **Build scutclient packages → Run workflow**，选择分支、系统版本及架构。首次配置时，工作流文件需要存在于默认分支。

- 仅手动触发，不需要 Secrets；权限为 `contents: read`，不推送代码、不创建 Release、不连接路由器。
- `prepare` 检查 Python、Lua 和 Shell，并生成所选系统的构建矩阵。
- `build` 为每个架构获取对应 SDK，编译并验证两个包；`all` 当前展开为五个架构，最多五个并行，一个失败不取消其他任务。
- 每个成功架构直接上传两个 APK/IPK 原文件，使用 `archive: false`，保留 30 天。构建日志留在步骤页面，不单独上传。

运行标题包含系统与架构。修改工作流或脚本后，从包含修复的最新提交新建运行；直接重跑旧任务仍使用旧提交。

## SDK 构建流程

[SDK 清单](../scripts/sdks.json) 是版本、架构、下载校验值和兼容配置的来源。[矩阵解析器](../scripts/sdk_matrix.py) 只接受清单中的组合，本地和 Actions 共用同一套选择逻辑。

1. 从对应发行版的官方下载站获取 SDK，先验证固定 SHA256，再按清单指定的 XZ 或 Zstandard 格式解压。
2. 保留 SDK 自带的 feed 地址和修订配置，更新并安装 feeds；检查 Lua 运行时布局是否符合清单。
3. ImmortalWrt 使用对应 packages feed 中的 `scutclient`；OpenWrt 使用本仓库 [vendor/scutclient](../vendor/scutclient/) 的固定打包配方。其余依赖和工具链来自各自 SDK，不混用整套软件源。
4. 将本仓库界面源码放入 SDK，移除 feed 中同名包的链接，避免误编译官方界面。禁用 LuCI 源码压缩，保留可逐文件比较的内容。
5. 依次编译核心和界面目标，避免两者同时写入共享构建依赖。并行编译失败时，自动进行一次串行重试并输出诊断日志。
6. 校验包名、版本、运行依赖及架构，核对核心 ELF 类型和字节序、必要安装文件，并逐文件比较 LuCI 与本仓库源码。两个包都通过后才收集和上传。

脚本不缓存或复用已有工作目录，不生成完整离线依赖套件。实际校验代码见 [verify_packages.py](../scripts/verify_packages.py)，来源见 [PROVENANCE.md](PROVENANCE.md)。

## 本地 SDK 构建

需要 x86_64 Linux；Windows 可使用 WSL2，并将源码与 SDK 放在 Linux 文件系统中。PowerShell 和 Git Bash 不能直接运行 SDK 的 Linux 工具。

| 构建版本 | CI / 本地建议环境 | SDK 压缩格式 |
| --- | --- | --- |
| ImmortalWrt 21.02.7 | Ubuntu 22.04 | XZ |
| 其余当前支持版本 | Ubuntu 24.04 | Zstandard |

安装公共依赖：

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends -y \
  build-essential clang flex bison g++ gawk gcc-multilib gettext git \
  libncurses-dev libssl-dev python3 python3-dev python3-pyelftools python3-setuptools rsync swig unzip \
  zlib1g-dev file wget curl zstd ca-certificates patch perl tar time xz-utils
```

仅构建 21.02.7 时，在 Ubuntu 22.04 额外安装：

```sh
sudo apt-get install --no-install-recommends -y python3-distutils
```

从仓库根目录执行下面适合目标系统的命令。最后两个参数分别为工作目录和输出目录，二者必须尚不存在；重试时换用新的路径。

```sh
# Ubuntu 24.04：ImmortalWrt 示例
bash scripts/build-packages.sh immortalwrt-25.12.2 aarch64_cortex-a53 /tmp/scut-sdk-build /tmp/scut-packages
# Ubuntu 22.04：旧版 ImmortalWrt 示例
bash scripts/build-packages.sh immortalwrt-21.02.7 x86_64 /tmp/scut-2102-build /tmp/scut-2102-packages
# Ubuntu 24.04：OpenWrt 示例
bash scripts/build-packages.sh openwrt-25.12.5 aarch64_cortex-a53 /tmp/scut-openwrt-build /tmp/scut-openwrt-packages
```

第一条命令的产物位于 `/tmp/scut-packages/packages/`，另外两条同样位于各自输出目录的 `packages/` 子目录。结果仅包含两个经过验证的安装包，安装步骤见 [README](../README.md#4-安装到路由器)。

本地脚本一次只构建一个架构；`all` 由 Actions 展开成五个独立任务。纯版本号 `25.12.2` 和 `24.10.6` 保留为早期 ImmortalWrt 命令的别名；新增版本应使用完整发行版标识。

无需 SDK 的检查命令与新增版本步骤见 [开发指南](DEVELOPMENT.md)。

## 旧版 LuCI 兼容

21.02.7 的 `aarch64_cortex-a53` SDK 目标是 `sunxi/cortexa53`，其他当前支持版本使用 `mediatek/filogic`。这些是构建用户态包的代表目标，不是跨设备刷机目标。

| 项目 | ImmortalWrt 21.02.7 | 当前 24.10 / 25.12 构建 |
| --- | --- | --- |
| Lua 支持 | luci-base 的依赖链 | 独立 luci-lua-runtime 包 |
| 设置页调用 | `_cbi` | `invoke_cbi_action` |
| 修订号格式 | `版本-修订号` | `版本-r修订号` |

Makefile 根据 SDK 是否提供独立 Lua 运行时添加依赖，脚本按版本清单检查该布局。旧版 luci.mk 不自动给界面版本追加修订号，因此 Makefile 在旧版路径显式拼接。设置页共用本项目兼容入口，保留提交保护；两个接口均不可用时明确报错。

21.02 核心配方以基础版本、日期和 Git 提交号计算版本，目前对应 `3.1.3-2021-11-26-b265ca8f-1`。校验器按已支持的配方表达式独立计算预期值，不直接信任产物自报的版本；未知表达式仍需明确适配。

## 构建问题排查

| 现象 | 检查与处理 |
| --- | --- |
| `Missing PKG_VERSION`，但日志中已生成 IPK | 旧校验器不能解析 21.02 核心的表达式版本；使用含修复的最新提交启动新运行 |
| `python3-pyelftools` 检查失败 | Rockchip SDK 的全局前置检查可能涉及 U-Boot；在构建机安装 python3-pyelftools 和 python3-dev，不是在路由器上安装 |
| 安装 pyelftools 后仍失败 | 在 SDK 目录运行下方解释器检查，确认 SDK 使用的 Python 能导入模块 |
| `Directory already exists` | 选择新的工作、输出路径；脚本不会删除已有目录 |
| SDK 校验值不符 | 核对清单和官方 sha256sums、重新下载；不要关闭校验 |
| Lua 运行时布局或包依赖不符 | 核对 SDK 版本和 feeds；不要混入另一发行版的软件源或跳过依赖校验 |
| 日志里有很多 warning | 以最终失败步骤及其具体错误定位，不把无关 warning 当作根因 |
| `all` 中部分架构失败 | 下载已成功架构的附件，分别排查失败任务 |

```sh
# 在 SDK 目录执行
staging_dir/host/bin/python3 -c 'import sys; print(sys.executable); import elftools'
```

构建成功只证明已完成该任务的编译与产物检查。设备页面、配置保存、服务行为及真实认证仍按 [验证清单](VALIDATION.md) 验收。
