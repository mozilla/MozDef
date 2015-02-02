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
    
    if toNumber(matches[14]) == 0 then
        --there will be no hash..nothing seen
        inject_message(msg)
        return 0
    end

    msg['Type']='brofiles'
    msg['Logger']='nsm'
    msg['ts'] = toString(matches[1])
    msg.Fields['fuid'] = toString(matches[2])
    msg.Fields['tx_hosts'] = toString(matches[3])
    msg.Fields['rx_hosts'] = toString(matches[4])
    msg.Fields['uid'] = toString(matches[5])
    msg.Fields['source'] = toString(matches[6])
    msg.Fields['depth_int'] = toNumber(matches[7])
    msg.Fields['analyzers'] = toString(matches[8])
    msg.Fields['mime_type'] = toString(matches[9])
    msg.Fields['filename'] = toString(matches[10])
    msg.Fields['duration_float'] = toNumber(matches[11])
    msg.Fields['local_origin'] = toString(matches[12])
    msg.Fields['is_origin'] = toString(matches[13])
    msg.Fields['seen_bytes_int'] = toNumber(matches[14])
    msg.Fields['total_bytes_int'] = toNumber(matches[15])
    msg.Fields['missing_bytes_int'] = toNumber(matches[16])
    msg.Fields['overflow_bytes_int'] = toNumber(matches[17])
    msg.Fields['timedout'] = toString(matches[18])
    msg.Fields['parent_fuid'] = toString(matches[19])
    msg.Fields['md5'] = toString(matches[20])
    msg.Fields['sha1'] = toString(matches[21])
    msg.Fields['sha256'] = toString(matches[22])
    msg.Fields['extracted'] = lastField(toString(matches[23]))
    msg['Payload'] = toString(msg.Fields['rx_hosts']) .. " downloaded (MD5)" .. toString(msg.Fields['md5']) .. " " .. toString(msg.Fields['filename']) .. " (" .. toString(msg.Fields['total_bytes_int'])  .. " bytes) from " .. toString(msg.Fields['tx_hosts'])
    inject_message(msg)
    return 0
end

