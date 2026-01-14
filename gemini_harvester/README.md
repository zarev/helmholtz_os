## Gemini Harvester

### gemini_harvester.py analyzes a given URL and extracts:
- up to 5 open-access papers, and
- up to 5 non-open-access publications.

A publication is classified as non-open-access if there is insufficient evidence that it is openly accessible. The harvester returns its results in JSON format

### How It Works
- The harvester uses Gemini CLI under the hood, which in turn leverages Chrome DevTools via the Model Context Protocol (MCP) to analyze web content.
- Because the extraction is performed by a large language model, the results should be treated as assistive and verified manually when accuracy is critical.

### Authentication
To run the harvester, you must provide a Gemini API key. The key can be exported as an environment variable: export GEMINI_API_KEY=your_key_here

### Model Configuration
By default, the harvester uses the gemini-2.5-flash model. You can change the model by editing the settings.json file, which is the configuration file for the Gemini CLI. This file is located in the working directory, at the same level as gemini_harvester.py.

Detailed documentation on configuring the Gemini CLI can be found here: https://geminicli.com/docs/get-started/configuration/

### Usage Example
python gemini_harvester.py https://www.maxiv.lu.se/science/publications/

### Important Notes
Since the harvester relies on an LLM for document identification and classification, all extracted information should be reviewed and validated before use.