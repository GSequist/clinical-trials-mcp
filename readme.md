# Clinical Trials MCP Search Tool

## Overview

This tool allows you to search and analyze hundreds of clinical trials from multiple sources (EU Clinical Trials and ClinicalTrials.gov) using Anthropic's Model Context Protocol (MCP) architecture. Unlike traditional chatbots that process small conversational turns, this MCP implementation:

- **Processes hundreds of trials simultaneously** by batching requests and distributing analysis
- **Uses sophisticated parsers** to extract and structure complex nested trial data
- **Leverages smaller, efficient models** to synthesize results while keeping costs low
- **Connects related information across trials** to surface insights human researchers might miss

The system acts as an intelligent research assistant, helping users quickly find relevant clinical trials based on conditions, treatments, locations, and other criteria.

## Architecture

The system consists of three main components:

1. **Clinical Trials MCP**: The main API interface that handles requests and responses
2. **Parsers**: Sophisticated extractors that transform complex trial data into structured formats
3. **Model Interface**: Handles communication with Claude and other Anthropic models

This architecture enables the system to process large batches of clinical trial data efficiently while keeping the analysis contextual and relevant to the user's specific query.

## Installation

### Prerequisites

- Python 3.8+
- pip package manager
- Anthropic API key
- Claude desktop app (for MCP integration)

### Setup Steps

1. Clone the repository.

2. Create and activate a virtual environment (recommended):

```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up your Anthropic API key:

   a. Get an API key from [Anthropic Console](https://console.anthropic.com/)
   
   b. Change `.env.example` file to .env and add your new API key:
   
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

## Setting up MCP with Claude

1. Install Claude desktop application if you haven't already.

2. Find Claude's configuration file:
   - MacOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%AppData%\Claude\claude_desktop_config.json`

* if you cannot find this file, when Claude opens click on Claude and system settings (these are different settings that inside the application) see https://modelcontextprotocol.io/quickstart/user

3. Add your MCP configuration to the JSON file:

```json
{
  "mcps": [
    {
      "name": "clinical-trials-mcp",
      "path": "which python output path goes here", 
      "args": ["clinical_trials_mcp_.py"]
    }
  ]
}
```

4. Get the correct Python path for your MCP:

```bash
which python  # On macOS/Linux
where python  # On Windows
```

5. Copy this path to the "path" field in the claude_desktop_config.json file.

6. Restart Claude.

## Usage

1. Start a conversation in Claude and ask about clinical trials:

```
Find me phase 3 trials for multiple myeloma in Europe
```

2. Claude will use the MCP to search for and analyze relevant trials.

3. You can request more specific details about trials of interest:

```
Can you get me more details about trial NCT04916639?
```

## Available Features

- **Trial search**: Find trials based on condition, location, sponsor, and status
- **Detailed trial information**: Get comprehensive details on any trial by ID
- **Intelligent analysis**: Receive summaries of which trials are most relevant to your query
- **Multi-source search**: Search both EU Clinical Trials and ClinicalTrials.gov simultaneously
