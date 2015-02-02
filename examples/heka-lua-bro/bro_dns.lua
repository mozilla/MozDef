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

    if string.find(matches[9], "domainiignore.com$") then
	inject_message(msg)
	return 0
    end
    if string.find(matches[9], "anotherignoreddomain.org$") then
	inject_message(msg)
	return 0
    end
    -- avoid logging SMB DNS queries and answers. Remove this if you care.
    if matches[13] == "NBSTAT" then
        inject_message(msg)
        return 0
    end

    msg['Type'] = 'brodns'
    msg['Logger'] = 'nsm'
    msg.Fields['ts'] = toString(matches[1])
    msg.Fields['uid'] = toString(matches[2])
    msg.Fields['sourceipaddress'] = toString(matches[3])
    msg.Fields['sourceport'] = toNumber(matches[4])
    msg.Fields['destinationipaddress'] = toString(matches[5])
    msg.Fields['destinationport'] = toNumber(matches[6])
    msg.Fields['proto'] = toString(matches[7])
    msg.Fields['trans_id_int'] = toNumber(matches[8])
    msg.Fields['query'] = toString(matches[9])
    msg.Fields['qclass_int'] = toNumber(matches[10])
    msg.Fields['qclass_name'] = toString(matches[11])
    msg.Fields['qtype_int'] = toNumber(matches[12])
    msg.Fields['qtype_name'] = toString(matches[13])
    msg.Fields['rcode_int'] = toNumber(matches[14])
    msg.Fields['rcode_name'] = toString(matches[15])
    msg.Fields['AA'] = toString(matches[16])
    msg.Fields['TC'] = toString(matches[17])
    msg.Fields['RD'] = toString(matches[18])
    msg.Fields['RA'] = toString(matches[19])
    msg.Fields['Z'] = toNumber(matches[20])
    msg.Fields['answers'] = truncate(toString(matches[21]))
    msg.Fields['TTLs_float'] = truncate(toNumber(matches[22]))
    msg.Fields['rejected'] = lastField(toString(matches[23]))
    msg.Fields['summary'] = nilToString(msg.Fields['sourceipaddress']) .. " -> " .. nilToString(msg.Fields['destinationipaddress']) .. ": " .. nilToString(msg.Fields['qtype_name']) .. " " .. nilToString(msg.Fields['query']) .. " " .. nilToString(msg.Fields['rcode_name'])
    inject_message(msg)
    return 0
end

