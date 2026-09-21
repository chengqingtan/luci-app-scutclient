# SDK 编译与安装

## 确认目标

设备执行 cat /etc/openwrt_release、ubus call system board、apk --print-arch 和 apk list --installed luci-app-scutclient。

历史记录仅确认 aarch64_cortex-a53、scutclient-3.1.3-r2；完整固件版本与 target/subtarget 尚未核实。取得匹配发行版、版本和 target/subtarget 的 ImmortalWrt SDK 并验证校验值，不能仅凭 CPU 架构选择。

Windows 使用 WSL2/Linux，在 Linux 文件系统内解压构建。当前电脑未安装 WSL，本次没有产出 APK。构建依赖参考 https://openwrt.org/docs/guide-developer/toolchain/install-buildsystem 。

## 在 SDK 根目录执行

```sh
./scripts/feeds update -a
./scripts/feeds install -a
SOURCE=/absolute/path/to/luci-app-scutclient
test -f "$SOURCE/Makefile"
test -f feeds/luci/luci.mk
```

将 SOURCE 改成 Linux 下的本仓库绝对路径。检查 package/feeds/luci/luci-app-scutclient：若为官方包符号链接，使用 unlink package/feeds/luci/luci-app-scutclient 解除链接；若为真实目录，先检查备份。确保没有两个同名包。

确认 package/luci-app-scutclient 尚不存在，然后：

```sh
mkdir package/luci-app-scutclient
cp "$SOURCE/Makefile" package/luci-app-scutclient/
cp -a "$SOURCE/luasrc" "$SOURCE/root" package/luci-app-scutclient/
make menuconfig
```

在 LuCI → Applications 选择 luci-app-scutclient 为 M，保存后：

```sh
make defconfig
make package/luci-app-scutclient/compile -j1 V=s
find bin/packages -type f -name 'luci-app-scutclient*.apk'
```

缺依赖时检查对应 feeds，不要删依赖绕过错误。若生成 IPK，重新确认 SDK 打包格式。

## 安装

备份配置和之前手工修改的 controller、模板、menu.d。把实际 APK 拷入设备 /tmp，替换下面文件名：

```sh
apk add --allow-untrusted /tmp/luci-app-scutclient-ACTUAL_VERSION.apk
/etc/init.d/rpcd restart
/etc/init.d/uhttpd restart
```

allow-untrusted 用于自己编译而未配置信任签名的包。遇版本或文件冲突先检查原因，不强制覆盖。重新登录 LuCI，按验证清单测试；必要时只清理确认属于 LuCI 的索引/模块缓存。

后续确认 SDK URL、校验值和 target 后，可添加 GitHub Actions 构建；当前没有未经验证的自动发布流程。
