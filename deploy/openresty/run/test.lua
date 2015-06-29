local UNSAFE_REGEX = "[^a-zA-Z0-9 _+@%-%.]"

function table_length(tab)
    local count = 0
    for _ in pairs(tab) do
        count = count + 1
    end
    return count
end

function sanitise_filename(fn)
    -- only allow up to 60 characters total
    if string.len(fn) > 60 then
        fn = string.sub(fn, 0, 59)
    end

    -- remove disallowed characters
    -- allow a-z, A-Z, 0-9, space, underscore, hyphen and .
    fn = string.gsub(fn, UNSAFE_REGEX, "")

    return fn
end

function generate_filename(ext)
    local resty_random = require "resty.random"
    local resty_str = require "resty.string"

    local rndstr = resty_random.bytes(16)
    return resty_str.tohex(rndstr) .. ext
end

function try_to_slice_segment(s, head, tail)
    local head_loc = string.find(s, head)
    if head_loc == nil then
        return nil
    end

    head_loc = head_loc + string.len(head)

    local tail_loc = string.find(s, tail, head_loc)
    if tail_loc == nil then
        return nil
    end

    local segment = string.sub(s, head_loc, tail_loc-1)
    return segment
end

function get_field_name(res)
    if res[1] == "Content-Disposition" then
        return try_to_slice_segment(res[2], "; name=\"", "\"")
    end
end
    

function my_get_file_name(res)
    if res[1] == "Content-Disposition" then
        local theirFn = try_to_slice_segment(res[2], "; filename=\"", "\"")
        if not theirFn then
            return generate_filename(".bin")
        end
        theirFn = sanitise_filename(theirFn)
        if theirFn == "" then
            -- filename invalid or blank, generating one
            return generate_filename(".bin")
        end

        return theirFn
    end
    return nil
end

function splitext(filename)
    return filename:match("(.*)(%.?.*)$")
end

local resty_sha1 = require "resty.sha1"
local upload = require "resty.upload"
local str = require "resty.string"

local cjson = require "cjson"

local chunk_size = 4096
local form = upload:new(chunk_size)
local sha1 = resty_sha1:new()
local file
local did_find_file = false

local submit_data = {}
local current_segment = nil

local test_target = ngx.re.gsub(ngx.var.request_uri, "/file/$", "/_preperform/")
local done_target = ngx.re.gsub(ngx.var.request_uri, "/file/$", "/_done/")
local test_res = ngx.location.capture(test_target,
    { method = ngx.HTTP_POST, body = "", args = "" }
)
if test_res.status ~= 200 then
    ngx.log(ngx.NOTICE, test_res.status)
    ngx.exit(ngx.HTTP_FORBIDDEN)
elseif test_res.truncated then
    ngx.exit(ngx.HTTP_INTERNAL_SERVER_ERROR)
end
local upload_target = cjson.decode(test_res.body)
if not upload_target.upload_to or not upload_target.subdir_name then
    ngx.exit(ngx.HTTP_INTERNAL_SERVER_ERROR)
end
local this_updir = upload_target.upload_to

ngx.header['Content-Type'] = 'text/plain'

while true do
    local typ, res, err = form:read()

    if not typ then
         ngx.say("failed to read: ", err)
         return
    end

    if typ == "header" then
        local fname = get_field_name(res)
        if fname and not did_find_file and fname == "file" then
            local file_name = my_get_file_name(res)
            if file_name then
                submit_data.file_path = upload_target.subdir_name .. "/" .. file_name
                submit_data.file_name, submit_data.file_extension = splitext(file_name)
                submit_data.file_extension = submit_data.file_extension or ""
                submit_data.file_size = 0
                file = io.open(this_updir .. "/" .. file_name, "w")
                if not file then
                    ngx.status = ngx.HTTP_INTERNAL_SERVER_ERROR
                    ngx.say("failed to open file ", file_name)
                    ngx.exit(ngx.HTTP_OK)
                    return
                end
            end
        end

        if fname and fname ~= "file" and table_length(submit_data) < 5 then
            current_segment = {name = fname, data = "", datalen = 0}
        end

     elseif typ == "body" then
        local reslen = string.len(res)

        if file then
            submit_data.file_size = submit_data.file_size + reslen
            file:write(res)
            sha1:update(res)
        end

        if current_segment and current_segment.datalen < 100 and reslen < 100 then
            current_segment.data = current_segment.data .. res
            current_segment.datalen = current_segment.datalen + reslen
        end

    elseif typ == "part_end" then
        if file then
            file:close()
            file = nil
            did_find_file = true
            local sha1sum = sha1:final()
            sha1:reset()
            submit_data.file_sha1 = str.to_hex(sha1sum)
        end

        if current_segment then
            submit_data[current_segment.name] = current_segment.data
            current_segment = nil
        end

    elseif typ == "eof" then
        if not did_find_file then
            ngx.status = ngx.HTTP_BAD_REQUEST
            ngx.say("request missing 'file'")
            break
        end

        --ngx.say(cjson.encode(submit_data))
        local test_res = ngx.location.capture(done_target,
            { method = ngx.HTTP_POST, body = cjson.encode(submit_data), args = "" }
        )
        ngx.status = test_res.status
        ngx.say(test_res.body)
        ngx.exit(ngx.HTTP_OK)
        break

    else
        -- do nothing
    end
end
