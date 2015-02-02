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
    end

    msg['Type']='brosqli'
    msg['Logger']='nsm'
    msg['ts'] = toString(matches[1])
    msg.Fields['uid'] = toString(matches[2])
    msg.Fields['sourceipaddress'] = toString(matches[3])
    msg.Fields['sourceport'] = toNumber(matches[4])
    msg.Fields['destinationipaddress'] = toString(matches[5])
    msg.Fields['destinationport'] = toNumber(matches[6])
    msg.Fields['cluster_client_ip'] = toString(matches[7])
    msg.Fields['status_code_int'] = toNumber(matches[8])
    msg.Fields['host'] = toString(matches[9])
    msg.Fields['uri'] = toString(matches[10])
    msg.Fields['sig_id'] = toString(matches[11])
    msg.Fields['tags'] = toString(string.sub(matches[12], 1, -2)) -- remove last "\n"
    msg['Payload'] = "SQLi by " .. nilToString(msg.Fields['cluster_client_ip'])  .. " on " .. nilToString(msg.Fields['host'])
    inject_message(msg)
    return 0
end

