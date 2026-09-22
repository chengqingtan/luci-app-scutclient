#
# Copyright (C) 2016 SCUT Router Term
#
# This is free software, licensed under the Apache License, Version 2.0 .
#
include $(TOPDIR)/rules.mk

LUCI_TITLE:=LuCI Support for scutclient
LUCI_DEPENDS:=+scutclient +luci-compat +luci-lib-nixio
# Older LuCI provides Lua support through luci-base, without a runtime package.
ifneq ($(wildcard $(TOPDIR)/feeds/luci/modules/luci-lua-runtime/Makefile),)
LUCI_DEPENDS+=+luci-lua-runtime
endif
PKG_VERSION:=26.264.1
PKG_RELEASE:=2
PKG_LICENSE:=Apache-2.0

# Legacy luci.mk sets VERSION to PKG_VERSION without appending PKG_RELEASE.
ifeq ($(wildcard $(TOPDIR)/feeds/luci/modules/luci-lua-runtime/Makefile),)
PKG_VERSION:=$(PKG_VERSION)-$(PKG_RELEASE)
endif

include $(TOPDIR)/feeds/luci/luci.mk

# call BuildPackage - OpenWrt buildroot signature
