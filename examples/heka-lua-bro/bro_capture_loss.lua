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

    msg['Type'] = 'brocaptureloss'
    msg['Logger'] = 'nsm'
    msg.Fields['ts'] = toString(matches[1])
    msg.Fields['ts_delta_float'] = toNumber(matches[2])
    msg.Fields['peer'] = toNumber(matches[3])
    msg.Fields['gaps_int'] = toNumber(matches[4])
    msg.Fields['acks_int'] = toNumber(matches[5])
    msg.Fields['percent_lost_float'] = toNumber(lastField(matches[6])) -- remove last "\n"
    msg.Fields['summary'] = nilToString(msg.Fields['percent_lost_float']) .. "% loss on ".. nilToString(msg.Fields['host']) .. " in the last " .. nilToString(msg.Fields['ts_delta_float']) .. "  seconds"
    inject_message(msg)
    return 0
end

