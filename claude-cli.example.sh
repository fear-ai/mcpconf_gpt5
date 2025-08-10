claude mcp add-json weather '{"command":"uv","args":["--directory","/ABSOLUTE/PATH/TO/PARENT/FOLDER/weather","run","weather.py"]}'
claude mcp add-json everything '{"command":"npx","args":["-y","@modelcontextprotocol/server-everything"]}'
claude mcp add --transport http cloudflare-observability https://observability.mcp.cloudflare.com/sse
claude mcp add --transport http cloudflare-bindings https://bindings.mcp.cloudflare.com/sse
claude mcp add-json cli-mcp-server '{"command":"uvx","args":["cli-mcp-server"],"env":{"ALLOWED_DIR":"/your/desired/dir","ALLOWED_COMMANDS":"ls,cat,pwd,echo","ALLOWED_FLAGS":"-l,-a,--help,--version","MAX_COMMAND_LENGTH":"1024","COMMAND_TIMEOUT":"30","ALLOW_SHELL_OPERATORS":"false"}}'
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
claude mcp add --transport http github https://api.githubcopilot.com/mcp/
