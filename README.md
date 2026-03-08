# UT Course Explorer MCP

A local MCP server for exploring UT course data.

It provides:

- `search_courses`: Search courses with filters.
- `get_course_details`: Get details for one course.
- `resource://dataset-info`: Dataset metadata.
- `resource://departments`: Available departments.

## Prerequisites

- Python 3.10+
- A local copy of this project

## Clone The Project

```bash
git clone <YOUR_REPO_URL>
cd mcp-workshop
```

## Install Dependencies

Windows:

```powershell
pip install -r requirements.txt
```

macOS:

```bash
python3 -m pip install -r requirements.txt
```

## Test The Project

Windows:

```powershell
python -m pytest test_server.py
```

macOS:

```bash
python3 -m pytest test_server.py
```

## Run The Server Locally

Windows:

```powershell
python server.py
```

macOS:

```bash
python3 server.py
```

## Use With Claude Desktop

Claude Desktop connects to this project over `stdio`.

### Open The Config File

Open the Claude Desktop config in VS Code with one of these commands.

macOS:

```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Windows:

```powershell
code "$env:APPDATA\Claude\claude_desktop_config.json"
```

### macOS Config Example

Replace `<PROJECT_DIR>` with the absolute path to your local project folder.

```json
{
  "mcpServers": {
    "ut-course-explorer": {
      "command": "/usr/bin/python3",
      "args": [
        "<PROJECT_DIR>/server.py"
      ]
    }
  }
}
```

### Windows Config Example

Replace `<PROJECT_DIR>` with the absolute path to your local project folder.

```json
{
  "mcpServers": {
    "ut-course-explorer": {
      "command": "python",
      "args": [
        "<PROJECT_DIR>\\server.py"
      ]
    }
  }
}
```

## Notes

- Use an absolute path for `server.py`.
- Use absolute paths for the project folder.
- If `python` or `python3` does not work in Claude Desktop, replace it with the full path to your Python executable.
- Example macOS project path: `/Users/alex/code/mcp-workshop`
- Example Windows project path: `C:\\Users\\alex\\projects\\mcp-workshop`
- JSON must use escaped backslashes on Windows.
- Restart Claude Desktop after saving the config.

## Verify It Works

After restarting Claude Desktop, start a new chat and try:

- `What tools are available from ut-course-explorer?`
- `Search for computer science courses.`
- `Read the departments resource.`

## Troubleshooting

- If Claude Desktop shows the server failed to start, confirm Python is installed and `fastmcp` is installed.
- If nothing appears, check that the JSON is valid and the file path is correct.
- If the server starts in a terminal but not in Claude Desktop, use the full path to your Python executable instead of `python` or `python3`.
