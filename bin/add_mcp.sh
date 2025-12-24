#!/usr/bin/sh
d=$(cd $(dirname $0) && pwd)
cd $d/../

# stdin
claude mcp add sequential-thinking -s project -- npx -y @modelcontextprotocol/server-sequential-thinking
claude mcp add context7 -- npx -y @upstash/context7-mcp
claude mcp add codex-cli -- npx -y codex-mcp-server 
claude mcp add codex-cli --env CODEX_HOME=$(pwd) -- npx -y codex-mcp-server


# npm install @byterover/cipher
# claude mcp add cipher -- cipher --mode mcp        # to set OPENAI_API_KEY for using

# sse
claude mcp add serena -s project --transport http http://serena:9121/mcp


