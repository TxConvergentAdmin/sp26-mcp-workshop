Yes — this is a very good MCP project.

A clean version is:

**Build a UT Courses MCP server that lets an LLM query course data through a small set of structured tools, instead of dumping the full JSON into context.** That matches MCP well because MCP servers expose tools/resources/prompts, and FastMCP is built exactly for wrapping Python functions as MCP-compliant tools and resources. ([FastMCP][1])

## Simple plan

### 1. Keep the JSON as your source of truth

Start with your scraped JSON file as the dataset. Do **not** make the LLM read the raw file directly for every question. Instead, load it once in Python, normalize a few fields, and expose targeted query functions through MCP tools. MCP tools are meant for executable capabilities with structured inputs, while resources are better for static context like metadata or schema summaries. ([FastMCP][2])

### 2. Use FastMCP for a very small server

Create one FastMCP server and register a handful of tools. FastMCP’s server is the container for tools, resources, and prompts, and the quickstart is just `mcp = FastMCP("...")` plus decorators. ([FastMCP][3])

### 3. Design for “query first, summarize second”

The server should not have one giant tool like `ask_courses_database(question)`. Better: expose small, predictable tools that return filtered results, and let the LLM compose them. That keeps it efficient and reduces hallucination risk because the model gets structured results back from the server rather than guessing from memory. MCP tools are designed for that kind of model-invoked action with clear schemas. ([Model Context Protocol][4])

### 4. Add 4–6 core tools only

A simple first version:

- `search_courses(department=None, number_level=None, keyword=None, instruction_mode=None, status=None)`
- `get_course_details(unique_id)`
- `list_open_courses(department=None, min_credit_hours=None, max_credit_hours=None)`
- `find_schedule_options(department, days=None, earliest_time=None, latest_time=None)`
- `find_instructor_courses(instructor_name)`
- `build_schedule(courses, constraints)`

This is enough for questions like:

- “What CS upper divs are open?”
- “Show me MWF courses after 11.”
- “What can I take with Professor X?”
- “Help me make a schedule with no Friday classes.”

### 5. Define one or two resources

Use MCP resources for things the model may want to read as reference:

- `resource://dataset-info` → what fields exist in the dataset
- `resource://query-tips` → how to ask about UT courses
- maybe `resource://departments` → list of department codes

Resources are meant to share context/data by URI, which fits schema summaries and lookup tables well. ([Model Context Protocol][5])

### 6. Add a prompt for schedule help

Add one MCP prompt like:

- `make_schedule` → “Given desired courses and constraints, help the student build a schedule using the available tools.”

Prompts in MCP are reusable templates/workflows, so this is a good fit if you want a guided schedule-building flow. ([Model Context Protocol][6])

### 7. Make the data efficient before MCP exposes it

Before wiring tools, preprocess the JSON:

- normalize department names/codes
- parse meeting days and times into machine-friendly fields
- flatten instructor names
- derive course level from the number
- index by `uniqueId`, department, instructor, and meeting time

This matters more than fancy MCP features. Your tools will be much faster if they query preprocessed data structures instead of rescanning raw nested JSON every time.

### 8. Keep tool outputs small

Each tool should return concise structured results, not hundreds of classes at once. Good rule:

- return top 10–20 matches
- include the fields students actually need
- include `uniqueId`, `fullName`, `status`, instructor, schedule, and URL
- let `get_course_details` return the full record when needed

That gives the LLM enough context without flooding the conversation.

### 9. Build schedule-making as a second step

For schedule creation, do not start with full optimization. First version:

- user specifies desired departments/courses and constraints
- tool filters valid sections
- simple logic removes time conflicts
- return 2–5 possible schedule combinations

That is enough for a workshop demo and feels impressive without getting too complex.

## Suggested architecture

**Data layer**

- `courses.json`
- `load_and_normalize.py`
- in-memory indexes

**MCP layer**

- FastMCP server
- tools for search/filter/detail/schedule
- one or two resources
- optional prompt

**Client/demo layer**

- Claude Desktop or another MCP client
- ask natural-language questions
- LLM chooses tools
- tools return structured course data

FastMCP clients can list tools and call them with arguments, which matches the demo flow you want. ([FastMCP][7])

## Best first milestone

Build only this first:

1. load JSON
2. create FastMCP server
3. add `search_courses`
4. add `get_course_details`
5. add `find_schedule_options`

If those 3 tools work well, the project is already useful.

## Best workshop framing

Call it:

**UT Course Explorer MCP**

Demo questions:

- “What upper-division CS courses are open?”
- “Find me courses on Tuesday/Thursday only.”
- “Which open classes are 3 credit hours and in person?”
- “Help me make a schedule with no morning classes.”

## Important design choice

For the workshop, I would **not** use a database first unless your JSON is huge enough to feel slow. Start with:

- JSON file
- Python preprocessing
- in-memory indexes

Then later, if needed, move to SQLite. That keeps the FastMCP server simple.

## Recommendation

Your MVP should be:

- **Tools:** search, details, schedule filter
- **Resources:** schema/departments/query tips
- **Prompt:** schedule helper
- **Backend:** normalized JSON in memory

That is simple, fast, and very demoable.

Next step should be defining the exact tool signatures and FastMCP file structure.

[1]: https://gofastmcp.com/?utm_source=chatgpt.com "Welcome to FastMCP - FastMCP"
[2]: https://gofastmcp.com/servers/tools?utm_source=chatgpt.com "Tools"
[3]: https://gofastmcp.com/servers/server?utm_source=chatgpt.com "The FastMCP Server"
[4]: https://modelcontextprotocol.io/specification/2025-06-18/server/tools?utm_source=chatgpt.com "Tools"
[5]: https://modelcontextprotocol.io/specification/2025-06-18/server/resources?utm_source=chatgpt.com "Resources"
[6]: https://modelcontextprotocol.io/specification/2025-06-18/server/prompts?utm_source=chatgpt.com "Prompts"
[7]: https://gofastmcp.com/clients/client?utm_source=chatgpt.com "The FastMCP Client"
