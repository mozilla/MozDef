-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at http://mozilla.org/MPL/2.0/.
-- Copyright (c) 2014 Mozilla Corporation
--
-- Contributors:
-- Anthony Verez averez@mozilla.com
-- Jeff Bryner jbryner@mozilla.com
-- Michal Purzynski mpurzynski@mozilla.com

local l=require "lpeg"
local string=require "string"
l.locale(l) --add locale entries in the lpeg table
local space = l.space^0  --define a space constant
local sep = l.P"\t"
local elem = l.C((1-sep)^0)
grammar = l.Ct(elem * (sep * elem)^0) -- split on tabs, return as table

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
        return 0
    end
    return tonumber(value)
end

function truncate(value)
    -- truncate the URI if too long (heka limited to 63KiB messages)
    if toString(value) then
        if string.len(value) > 10000 then
            return toString(string.sub(value, 1, 10000)) .. "[truncated]"
        else
            return value
        end
    end
end

function lastField(value)
    -- remove last "\n" if there's one
    if value ~= nil and string.len(value) > 1 and string.sub(value, -2) == "\n" then
        return string.sub(value, 1, -2)
    end
    return value
end

function process_message()
    local log = read_message("Payload")
    --set a default msg that heka's
    --message matcher can ignore via a message matcher:
    -- message_matcher = "( Type!='heka.all-report' && Type != 'IGNORE' )"
    local msg = {
        Type = "IGNORE",
        Fields={}
    }
    local matches = grammar:match(log)
    if not matches then
        --return 0 to not propogate errors to heka's log.
        --return a message with IGNORE type to not match heka's message matcher
        inject_message(msg)
        return 0
    end
    if string.sub(log,1,1)=='#' then
        --it's a comment line
        inject_message(msg)
        return 0
    end

    msg['Type'] = 'brohttp'
    msg['Logger'] = 'nsm'
    msg.Fields['ts'] = toString(matches[1])
    msg.Fields['uid'] = toString(matches[2])
    msg.Fields['sourceipaddress'] = toString(matches[3])
    msg.Fields['sourceport'] = toNumber(matches[4])
    msg.Fields['destinationipaddress'] = toString(matches[5])
    msg.Fields['destinationport'] = toNumber(matches[6])
    msg.Fields['trans_depth_int'] = toNumber(matches[7])
    msg.Fields['method'] = toString(matches[8])
    msg.Fields['host'] = toString(matches[9])
    msg.Fields['uri'] = truncate(toString(matches[10]))
    msg.Fields['referrer'] = toString(matches[11])
    msg.Fields['user_agent'] = truncate(toString(matches[12]))
    msg.Fields['request_body_len_int'] = toNumber(matches[13])
    msg.Fields['response_body_len_int'] = toNumber(matches[14])
    msg.Fields['status_code_int'] = toNumber(matches[15])
    msg.Fields['status_msg'] = toString(matches[16])
    msg.Fields['info_code_int'] = toNumber(matches[17])
    msg.Fields['info_msg'] = toString(matches[18])
    msg.Fields['filename'] = truncate(toString(matches[19]))
    msg.Fields['tags'] = truncate(toString(matches[20]))
    msg.Fields['username'] = truncate(toString(matches[21]))
    msg.Fields['password'] = truncate(toString(matches[22]))
    msg.Fields['proxied'] = truncate(toString(matches[23]))
    msg.Fields['orig_fuids'] = truncate(toString(matches[24]))
    msg.Fields['orig_mime_types'] = truncate(toString(matches[25]))
    msg.Fields['resp_fuids'] = truncate(toString(matches[26]))
    msg.Fields['resp_mime_types'] = truncate(toString(matches[27]))
    if lastField(toString(matches[28])) ~= nil then
        msg.Fields['cluster_client_ip'] = lastField(toString(matches[28]))
    end
    if msg.Fields['cluster_client_ip'] ~= nil then
        msg.Fields['summary'] = nilToString(msg.Fields['cluster_client_ip'])
    else
        msg.Fields['summary'] = nilToString(msg.Fields['sourceipaddress'])
    end
    msg.Fields['summary'] = msg.Fields['summary'] .. " - " .. nilToString(msg.Fields['method']) .. " " .. nilToString(msg.Fields['host']) .. nilToString(msg.Fields['uri']) .. " " .. nilToString(msg.Fields['status_code_int'])
    inject_message(msg)
    return 0
end

