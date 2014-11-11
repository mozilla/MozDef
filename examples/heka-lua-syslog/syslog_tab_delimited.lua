-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at http://mozilla.org/MPL/2.0/.
-- Copyright (c) 2014 Mozilla Corporation
--
-- Contributors:
-- Anthony Verez averez@mozilla.com
-- Mike Trinkala mtrinkala@mozilla.com

require "lpeg"
require "string"
local sep = lpeg.P"\t"
local elem = lpeg.C((1-sep)^0)
grammar = lpeg.Ct(elem * (sep * elem)^0) -- split on tabs, return as table


function process_message()
    local log = read_message("Payload")

        --set a default msg that heka's
    --message matcher will ignore
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

    -- populating our fields
    msg['Type'] = read_config('type')
    msg['Logger'] = 'heka'
    msg['Payload'] = matches[5]
    msg['Severity'] = 'INFO'
    msg.Fields['hostname'] = matches[2]
    msg.Fields['timestamp'] = matches[1]
    msg.Fields['hostname'] = matches[2]
    msg.Fields['program'] = matches[3]
    msg.Fields['processid'] = matches[4]
--    msg.Fields['debug'] = matches
    inject_message(msg)
    return 0
end
