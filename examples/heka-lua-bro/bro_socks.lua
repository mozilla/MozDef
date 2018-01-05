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
    Type = "brosocks",
    Logger = "nsm",
    Fields = {
        -- Initializing our fields
        ['ts'] = nil,
        ['uid'] = nil,
        ['sourceipaddress'] = nil,
        ['sourceport'] = nil,
        ['destinationipaddress'] = nil,
        ['destinationport'] = nil,
        ['version_int'] = nil,
        ['user'] = nil,
        ['status'] = nil,
        ['request.host'] = nil,
        ['request.name'] = nil,
        ['request_p_int'] = nil,
        ['bound.host'] = nil,
        ['bound.name'] = nil,
        ['bound_p_int'] = nil,
        ['summary'] = nil,
        summary = nil,
        severity = "INFO",
        category = "brosocks",
        tags = "nsm,bro,socks"
    }
}

function toString(value)
    if value == "-" then
        return nil
    end
    return value
end

function toNumber(value)
    if value == "-" then
        return nil
    end
    return tonumber(value)
end

function nilToString(value)
    if value == nil then
        return ""
    end
    return value
end

function process_message()
    local log = read_message("Payload")

    local matches = grammar:match(log)
    if not matches then return -1 end

    msg.Fields['ts'] = toString(matches[1])
    msg.Fields['uid'] = toString(matches[2])
    msg.Fields['sourceipaddress'] = toString(matches[3])
    msg.Fields['sourceport'] = toNumber(matches[4])
    msg.Fields['destinationipaddress'] = toString(matches[5])
    msg.Fields['destinationport'] = toNumber(matches[6])
    msg.Fields['version_int'] = toNumber(matches[7])
    msg.Fields['user'] = toString(matches[8])
    msg.Fields['status'] = toString(matches[9])
    msg.Fields['request.host'] = toString(matches[10])
    msg.Fields['request.name'] = toString(matches[11])
    msg.Fields['request_p_int'] = toNumber(matches[12])
    msg.Fields['bound.host'] = toString(matches[13])
    msg.Fields['bound.name'] = toString(matches[14])
    msg.Fields['bound_p_int'] = toNumber(string.sub(matches[15], 1, -2)) -- remove last "\n"
    msg.Fields['summary'] = nilToString(msg.Fields['sourceipaddress']) .. ":" .. nilToString(msg.Fields['sourceport']) .. " -> " .. nilToString(msg.Fields['destinationipaddress']) .. ":" .. nilToString(msg.Fields['destinationport']) .. " SOCKS v" .. nilToString(msg.Fields['version_int']) .. " " .. nilToString(msg.Fields['request.host']) .. ":" .. nilToString(msg.Fields['request_p_int']) .. " -> " .. nilToString(msg.Fields['bound.host']) .. ":" .. nilToString(msg.Fields['bound_p_int'])
    inject_message(msg)
    return 0
end

