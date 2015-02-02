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

function lastField(value)
    -- remove last "\n" if there's one
    if value ~= nil and string.len(value) > 1 and string.sub(value, -2) == "\n" then
        return string.sub(value, 1, -2)
    end
    return value
end

function validIP(value)
    if string.find(value, "-") then
        return "0.0.0.0"
    end
end

function validPort(value)
    if string.find(value, "-") then
        return "0"
    end
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
    
    if string.find(matches[13], toString("unknown-")) then
        --noise from incorrect ssl parsing, should be fixed in Bro 2.4
        --unknown-6518900,unknown-11273317,unknown-4522550,unknown-12624352,unknown-4609124,unknown-12586245
        inject_message(msg)
        return 0
    end

    if string.find(matches[13], toString("empty")) then
        --noise from incorrect ssl parsing, should be fixed in Bro 2.4
	-- (empty)
        inject_message(msg)
        return 0
    end

    msg['Type']='bronotice'
    msg['Logger']='nsm'
    msg['ts'] = toString(matches[1])
    msg.Fields['uid'] = toString(matches[2])
    msg.Fields['sourceipaddress'] = toString(validIP(matches[3]))
    msg.Fields['sourceport'] = toNumber(validPort(matches[4]))
    msg.Fields['destinationipaddress'] = toString(validIP(matches[5]))
    msg.Fields['destinationport'] = toNumber(validPort(matches[6]))
    msg.Fields['fuid'] = toString(matches[7])
    msg.Fields['file_mime_type'] = toString(matches[8])
    msg.Fields['file_desc'] = toString(matches[9])
    msg.Fields['proto'] = toString(matches[10])
    msg.Fields['note'] = toString(matches[11])
    msg.Fields['msg'] = toString(matches[12])
    msg.Fields['sub'] = toString(matches[13])
    msg.Fields['src'] = toString(matches[14])
    msg.Fields['dst'] = toString(matches[15])
    msg.Fields['p'] = toString(matches[16])
    msg.Fields['n'] = toString(matches[17])
    msg.Fields['peer_descr'] = toString(matches[18])
    msg.Fields['actions'] = toString(matches[19])
    msg.Fields['suppress_for'] = toString(matches[20])
    msg.Fields['dropped'] = lastField(toString(matches[21]))
    msg['Payload'] = toString(msg.Fields['note']) .. " " .. toString(msg.Fields['msg']) .. " " .. toString(msg.Fields['sub'])
    inject_message(msg)
    return 0
end

