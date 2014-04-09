require "lpeg"
require "string"
-- Some magic for parsing tab-separated logs
local sep = lpeg.P"\t"
local elem = lpeg.C((1-sep)^0)
grammar = lpeg.Ct(elem * (sep * elem)^0) -- split on tabs, return as table

local msg = {
    Type = "bronotice_log",
    Logger = "nsm",
    Fields = {
        -- Initializing our fields
        ['details.ts'] = nil,
        ['details.uid'] = nil,
        ['details.orig_h'] = nil,
        ['details.orig_p'] = nil,
        ['details.resp_h'] = nil,
        ['details.resp_p'] = nil,
        ['details.proto'] = nil,
        ['details.note'] = nil,
        ['details.msg'] = nil,
        ['details.sub'] = nil,
        summary = nil,
        severity = "NOTICE",
        category = "bronotice",
        tags = "nsm,bro,notice"
    }
}

function process_message()
    local log = read_message("Payload")

    -- Don't take comments
    if string.sub(log, 1, 1) ~= "#" then
        local matches = grammar:match(log)
        if not matches then return -1 end

        -- populating our fields
        msg.Fields['details.ts'] = matches[1]
        msg.Fields['details.uid'] = matches[2]
        msg.Fields['details.sourceipaddress'] = matches[3]
        msg.Fields['details.sourceport'] = matches[4]
        msg.Fields['details.destinationipaddress'] = matches[5]
        msg.Fields['details.destinationport'] = matches[6]
        msg.Fields['details.proto'] = matches[10]
        msg.Fields['details.note'] = matches[11]
        msg.Fields['details.msg'] = matches[12]
        msg.Fields['details.sub'] = matches[13]
        -- Our summary is the concatenation of other fields
        msg.Fields['summary'] = msg.Fields['details.note'] .. " " .. msg.Fields['details.msg'] .. " " .. msg.Fields['details.sub']
        inject_message(msg)
        return 0
    else
        return -1 -- do not send bro comments
    end
end
