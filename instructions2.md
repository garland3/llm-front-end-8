
Writing a frontend for an llm similar to chatgpt or chainlit or anthropic. 
- users can see and select the llm they want to use. 

uses websockets for dynamic loading.
Be very modular and easy to optimize. 
All files shoudl be shorter than 400 lines long. No exceptions. 
when using fastsapi, make routes to help help seperate concerns. 

Add unit tests, but NOT integration tests. 

use a fastapi backend. Next.js is nice, but I think python is more widely known in the team now and likely into the future. Learning a new eco system of npm and node.js is not the best right now,...perhaps this will change in the future.
frontend is vanilla js. ... css, html. Likely this will be the first location to switch to npm. So, just use vanilla for now, but make it in its own folder and easy to switch in the future. No jinja2 templates. 


all tools or pipelines are mcp servers.... including RAG. . Some mcp's can just be the stdio version if they are commonly used, ... like RAG.
-- use resource, templates to surface UI options for a mcp at run time. .. important for authoarization of differen tools.
-- the frontend on chat complete can send the requested mcp tool to use ... or tools with "auto" selecton.
-- the frontend has buttons (for single activated toolcalls.... exclusive where you can only use it by itself,and checkboxes for loading multipletools).

common mcps are put in a folder called 'mcp' each folder in the 'mcp' folder specifies an mcp.
also a config.json for loading external mcps.
All user requests are validated server side, ... ie. you actually have access to the mcp you are requesting. 

use fastmcp2 https://gofastmcp.com/servers/server


Security: Implement robust security measures, including proper authentication and authorization, to protect user data and access to MCP servers.
-- auth will be a reveerse proxy. add middlware to cehck the x-email-header. if missing, then send to the /auth endpoint which will be handeled by the reverse proxy. 
-- make a debug mode that skips this, and makes the user test@test.com

Add logging. 
save all logs into a folder called logs. ON exception, use traceback to print the whole error to the log. 


Authorization
* authorization will be done via a custom library that you do NOT need to code.  You can add a simple mock for now.
* the only authoization you are allowed to call is a function called is_user_in_group(userid, groupid)

The python fastmcp is here. https://gofastmcp.com/getting-started/welcome
Look up documentation use the context 7 mcp. 

Here is a quick example of mcp server. The chat ui we are creating is mostly a mcp client. 

```python
from fastmcp import FastMCP

mcp = FastMCP("Demo ")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run()

```

Do NOT use emojis anywhere in the code base. 

Add a docker file. Use fedora:latest as the base. 

use uv for python
make it so it can read a yml file for model_url, model_name, and api_key to allow multiple models to be visibile. 
there is a config.json for the other mcp servers
all other config vaus should be in a .env file. 
