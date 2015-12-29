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
#fields ts  uid id.orig_h   id.orig_p   id.resp_h   id.resp_p   trans_depth method  uri date    request_from    request_to  response_from   response_to reply_to    call_id seq subject request_path    response_path   user_agent  status_code status_msg  warning request_body_len    response_body_len   content_type
#types  time    string  addr    port    addr    port    count   string  string  string  string  string  string  string  string  string  string  string  vector[string]  vector[string]  string  count   string  string  string  string  string

    msg['Type']='brosip'
    msg['Logger']='nsm'
    msg.Fields['ts'] = toString(matches[1])
    msg.Fields['uid'] = toString(matches[2])
    msg.Fields['sourceipaddress'] = toString(matches[3])
    msg.Fields['sourceport'] = toNumber(matches[4])
    msg.Fields['destinationipaddress'] = toString(matches[5])
    msg.Fields['destinationport'] = toNumber(matches[6])
    msg.Fields['transdepth'] = toNumber(matches[7])
    msg.Fields['method'] = toString(matches[8])
    msg.Fields['uri'] = toString(matches[9])
    msg.Fields['date'] = toString(matches[10])
    msg.Fields['requestfrom'] = toString(matches[11])
    msg.Fields['requestto'] = toString(matches[12])
    msg.Fields['responsefrom'] = toString(matches[13])
    msg.Fields['responseto'] = toString(matches[14])
    msg.Fields['replyto'] = toString(matches[15])
    msg.Fields['callid'] = toString(matches[16])
    msg.Fields['seq'] = toString(matches[17])
    msg.Fields['subject'] = toString(matches[18])
    msg.Fields['requestpath'] = toString(matches[19])
    msg.Fields['responsepath'] = toString(matches[20])
    msg.Fields['useragent'] = toString(matches[21])
    msg.Fields['statuscode'] = toNumber(matches[22])
    msg.Fields['statusmsg'] = toString(matches[23])
    msg.Fields['warning'] = toString(matches[24])
    msg.Fields['requestbodylen'] = toNumber(matches[25])
    msg.Fields['responsebodylen'] = toNumber(matches[26])
    msg.Fields['contenttype'] = lastField(toString(matches[27]))
    msg.Fields['summary'] = "SIP: " .. nilToString(msg.Fields['sourceipaddress']) .. " -> " .. nilToString(msg.Fields['destinationipaddress']) .. ":" .. nilToString(msg.Fields['destinationport']) .. " method " .. nilToString(msg.Fields['method']) .. " uri " .. nilToString(msg.Fields['uri']) .. " status " .. nilToString(msg.Fields['statusmsg'])
    inject_message(msg)
    return 0
end

