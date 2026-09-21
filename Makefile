#
# Copyright (C) 2016 SCUT Router Term
#
# This is free software, licensed under the Apache License, Version 2.0 .
#
include $(TOPDIR)/rules.mk

LUCI_TITLE:=LuCI Support for scutclient
LUCI_DEPENDS:=+scutclient +luci-compat +luci-lib-nixio +luci-lua-runtime
PKG_VERSION:=26.264.1
PKG_RELEASE:=1
PKG_LICENSE:=Apache-2.0

include $(TOPDIR)/feeds/luci/luci.mk

# call BuildPackage - OpenWrt buildroot signature
