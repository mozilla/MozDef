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

    countfields = 0
    for index, value in pairs(matches) do
        countfields = countfields + 1
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

    msg['Type']='brossl'
    msg['Logger']='nsm'
    msg['ts'] = toString(matches[1])
    msg.Fields['uid'] = toString(matches[2])
    msg.Fields['sourceipaddress'] = toString(matches[3])
    msg.Fields['sourceport'] = toNumber(matches[4])
    msg.Fields['destinationipaddress'] = toString(matches[5])
    msg.Fields['destinationport'] = toNumber(matches[6])
    msg.Fields['version'] = toString(matches[7])
    msg.Fields['cipher'] = truncate(toString(matches[8]))
    if toString(matches[9]) ~= nil then
        msg.Fields['curve'] = toString(matches[9])
    end
    msg.Fields['server_name'] = truncate(toString(matches[10]))
    msg.Fields['session_id'] = truncate(toString(matches[11]))
    msg.Fields['last_alert'] = toString(matches[12])
    msg.Fields['established'] = toString(matches[13])
    msg.Fields['cert_chain_fuids'] = truncate(toString(matches[14]))
    msg.Fields['client_cert_chain_fuids'] = truncate(toString(matches[15]))
    msg.Fields['subject'] = truncate(toString(matches[16]))
    msg.Fields['issuer'] = truncate(toString(matches[17]))
    msg.Fields['client_subject'] = truncate(toString(matches[18]))
    msg.Fields['client_issuer'] = truncate(toString(matches[19]))
    msg.Fields['weak_cipher'] = toString(matches[20])
    msg.Fields['pfs'] = lastField(toString(matches[21]))
    if msg.Fields['server_name'] ~= nil then
        msg['Payload'] = "SSL: " .. nilToString(msg.Fields['sourceipaddress']) .. " -> " .. nilToString(msg.Fields['destinationipaddress']) .. ":" .. nilToString(msg.Fields['destinationport']) .. " " .. msg.Fields['server_name']
    else
         msg['Payload'] = "SSL: " .. nilToString(msg.Fields['sourceipaddress']) .. " -> " .. nilToString(msg.Fields['destinationipaddress']) .. ":" .. nilToString(msg.Fields['destinationport'])
    end
    inject_message(msg)
    return 0
end

