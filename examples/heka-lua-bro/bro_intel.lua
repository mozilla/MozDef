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

    msg['Type']='brointel'
    msg['Logger']='nsm'
    msg['ts'] = toString(matches[1])
    msg.Fields['uid'] = toString(matches[2])
    msg.Fields['sourceipaddress'] = toString(matches[3])
    msg.Fields['sourceport'] = toNumber(matches[4])
    msg.Fields['destinationipaddress'] = toString(matches[5])
    msg.Fields['destinationport'] = toNumber(matches[6])
    msg.Fields['fuid'] = toString(matches[7])
    msg.Fields['filemimetype'] = toString(matches[8])
    msg.Fields['filedesc'] = toString(matches[9])
    msg.Fields['seenindicator'] = toString(matches[10])
    msg.Fields['seenindicatortype'] = toString(matches[11])
    msg.Fields['seenwhere'] = toString(matches[12])
    msg.Fields['seennode'] = toString(matches[13])
    -- because seen.cluster_client_ip is 14 and also the last field
    msg.Fields['sources'] = toString(matches[15])
    msg.Fields['clusterclientip'] = lastField(toString(matches[16]))
    msg['Payload'] = "Bro intel match: " .. toString(msg.Fields['seenindicator'])
    inject_message(msg)
    return 0
end

