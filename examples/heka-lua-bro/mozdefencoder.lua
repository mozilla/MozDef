-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at http://mozilla.org/MPL/2.0/.

require "cjson"
require "string"

local msg = {}

function process_message ()
    msg.Uuid = read_message("Uuid")
    msg.Timestamp = read_message("Timestamp")
    msg.Type = read_message("Type")
    msg.Logger = read_message("Logger")
    msg.Severity = read_message("Severity")
    msg.Payload = read_message("Payload")
    msg.Pid = read_message("Pid")
    msg.Hostname = read_message("Hostname")

    local f = {}
    msg.Fields = f

    while true do
        local typ, name, value, rep, cnt = read_next_field()
        if not typ then break end

        if not f[name] then -- first instance wins, any others are ignored
            if cnt > 1 then
                f[name] = {}
                local full_name = string.format("Fields[%s]", name)
                for i=1, cnt do
                    f[name][i] = read_message(full_name, 0, i-1)
                end
            else
                f[name] = value
            end
        end
    end

    inject_payload("json", "mozdef", cjson.encode(msg))
    return 0
end

