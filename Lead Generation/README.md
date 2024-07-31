# Outbound Writing Assistant

This repository contains a Python script for automating the process of researching leads and generating personalized outreach messages for LinkedIn using various APIs and the Autogen framework.

## Prerequisites

- Python 3.8+
- Required Python libraries (listed in `requirements.txt`)
- Environment variables set up for:
  - `SERPER_API_KEY`
  - `SCRAPPINGDOG_API_KEY`
  - `LINKEDIN_API_KEY`

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/outbound-writing-assistant.git
   cd outbound-writing-assistant
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the root directory with the following content:
   ```env
   SERPER_API_KEY=your_serper_api_key
   SCRAPPINGDOG_API_KEY=your_scrappingdog_api_key
   LINKEDIN_API_KEY=your_linkedin_api_key
   ```

## Code Overview

### `main.py`

This script automates lead research and outreach tasks. It includes the following components:

#### Imports

```python
import requests
import json
import autogen
from langchain_community.chat_models import AzureChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
import prompts
from dotenv import load_dotenv
import os
```

#### Load Environment Variables

```python
load_dotenv()
config_list = autogen.config_list_from_json(env_or_file="AOAI_CONFIG_LIST")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
```

#### Functions

- **`summarize(content, type)`**
  - Summarizes content based on type (`linkedin` or `website`) using Azure OpenAI.
  
  ```python
  def summarize(content, type):
      ...
  ```

- **`search(query)`**
  - Performs a Google search using Serper API.

  ```python
  def search(query):
      ...
  ```

- **`scrape_linkedin(linkedin_url: str)`**
  - Scrapes LinkedIn profile data using Scrappingdog API. Fetches data from local cache if available.

  ```python
  def scrape_linkedin(linkedin_url: str):
      ...
  ```

- **`research(lead_data: dict)`**
  - Researches a lead's website and LinkedIn profile, generating a detailed report using Autogen agents.

  ```python
  def research(lead_data: dict):
      ...
  ```

- **`create_outreach_msg(research_material, lead_data: dict)`**
  - Creates a personalized cold email based on research material and lead information.

  ```python
  def create_outreach_msg(research_material, lead_data: dict):
      ...
  ```

- **`send_linkedin_message(linkedin_url: str, message: str)`**
  - Sends a message to a LinkedIn lead using LinkedIn API.

  ```python
  def send_linkedin_message(linkedin_url: str, message: str):
      ...
  ```

- **`send_message_to_linkedin_lead(lead_data: dict, message: str)`**
  - Sends the generated message to the LinkedIn lead.

  ```python
  def send_message_to_linkedin_lead(lead_data: dict, message: str):
      ...
  ```

#### Example Lead Data

```python
lead_data = {
    'First Name': 'Rahul Kurkure',
    'Company Name': 'cloud.in',
    'Website URL': 'https://www.cloud.in/',
    'LinkedIn URL': 'rahulskurkure'
}
```

#### Execution Flow

1. **Research Lead:**
   ```python
   research_material = user_proxy.initiate_chat(
       outbound_writing_assistant, message=f"research {str({'lead_data': lead_data})}")
   ```

2. **Create Outreach Message:**
   ```python
   def debug_create_outreach_msg(research_material, lead_data: dict):
       try:
           result = create_outreach_msg(research_material, lead_data)
           print("Function executed successfully.")
           return result
       except Exception as e:
           print(f"Error: {e}")
   ```

3. **Send Message to LinkedIn Lead:**
   ```python
   user_proxy.initiate_chat(
       outbound_writing_assistant, message=f"send_message_to_linkedin_lead {str({'lead_data': lead_data, 'message': last_drafted_message})}")
   ```

## Usage

1. **Update Lead Data:**
   Modify the `lead_data` dictionary with the lead's information.

2. **Run the Script:**
   Execute the script with:
   ```bash
   python main.py
   ```

## Debugging

- **Debugging `create_outreach_msg`:**
  - Includes a function to debug the `create_outreach_msg` function to ensure it works correctly.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Acknowledgments

- Thanks to the developers of the Autogen framework and the APIs used in this project.
```
