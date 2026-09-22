-- Run with Lua 5.1 from the repository root; no router modules are required.
local controller_path = "luasrc/controller/scutclient.lua"
dofile(controller_path)
local settings = luci.controller.scutclient.action_settings

local called
package.loaded["luci.dispatcher"] = {
    invoke_cbi_action = function(model, config, argument)
        assert(model == "scutclient/scutclient")
        assert(type(config) == "table" and next(config) == nil)
        assert(argument == "request-argument")
        called = "modern"
        return "modern-result"
    end,
    _cbi = function() error("Legacy entry must not run on modern LuCI") end
}
assert(settings("request-argument") == "modern-result")
assert(called == "modern")

package.loaded["luci.dispatcher"] = {
    _cbi = function(options, argument)
        assert(options.model == "scutclient/scutclient")
        assert(type(options.config) == "table" and next(options.config) == nil)
        assert(argument == "request-argument")
        called = "legacy"
        return "legacy-result"
    end
}
assert(settings("request-argument") == "legacy-result")
assert(called == "legacy")

package.loaded["luci.dispatcher"] = {}
local ok, message = pcall(settings)
assert(not ok and message:find("no supported LuCI CBI dispatcher", 1, true))
print("Settings dispatcher: modern, legacy and unsupported cases passed")
