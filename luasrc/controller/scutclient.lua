module("luci.controller.scutclient", package.seeall)


local log_file = "/tmp/scutclient.log"
local log_file_backup = "/tmp/scutclient.log.backup.log"

function index()
    local fs = require "nixio.fs"
    if not fs.access("/etc/config/scutclient") then return end
    -- Visible pages are declared in menu.d; only legacy APIs live here.
    entry({"admin", "services", "scutclient", "get_log"}, call("get_log")).leaf = true
    entry({"admin", "services", "scutclient", "netstat"}, call("get_netstat")).leaf = true
    entry({"admin", "services", "scutclient", "scutclient-log.tar"}, call("get_dbgtar")).leaf = true
end


function get_log()
	local http = require "luci.http"
	local fs = require "nixio.fs"
	local sys = require "luci.sys"
	local send_log_lines = 75
	local client_log
	if fs.access(log_file) then
		client_log = sys.exec("tail -n "..send_log_lines.." " .. log_file)
	else
		client_log = "Unable to access the log file!"
	end

	http.prepare_content("text/plain; charset=gbk")
	http.write(client_log)
	http.close()
end

function action_settings(...)
    local dispatcher = require "luci.dispatcher"
    if type(dispatcher.invoke_cbi_action) == "function" then
        return dispatcher.invoke_cbi_action("scutclient/scutclient", {}, ...)
    elseif type(dispatcher._cbi) == "function" then
        return dispatcher._cbi({ model = "scutclient/scutclient", config = {} }, ...)
    end
    error("SCUTClient: no supported LuCI CBI dispatcher is available")
end

function action_about()
	local template = require "luci.template"
	template.render("scutclient/about")
end


function action_status()
	local template = require "luci.template"
	local http = require "luci.http"
	local sys = require "luci.sys"
	template.render("scutclient/status")
	if http.formvalue("logoff") == "1" then
		sys.call("/etc/init.d/scutclient stop > /dev/null")
	end
	if http.formvalue("redial") == "1" then
		sys.call("/etc/init.d/scutclient stop > /dev/null")
		sys.call("/etc/init.d/scutclient start > /dev/null")
	end
	if http.formvalue("move_tag") == "1" then
		sys.call("uci set scutclient.@luci[-1].mainorder=90")
		sys.call("uci commit")
		sys.call("rm -rf /tmp/luci-*cache")
	end
end

function get_netstat()
	local http = require "luci.http"
	local sys = require "luci.sys"
	local hcontent = sys.exec("wget -O- http://whatismyip.akamai.com 2>/dev/null | head -n1")
	local nstat = {}
	if hcontent == '' then
		nstat.stat = 'no_internet'
	elseif hcontent:find("(%d+)%.(%d+)%.(%d+)%.(%d+)") then
		nstat.stat = 'internet'
	else
		nstat.stat = 'no_login'
	end
	http.prepare_content("application/json")
	http.write_json(nstat)
	http.close()
end

function get_dbgtar()
	local http = require "luci.http"
	local fs = require "nixio.fs"
	local sys = require "luci.sys"

	local tar_dir = "/tmp/scutclient-log"
	local tar_files = {
		"/etc/config/wireless",
		"/etc/config/network",
		"/etc/config/system",
		"/etc/config/scutclient",
		"/etc/openwrt_release",
		"/etc/crontabs/root",
		"/etc/config/dhcp",
		"/tmp/dhcp.leases",
		"/etc/rc.local",
	}

	fs.mkdirr(tar_dir)
	table.foreach(tar_files, function(i, v)
			sys.call("cp " .. v .. " " .. tar_dir)
	end)

	if fs.access(log_file_backup) then
		sys.call("cat " .. log_file_backup .. " >> " .. tar_dir .. "/scutclient.log")
	end
	if fs.access(log_file) then
		sys.call("cat " .. log_file .. " >> " .. tar_dir .. "/scutclient.log")
	end
	http.prepare_content("application/octet-stream")
	http.write(sys.exec("tar -C " .. tar_dir .. " -cf - ."))
	sys.call("rm -rf " .. tar_dir)
	http.close()
end
