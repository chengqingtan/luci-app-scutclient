# 开发与目录指南

[文档导航](README.md) · [构建指南](BUILD.md) · [验证状态](VALIDATION.md)

## 目录结构

项目根目录本身就是一个 LuCI 软件包。保留 `Makefile`、`luasrc/` 和 `root/` 的标准位置，便于放入 SDK 的 `package/luci-app-scutclient`，也便于构建脚本逐文件核对源码。

```text
luci-app-scutclient/
├── README.md                      # 使用入口：选包、安装、配置
├── Makefile                       # LuCI 包版本、依赖与打包规则
├── .github/workflows/
│   └── build-packages.yml         # 手动构建、矩阵和附件上传
├── luasrc/
│   ├── controller/scutclient.lua  # 页面入口与日志、网络状态接口
│   ├── model/cbi/scutclient/       # 设置表单
│   └── view/scutclient/            # 状态、日志、关于模板
├── root/
│   ├── etc/uci-defaults/          # 安装初始化
│   └── usr/share/
│       ├── luci/menu.d/           # 菜单与路由
│       └── rpcd/acl.d/            # UCI 访问权限
├── scripts/
│   ├── sdks.json                  # 受支持的 SDK 元数据
│   ├── sdk_matrix.py              # 版本、架构选择与矩阵生成
│   ├── build-packages.sh          # 下载、准备、编译
│   └── verify_packages.py         # 检查并收集两个产物
├── tests/
│   ├── test_build_tools.py        # 构建辅助工具的离线回归测试
│   └── test_settings.lua          # 新旧 LuCI 设置页入口测试
├── vendor/scutclient/             # OpenWrt 使用的核心打包文件与许可
└── docs/
    ├── README.md                  # 文档导航
    ├── BUILD.md                   # 构建与诊断
    ├── DEVELOPMENT.md             # 本文
    ├── VALIDATION.md              # 当前证据与验收清单
    ├── PROVENANCE.md              # 来源与许可
    └── history/                   # 历史验证记录
```

`vendor/scutclient` 不包含完整核心源码；构建时依据配方下载并校验。ImmortalWrt 使用其自身 feed 中的核心，OpenWrt 才使用这里的配方。

## 修改入口与安装路径

| 任务 | 源码位置 | 路由器安装位置或用途 |
| --- | --- | --- |
| 调整页面入口、日志接口 | [控制器](../luasrc/controller/scutclient.lua) | `/usr/lib/lua/luci/controller/scutclient.lua` |
| 修改设置表单 | [CBI 模型](../luasrc/model/cbi/scutclient/scutclient.lua) | `/usr/lib/lua/luci/model/cbi/scutclient/scutclient.lua` |
| 修改状态、日志、关于页面 | [模板目录](../luasrc/view/scutclient/) | `/usr/lib/lua/luci/view/scutclient/` |
| 调整菜单与访问权限 | [安装文件目录](../root/) | 相对 root 的路径原样安装到路由器根目录 |
| 修改构建或产物检查 | [脚本目录](../scripts/) | 仅在构建机执行，不安装到路由器 |
| 修改自定义包版本与依赖 | [Makefile](../Makefile) | 软件包元数据 |

新旧 LuCI 共用一套源码。设置页兼容入口选择新版 `invoke_cbi_action` 或旧版 `_cbi`，JSON 菜单保留 `cbi.submit` 提交保护。依赖与版本格式的区别见 [构建指南](BUILD.md#旧版-luci-兼容)。

## 构建目录与产物

推荐将下载、SDK 和产物放在仓库外；本地构建示例见 [构建指南](BUILD.md#本地-sdk-构建)。也可以在仓库内使用 `.build/` 和 `output/`，两者均被 Git 忽略，不预先创建空占位目录。

脚本的工作目录和输出目录参数必须是**尚不存在的具体路径**。例如使用 `.build/run-01` 和 `output/run-01`，下次改用新的运行目录。产物写入输出目录下的 `packages/`；脚本不清空或复用已有目录。

APK/IPK、日志、归档和 Python 缓存属于本地产物，不提交到源码仓库。`.gitignore` 只影响未跟踪文件，不能清除已提交的文件或历史内容。

## 本地检查

从仓库根目录执行。Python 检查要求 Python 3.9+ 和 GNU make；Windows 可使用 `mingw32-make`。Lua 检查使用 Lua 5.1。Bash、ShellCheck 和 actionlint 应已安装。

```sh
python3 -B -m unittest discover -s tests -v
lua5.1 tests/test_settings.lua
find luasrc -name '*.lua' -print0 | xargs -0 -r -n1 luac5.1 -p
bash -n scripts/build-packages.sh
shellcheck scripts/build-packages.sh
actionlint .github/workflows/build-packages.yml
git diff --check
```

离线测试使用合成 IPK/ELF，APK 解码使用模拟接口；Lua 测试也不启动真实 LuCI。实际构建与设备验收请使用 [验证清单](VALIDATION.md)。

## 新增版本或架构

1. 核对对应发行版官方下载目录中的 SDK 文件名、GCC 版本、SHA256，以及 `profiles.json` 中的软件包架构。
2. 更新 [SDK 清单](../scripts/sdks.json)：填写格式、压缩方式、包版本格式、runner、Lua 运行时布局和架构目标映射，不使用猜测的 URL 或相近架构。
3. 同步 [工作流](../.github/workflows/build-packages.yml) 中的选项。新增架构还需更新 ELF 架构/字节序校验表及测试；不要把 `all` 当作 CPU 架构。
4. 补充回归测试与环境适配，确认 SDK 的核心来源、依赖和包版本生成规则。
5. 更新 README 的用户选项、构建文档和验证状态。先验证一个架构，再覆盖全部新增组合；公共逻辑修改还需回归已有系统。

## Git / GitHub 维护

先 Fork，再通过 SSH 克隆自己的仓库；将占位用户名替换为自己的 GitHub 用户名，确保 SSH key 已配置：

```sh
git clone git@github.com:YOUR_GITHUB_USERNAME/luci-app-scutclient.git
cd luci-app-scutclient
git remote -v
```

修改后先检查差异和测试结果，再显式选择文件提交。推送前确认远程仓库属于自己。工作流文件须存在于 GitHub 默认分支，才能正常使用手动触发入口；修复后应从最新提交启动新运行。

不要提交真实账号、密码、路由器配置或调试包。状态页仍会显示设备中的密码，调试包也可能包含凭据；这些是已有运行行为，提交排错资料前应脱敏。来源与许可证按 [来源说明](PROVENANCE.md) 保留。
