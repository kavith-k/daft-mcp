# Daft MCP Server

An MCP server built on top of the [daftlistings](https://github.com/AnthonyBloomer/daftlistings) library to search for rental properties on [daft.ie](https://daft.ie) using an MCP Client. It exposes a tool, `find_rental_properties`, which can be used to find properties based on criteria such as location, maximum price, number of bedrooms, search radius, and property type.

## Intallation

### 1. Create a Python virtual environment
```bash
python -m venv .venv
```

### 2. Install the required dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup MCP Client

This MCP server uses stdio at the moment, so you'd have to configure your client accordingly. This is how you'd set it up to be used via [goose](https://github.com/block/goose):

1. Advanced settings (⌘,) > Add custom extension
2. Give the extension an appropriate name
3. Set Type to "STDIO"
4. Command needs to basically run the python script (daft_mcp_server.py) using the version of Python in your virtual environment. So, this would look like `<path-to-python-in-virtual-env> <path-to-daft_mcp_server.py>`. For example here's my command: `/Users/kavith/Projects/daft-mcp/.venv/bin/python3 /Users/kavith/Projects/daft-mcp/daft_mcp_server.py`

## Usage

This is the easy bit. You can ask your LLM to list rental properties around an area in Ireland, and it should be able to help. The tool requires the location, max_price, num_beds; so if you don't provide them explicitly in your first prompt, the model will come back and ask for the additional information :)

![Screenshot showing the MCP server working](./screenshots/screenshot-1.png)
![Another screenshot showing the MCP server working](./screenshots/screenshot-2.png)