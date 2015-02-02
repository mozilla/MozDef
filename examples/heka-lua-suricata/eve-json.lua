local cjson = require "cjson"
-- example of the input JSON from Suricata
-- local dt = require "date_time"

-- {
--    "timestamp": "2009-11-24T21:27:09.534255",
--    "event_type": "alert",
--    "src_ip": "192.168.2.7",
--    "src_port": 1041,
--    "dest_ip": "x.x.250.50",
--    "dest_port": 80,
--    "proto": "TCP",
--    "alert": {
--        "action": "allowed",
--        "gid": 1,
--        "signature_id" :2001999,
--        "rev": 9,
--        "signature": "ET MALWARE BTGrab.com Spyware Downloading Ads",
--        "category": "A Network Trojan was detected",
--        "severity": 1
--    }
-- }

local l=require "lpeg"
local string=require "string"
local math=require "math"
l.locale(l) --add locale entries in the lpeg table
local space = l.space^0  --define a space constant
local sep = l.P"\t"
local elem = l.C((1-sep)^0)
grammar = l.Ct(elem * (sep * elem)^0) -- split on tabs, return as table
local os=require "os"
-- set timezone defaults
-- local tz = os.date("%z") doesn't work
-- since heka sets sandbox env to UTC
-- override if not in UTC with heka.toml config like so:
-- [systemslogs_transform_decoder.config]
-- tzoffset="-0700"
local offset = "([+-])(%d%d)(%d%d)"
local tz= "-0000"
-- if read_config("tzoffset") then
--     tz=read_config("tzoffset")
-- end
local sign, hour, min  = tz:match(offset)

--date definitions:
date_mabbr = l.Cg(
    l.P"Jan"   /"1"
    + l.P"Feb" /"2"
    + l.P"Mar" /"3"
    + l.P"Apr" /"4"
    + l.P"May" /"5"
    + l.P"Jun" /"6"
    + l.P"Jul" /"7"
    + l.P"Aug" /"8"
    + l.P"Sep" /"9"
    + l.P"Oct" /"10"
    + l.P"Nov" /"11"
    + l.P"Dec" /"12"
    , "month")

date_fullyear = l.Cg(l.digit * l.digit * l.digit * l.digit, "year")

date_month = l.Cg(l.P"0" * l.R"19"
                     + "1" * l.R"02", "month")
date_mday = l.Cg(l.P"0" * l.R"19"
                    + l.R"12" * l.R"09"
                    + "3" * l.R"01", "day")

time_hour = l.Cg(l.R"01" * l.digit
                    + "2" * l.R"03", "hour")

time_minute = l.Cg(l.R"05" * l.digit, "min")

time_second = l.Cg(l.R"05" * l.digit
                           + "60", "sec") -- include leap second

time_secfrac = l.Cg(l.P"," * l.digit^1 / tonumber, "sec_frac")

rfc3339_partial_time    = time_hour * ":" * time_minute * ":" * time_second * time_secfrac^-1
dategrammer=l.Ct(date_fullyear *"-"* date_month  *"-"* date_mday * "T" * rfc3339_partial_time)

function time_to_ns(t)
    if not t then return 0 end

    local offset = 0
    if t.offset_hour then
        offset = (t.offset_hour * 60 * 60) + (t.offset_min * 60)
        if t.offset_sign == "+" then offset = offset * -1 end
    end

    local frac = 0
    if t.sec_frac then
        frac = t.sec_frac
    end
    return (os.time(t) + frac + offset) * 1e9
end

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
   local ok, json = pcall(cjson.decode, log)
   if not ok then
      return 0 -- when plain text is found, ship it in it's raw form
   end

    --set a default msg that heka's
    --message matcher will ignore
    -- this is a message skeleton that we will add fields to
    -- the initialization must be local to isolate variable's content between messages
    local msg = {
        Type = "IGNORE",
        Fields={}
    }
    --inject a random value for use in the message matcher
    --for poor mans load balancing
    msg.Fields['Random']=math.random(0,10)	

    local eventdate = dategrammer:match(json['timestamp'])
    if not eventdate then
        --no date/time, likely a stack trace
         inject_message(msg)
        return 0
    else
        --no year in the date, add current year. 
        eventdate.year=os.date('%Y')
        -- set the timezone
        eventdate.offset_hour=hour
        eventdate.offset_sign=sign
        eventdate.offset_min=min
    end

   msg['Type'] = 'suricata_event_log'
   msg['Logger'] = 'nsm'
   msg['severity'] = 'INFO'
   msg['category'] = 'suricata_event'
   msg['tags'] = 'nsm,suricata,event'
   msg['Timestamp'] = time_to_ns(eventdate)
   msg.Fields['Type'] = 'suricata_event_log'
   msg.Fields['flow_id'] = toNumber(json['flow_id'])
   msg.Fields['in_iface'] = json['in_iface']
   msg.Fields['vlan'] = toNumber(json['vlan'])
   msg.Fields['sourceipaddress'] = json['src_ip']
   msg.Fields['sourceport'] = toNumber(json['src_port'])
   msg.Fields['destinationipaddress'] = json['dest_ip']
   msg.Fields['destinationport'] = toNumber(json['dest_port'])
   msg.Fields['proto'] = json['proto']
   msg.Fields['gid'] = toNumber(json.alert['gid'])
   msg.Fields['signature_id'] = toNumber(json.alert['signature_id'])
   msg.Fields['rev'] = toNumber(json.alert['rev'])
   msg.Fields['signature'] = json.alert['signature']
   msg.Fields['category'] = json.alert['category']
   msg.Fields['severity'] = json.alert['severity']
   msg.Fields['tx_id'] = toNumber(json.alert['tx_id'])
   if json.http then
       msg.Fields['http_hostname'] = json.http['hostname']
       msg.Fields['http_url'] = json.http['url']
       msg.Fields['http_user_agent'] = json.http['http_user_agent']
       msg.Fields['http_content_type'] = json.http['http_content_type']
       msg.Fields['http_method'] = json.http['http_method']
       msg.Fields['http_protocol'] = json.http['protocol']
       msg.Fields['http_status'] = toNumber(json.http['status'])
       msg.Fields['http_length'] = toNumber(json.http['length'])
   end
   msg.Fields['payload'] = json['payload']
   msg.Fields['payload_printable'] = json['payload_printable']
   msg.Fields['stream'] = toNumber(json['stream'])
   msg.Fields['packet'] = lastField(json['packet'])
   inject_message(msg)
   return 0
end

