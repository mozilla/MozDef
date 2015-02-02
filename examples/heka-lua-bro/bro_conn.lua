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
    
    -- avoid logging UDP/TCP connections for UDP, remove that if you care
    if matches[8] == "dns" then 
        inject_message(msg)
        return 0 
    end

    msg['Type']='broconnection'
    msg['Logger']='nsm'
    msg['ts'] = toString(matches[1])
    msg.Fields['uid'] = toString(matches[2])
    msg.Fields['sourceipaddress'] = toString(matches[3])
    msg.Fields['sourceport'] = toNumber(matches[4])
    msg.Fields['destinationipaddress'] = toString(matches[5])
    msg.Fields['destinationport'] = toNumber(matches[6])
    msg.Fields['protocol'] = toString(matches[7])
    msg.Fields['service'] = toString(matches[8])
    msg.Fields['duration_float'] = toNumber(matches[9])
    msg.Fields['originbytes_int'] = toNumber(matches[10])
    msg.Fields['responsebytes_int'] = toNumber(matches[11])
    msg.Fields['connectionstate'] = toString(matches[12])
    msg.Fields['local_origin'] = toString(matches[13])
    msg.Fields['missedbytes_int'] = toNumber(matches[14])
    msg.Fields['history'] = toString(matches[15])
    msg.Fields['originpkts_int'] = toNumber(matches[16])
    msg.Fields['originipbytes_int'] = toNumber(matches[17])
    msg.Fields['responsepackets_int'] = toNumber(matches[18])
    msg.Fields['responseipbytes_int'] = toNumber(matches[19])
    msg.Fields['tunnelparents'] = lastField(toString(matches[20]))
    msg['Payload'] = toString(msg.Fields['sourceipaddress']) .. ":" .. toString(msg.Fields['sourceport']) .. " -> " .. toString(msg.Fields['destinationipaddress']) .. ":" .. toString(msg.Fields['destinationport']) .. " " .. toString(msg.Fields['history']) .. " " .. toString(msg.Fields['originipbytes_int']) .. " bytes / " .. toString(msg.Fields['responseipbytes_int']) .. " bytes"
    inject_message(msg)
    return 0
end

