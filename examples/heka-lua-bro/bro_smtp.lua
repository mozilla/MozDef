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
        return nil
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

    msg['Type'] = 'brosmtp'
    msg['Logger'] = 'nsm'
    msg.Fields['ts'] = toString(matches[1])
    msg.Fields['uid'] = toString(matches[2])
    msg.Fields['sourceipaddress'] = toString(matches[3])
    msg.Fields['sourceport'] = toNumber(matches[4])
    msg.Fields['destinationipaddress'] = toString(matches[5])
    msg.Fields['destinationport'] = toNumber(matches[6])
    msg.Fields['trans_depth_int'] = toNumber(matches[7])
    msg.Fields['helo'] = toString(matches[8])
    msg.Fields['mailfrom'] = truncate(toString(matches[9]))
    msg.Fields['rcptto'] = truncate(toString(matches[10]))
    msg.Fields['date'] = truncate(toString(matches[11]))
    msg.Fields['from'] = truncate(toString(matches[12]))
    msg.Fields['to'] = truncate(toString(matches[13]))
    msg.Fields['reply_to'] = truncate(toString(matches[14]))
    msg.Fields['msg_id'] = truncate(toString(matches[15]))
    msg.Fields['in_reply_to'] = truncate(toString(matches[16]))
    msg.Fields['subject'] = truncate(toString(matches[17]))
    msg.Fields['x_originating_ip'] = toString(matches[18])
    msg.Fields['first_received'] = truncate(toString(matches[19]))
    msg.Fields['second_received'] = truncate(toString(matches[20]))
    msg.Fields['last_reply'] = truncate(toString(matches[21]))
    msg.Fields['path'] = truncate(toString(matches[22]))
    msg.Fields['user_agent'] = truncate(toString(matches[23]))
    msg.Fields['tls'] = toString(matches[24])
    msg.Fields['fuids'] = truncate(toString(matches[25]))
    msg.Fields['is_webmail'] = toString(lastField(matches[26])) -- remove last "\n"
    msg.Fields['summary'] = "SMTP: " .. nilToString(msg.Fields['sourceipaddress']) .. " -> " .. nilToString(msg.Fields['destinationipaddress']) .. " from " .. nilToString(msg.Fields['from']) .. " to " .. nilToString(msg.Fields['to'])  .. " ID " .. nilToString(msg.Fields['msg_id'])
    inject_message(msg)
    return 0
end

