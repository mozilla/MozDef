-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at http://mozilla.org/MPL/2.0/.
-- Copyright (c) 2014 Mozilla Corporation
--
-- Contributors:
-- Anthony Verez averez@mozilla.com
-- Mike Trinkala mtrinkala@mozilla.com

require "lpeg"
require "string"
local sep = lpeg.P"\t"
local elem = lpeg.C((1-sep)^0)
grammar = lpeg.Ct(elem * (sep * elem)^0) -- split on tabs, return as table

local msg = {
    type = "lua_syslog_tab_delimited",
    logger = "heka",
    Fields = {
        ['type'] = nil,
        ['logger'] = nil,
        ['summary'] = nil,
        ['severity'] = nil,
        ['hostname'] = nil,
        ['details.syslogtimestamp'] = nil,
        ['details.hostname'] = nil,
        ['details.program'] = nil,
        ['details.processid'] = nil,
    }
}

function process_message()
    local log = read_message("Payload")

    local matches = grammar:match(log)
    if not matches then return -1 end

    -- populating our fields
    msg.Fields['type'] = read_config('type')
    msg.Fields['logger'] = 'heka'
    msg.Fields['summary'] = matches[5]
    msg.Fields['severity'] = 'INFO'
    msg.Fields['hostname'] = matches[2]
    msg.Fields['details.timestamp'] = matches[1]
    msg.Fields['details.hostname'] = matches[2]
    msg.Fields['details.program'] = matches[3]
    msg.Fields['details.processid'] = matches[4]
--    msg.Fields['debug'] = matches
    inject_message(msg)
    return 0
end
