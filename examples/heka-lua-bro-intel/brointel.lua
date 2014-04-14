require "lpeg"
require "string"
-- Some magic for parsing tab-separated logs
local sep = lpeg.P"\t"
local elem = lpeg.C((1-sep)^0)
local grammar = -lpeg.P"#" * lpeg.Ct(elem * (sep * elem)^0) -- ignore comment, split on tabs, return as table

local msg = {
    Type = "brointel_log",
    Logger = "nsm",
    Fields = {
        -- Initializing our fields
        ['details.ts'] = nil,
        ['details.uid'] = nil,
        ['details.sourceipaddress'] = nil,
        ['details.sourceport'] = nil,
        ['details.destinationipaddress'] = nil,
        ['details.destinationport'] = nil,
        ['details.fuid'] = nil,
        ['details.filemimetype'] = nil,
        ['details.filedesc'] = nil,
        ['details.seenindicator'] = nil,
        ['details.seenwhere'] = nil,
        ['details.seenindicatortype'] = nil,
        ['details.sources'] = nil,
        ['summary'] = nil,
        summary = nil,
        severity = "NOTICE",
        category = "brointel",
        tags = "nsm,bro,intel"
    }
}

function process_message()
    local log = read_message("Payload")

    local matches = grammar:match(log)
    if not matches then return -1 end

    msg.Fields['details.ts'] = matches[1]
    msg.Fields['details.uid'] = matches[2]
    msg.Fields['details.sourceipaddress'] = matches[3]
    msg.Fields['details.sourceport'] = matches[4]
    msg.Fields['details.destinationipaddress'] = matches[5]
    msg.Fields['details.destinationport'] = matches[6]
    msg.Fields['details.fuid'] = matches[7]
    msg.Fields['details.filemimetype'] = matches[8]
    msg.Fields['details.filedesc'] = matches[9]
    msg.Fields['details.seenindicator'] = matches[10]
    msg.Fields['details.seenwhere'] = matches[11]
    msg.Fields['details.seenindicatortype'] = matches[12]
    msg.Fields['details.sources'] = matches[13]
    msg.Fields['summary'] = "Bro intel match: " .. msg.Fields['details.seenindicator']
    inject_message(msg)
    return 0
end
