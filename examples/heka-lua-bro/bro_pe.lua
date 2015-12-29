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

    msg['Type']='brope'
    msg['Logger']='nsm'
    msg.Fields['ts'] = toString(matches[1])
    msg.Fields['uid'] = toString(matches[2])
    msg.Fields['machine'] = toString(matches[3])
    msg.Fields['compilets'] = toString(matches[4])
    msg.Fields['os'] = toString(matches[5])
    msg.Fields['subsystem'] = toString(matches[6])
    msg.Fields['isexe'] = toString(matches[7])
    msg.Fields['is64bit'] = toString(matches[8])
    msg.Fields['usesaslr'] = toString(matches[9])
    msg.Fields['usesdep'] = toString(matches[10])
    msg.Fields['usescodeintegrity'] = toString(matches[11])
    msg.Fields['usesseh'] = toString(matches[12])
    msg.Fields['hasimporttable'] = toString(matches[13])
    msg.Fields['hasexporttable'] = toString(matches[14])
    msg.Fields['hascerttable'] = toString(matches[15])
    msg.Fields['hasdebugdata'] = toString(matches[16])
    msg.Fields['sectionnames'] = lastField(toString(matches[16]))
    msg.Fields['summary'] = "PE file: " .. nilToString(msg.Fields['os']) .. " " .. nilToString(msg.Fields['subsystem']) .. " " .. nilToString(msg.Fields['sectionnames'])
    inject_message(msg)
    return 0
end

