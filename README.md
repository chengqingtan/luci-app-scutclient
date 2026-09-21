# luci-app-scutclient：ImmortalWrt 25 兼容版

基于 [scutclient/luci-app-scutclient](https://github.com/scutclient/luci-app-scutclient)，保留状态、设置、日志、关于四个页面。核心认证程序继续使用软件源的 scutclient。

已整理：函数内 local require、服务菜单 JSON、APK/opkg/可执行文件安装检测、分段 build_url、新路径、fetch 日志刷新、Lua 兼容依赖和 RPCD ACL。

**这是根据原会话重建的源码，不是设备最终文件的逐字备份；尚未完成本仓库 SDK 编译和上机回归。** 详见 [验证记录](docs/VALIDATION.md)、[构建说明](docs/BUILD.md)、[来源](docs/PROVENANCE.md)。

## Git / GitHub

本地 main 分支保留原版历史，upstream 指向原版。尚未设置个人 origin 或推送。创建自己的 GitHub 空仓库后，替换以下地址再执行：

```sh
git remote add origin https://github.com/YOUR_ACCOUNT/luci-app-scutclient.git
git push -u origin main
```

后续用 git diff 审阅、git add / git commit 保存修改。不要提交真实账号、密码、设备配置或调试包。

包名保持 luci-app-scutclient，自定义版本为 26.264.1-r1；不承诺高于未来官方版本，安装前检查设备版本。上游 Makefile 声明 Apache-2.0，原作者版权注释保留。
