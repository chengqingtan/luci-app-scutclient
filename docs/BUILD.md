# SDK 编译与安装

## GitHub Actions

1. 将本仓库源码、`.github/workflows/build-packages.yml` 和 `scripts/` 提交并推送到自己的 GitHub 仓库默认分支。
2. 打开 **Actions → Build scutclient packages → Run workflow**；选择包含所需修改的分支，再选择系统版本和架构。
3. 等待成功，打开该次运行的 **Artifacts**，下载名称以 `scutclient-immortalwrt-` 开头的附件并解压 ZIP。`logs-` 附件用于排错。

工作流仅手动触发；无需 Secrets，权限为 `contents: read`；不创建 Release、不推送提交，也不连接路由器。附件保留 30 天，过期后可重新构建。

| 系统版本 | 软件包格式 |
| --- | --- |
| ImmortalWrt 25.12.2 | APK |
| ImmortalWrt 24.10.6 | IPK |

| 架构 | 选用 SDK target/subtarget |
| --- | --- |
| aarch64_cortex-a53 | mediatek/filogic |
| aarch64_generic | rockchip/armv8 |
| x86_64 | x86/64 |
| mipsel_24kc | ramips/mt7621 |
| mips_24kc | ath79/generic |

选择 `all` 会为所选版本启动五个独立任务，最多两个同时构建，一个失败不会取消其他架构。CPU 架构是系统的软件包 ABI 标识，不能只按芯片品牌判断。这里编译用户态软件包，不含固件、内核或 kmod；表中的 target 是该架构的 SDK 代表目标，不代表支持刷写所有同架构设备。

当前路由器已确认：ImmortalWrt **25.12.2**、target **mediatek/filogic**、架构 **aarch64_cortex-a53**、内核 **6.12.103**。在其他设备上安装前确认：

```sh
cat /etc/openwrt_release
ubus call system board
# 25.12:
apk --print-arch
# 24.10:
opkg print-architecture
```

## 构建行为与附件

工作流从 `downloads.immortalwrt.org` 获取版本匹配的 Linux x86_64 SDK，并使用 `scripts/sdks.json` 固定的 SHA256 校验。保留 SDK 自带 feed URL/版本信息；核心来自官方 packages feed，本仓库的 LuCI 源码覆盖 SDK 的同名包入口。SDK 决定 IPK/APK 格式，不跨版本强制转换。

构建只请求两个目标包及其构建依赖。上传前检查软件包名称、版本、依赖和架构；检查 scutclient 的 ELF 类型及字节序；逐文件比较 LuCI 源码与包内文件。为便于核对，禁用 LuCI 源码压缩。LuCI 包的架构显示 `all` 是正常现象，仍应使用与系统版本匹配的附件。

每个附件包含两个安装包、`build-info.json`、`SHA256SUMS` 和本说明。构建信息记录 SDK、仓库提交、实际 feed 提交和包元数据；其他依赖仍从路由器对应的软件源安装，不是完整离线安装套件。初版不缓存构建目录，避免不同 SDK 的中间产物混用。

Linux 或路由器中进入解压后的附件目录，先校验：

```sh
sha256sum -c SHA256SUMS
```

## 安装

先备份 `/etc/config/scutclient` 和以前手工修改过的 LuCI 文件。将附件中两个安装包传到路由器 `/tmp`，下面的 `ACTUAL_VERSION` 必须替换为实际文件名。若只更新界面而核心已满足依赖，也可只安装 LuCI 包。

ImmortalWrt 25.12.2：

```sh
apk update
apk add --allow-untrusted /tmp/scutclient-ACTUAL_VERSION.apk /tmp/luci-app-scutclient-ACTUAL_VERSION.apk
/etc/init.d/rpcd restart
/etc/init.d/uhttpd restart
```

`--allow-untrusted` 用于这个没有配置路由器信任签名的自编译包，仅用于明确选择的本地文件。不要换用其他系统版本的软件源解决依赖；遇到版本或文件冲突先查看错误，不强制覆盖或降级。

ImmortalWrt 24.10.6：

```sh
opkg update
opkg install /tmp/scutclient_ACTUAL_VERSION_ARCH.ipk /tmp/luci-app-scutclient_ACTUAL_VERSION_all.ipk
/etc/init.d/rpcd restart
/etc/init.d/uhttpd restart
```

重新登录 LuCI，按 `docs/VALIDATION.md` 验证四个页面、日志、配置和校园网认证。编译成功不等于已经通过设备运行测试。

## 本地 Linux 构建

使用 x86_64 Linux 或 WSL2，在 Linux 文件系统中构建。Windows PowerShell、Git Bash 不能执行 SDK 内的 Linux 工具。Ubuntu 24.04 安装依赖：

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends -y \
  build-essential clang flex bison g++ gawk gcc-multilib gettext git \
  libncurses-dev libssl-dev python3 python3-setuptools rsync swig unzip \
  zlib1g-dev file wget curl zstd ca-certificates patch perl tar time xz-utils
```

进入本仓库，工作目录和输出目录都必须尚不存在：

```sh
bash scripts/build-packages.sh 25.12.2 aarch64_cortex-a53 /tmp/scut-sdk-build /tmp/scut-packages
```

结果位于 `/tmp/scut-packages/packages`，日志位于 `/tmp/scut-packages/logs`。重试时选择新的空路径，脚本不删除已有目录。

## 检查与扩展

本地无需 SDK 的检查：

```sh
python3 -m unittest discover -s tests -v
bash -n scripts/build-packages.sh
shellcheck scripts/build-packages.sh
actionlint .github/workflows/build-packages.yml
```

新增版本时，先确认该版本所有目标的官方 SDK；从官方 `sha256sums` 核对文件名、GCC 版本和 SHA256，添加到 `scripts/sdks.json`，再同步工作流版本选项。新增架构还需补充目标映射、ELF 验证表、工作流选项及测试。不要填写未验证的下载地址或用相近架构代替。

首次完整验收：先分别构建两个版本的 `aarch64_cortex-a53`；成功后分别选择两个版本的 `all`，覆盖十个组合。
