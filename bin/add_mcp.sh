#!/usr/bin/sh

# stdin
claude mcp add sequential-thinking -s project -- npx -y @modelcontextprotocol/server-sequential-thinking
claude mcp add context7 -- npx -y @upstash/context7-mcp

# npm install @byterover/cipher
# claude mcp add cipher -- cipher --mode mcp        # to set OPENAI_API_KEY for using

# sse
claude mcp add serena -s project --transport sse http://serena:9121/sse


# # custom script
# claude mcp add cognee -s project -- sh bin/run_cognee.sh

