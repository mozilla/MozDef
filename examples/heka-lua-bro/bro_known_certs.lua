-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at http://mozilla.org/MPL/2.0/.
-- Copyright (c) 2014 Mozilla Corporation

require "lpeg"
require "string"
-- Some magic for parsing tab-separated logs
local sep = lpeg.P"\t"
local elem = lpeg.C((1-sep)^0)
local grammar = -lpeg.P"#" * lpeg.Ct(elem * (sep * elem)^0) -- ignore comment, split on tabs, return as table

local msg = {
    Type = "broknowncerts",
    Logger = "nsm",
    Fields = {
        -- Initializing our fields
        ['ts'] = nil,
        ['host'] = nil,
        ['port_num_int'] = nil,
        ['subject'] = nil,
        ['issuer_subject'] = nil,
        ['serial'] = nil,
        summary = nil,
        severity = "INFO",
        category = "broknowncerts",
        tags = "nsm,bro,known_certs"
    }
}

function toString(value)
    if value == "-" then
        return nil
    end
    return value
end

function nilToString(value)
    if value == nil then
        return ""
    end
    return value
end

function toNumber(value)
    if value == "-" then
        return nil
    end
    return tonumber(value)
end

function process_message()
    local log = read_message("Payload")

    local matches = grammar:match(log)
    if not matches then return -1 end

    msg.Fields['ts'] = toString(matches[1])
    msg.Fields['host'] = toString(matches[2])
    msg.Fields['port_num_int'] = toNumber(matches[3])
    msg.Fields['subject'] = toString(matches[4])
    msg.Fields['issuer_subject'] = toString(matches[5])
    msg.Fields['serial'] = toString(string.sub(matches[6], 1, -2)) -- remove last "\n"
    msg.Fields['summary'] = nilToString(msg.Fields['host']) .. ":".. nilToString(msg.Fields['port_num_int']) .. " " .. nilToString(msg.Fields['subject'])
    inject_message(msg)
    return 0
end

