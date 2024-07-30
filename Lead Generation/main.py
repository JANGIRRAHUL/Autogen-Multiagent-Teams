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

# Load environment variables from .env file
load_dotenv()
config_list = autogen.config_list_from_json(env_or_file="AOAI_CONFIG_LIST")

# Retrieve API key from environment variables
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def summarize(content, type):
    # Initialize the AzureChatOpenAI model
    llm = AzureChatOpenAI(temperature=0, deployment_name="autogen_studio_deployment")
    
    # Split the text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n"], chunk_size=10000, chunk_overlap=500)
    docs = text_splitter.create_documents([content])

    # Select the appropriate prompt based on the type
    if type == 'linkedin':
        map_prompt = prompts.linkedin_scraper_prompt
    elif type == 'website':
        map_prompt = prompts.website_scraper_prompt

    # Create a prompt template
    map_prompt_template = PromptTemplate(
        template=map_prompt, input_variables=["text"])

    # Load the summarize chain
    summary_chain = load_summarize_chain(
        llm=llm,
        chain_type='map_reduce',
        map_prompt=map_prompt_template,
        combine_prompt=map_prompt_template,
        verbose=True
    )

    # Run the summarize chain
    output = summary_chain.run(input_documents=docs)

    return output

def search(query):
    url = "https://google.serper.dev/search"

    payload = json.dumps({
        "q": query
    })
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()

def scrape_linkedin(linkedin_url: str):
    json_cache = 'json_cache.json'
    api_key = os.getenv('SCRAPPINGDOG_API_KEY')  # Ensure your API key is set
    api_endpoint = f'https://api.scrapingdog.com/linkedin/?api_key={api_key}&type=profile&linkId={linkedin_url}'
    
    # Try to fetch data from local cache
    try:
        with open(json_cache, 'r') as f:
            cached_data = json.load(f)
            for entry in cached_data:
                if entry['linkedin_url'] == linkedin_url:
                    print('Fetched data from Local Cache')
                    return summarize(json.dumps(entry['response']), 'linkedin')  # Convert dict to JSON string
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f'No local cache found...({e})')
        cached_data = []

    # If data not found in cache, make an API call
    print('Fetching new json data... (updating local cache)')
    response = requests.get(api_endpoint)
    
    if response.status_code == 200:
        new_data = {
            'linkedin_url': linkedin_url,
            'response': response.json()
        }
        cached_data.append(new_data)
        
        # Update the local cache with new data
        with open(json_cache, 'w') as f:
            json.dump(cached_data, f, indent=4)
        
        return summarize(json.dumps(new_data['response']), 'linkedin')  # Convert dict to JSON string
    else:
        print(f'Error fetching data: {response.status_code}')
        return None

def research(lead_data: dict):
    llm_config_research_li = {
        "functions": [
            {
                "name": "scrape_linkedin",
                "description": "scrape the LinkedIn profile and look for relevant information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "linkedin_url": {
                            "type": "string",
                            "description": "The LinkedIn URL to scrape",
                        }
                    },
                    "required": ["linkedin_url"],
                },
            },
            {
                "name": "search",
                "description": "google search for relevant information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Google search query",
                        }
                    },
                    "required": ["query"],
                },
            },
        ],
        "config_list": config_list
    }

    outbound_researcher = autogen.AssistantAgent(
        name="Outbound_researcher",
        system_message="Research the LinkedIn Profile of a potential lead and generate a detailed report; Add TERMINATE to the end of the research report;",
        llm_config=llm_config_research_li,
    )

    user_proxy = autogen.UserProxyAgent(
        name="User_proxy",
        code_execution_config={"last_n_messages": 2, "work_dir": "coding"},
        max_consecutive_auto_reply=3,
        default_auto_reply='Please continue with the task',
        is_termination_msg=lambda x: x.get("content", "") and x.get(
            "content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="TERMINATE",
        function_map={
            "scrape_linkedin": scrape_linkedin,
            "search": search,
        }
    )

    user_proxy.initiate_chat(outbound_researcher, message=f"Research this lead's website and LinkedIn Profile {str(lead_data)}")

    user_proxy.stop_reply_at_receive(outbound_researcher)
    user_proxy.send(
        "Give me the research report that just generated again, return ONLY the report", outbound_researcher)

    # return the last message the expert received
    return user_proxy.last_message()["content"]

def create_outreach_msg(research_material, lead_data: dict):
    outbound_strategist = autogen.AssistantAgent(
        name="outbound_strategist",
        system_message="You are a senior outbound strategist responsible for analyzing research material and coming up with the best cold email structure with relevant personalization points",
        llm_config={"config_list": config_list},
    )

    outbound_copywriter = autogen.AssistantAgent(
        name="outbound_copywriter",
        system_message="You are a professional AI copywriter who is writing cold emails for leads. You will write a short cold email based on the structure provided by the outbound strategist, and feedback from the reviewer; After 2 rounds of content iteration, add TERMINATE to the end of the message",
        llm_config={"config_list": config_list},
    )

    reviewer = autogen.AssistantAgent(
        name="reviewer",
        system_message="You are a world-class cold email critic, you will review & critique the cold email and provide feedback to the writer. After 2 rounds of content iteration, add TERMINATE to the end of the message",
        llm_config={"config_list": config_list},
    )

    user_proxy = autogen.UserProxyAgent(
        name="admin",
        system_message="A human admin. Interact with outbound strategist to discuss the structure. Actual writing needs to be approved by this admin.",
        code_execution_config=False,
        is_termination_msg=lambda x: x.get("content", "") and x.get(
            "content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="TERMINATE",
    )

    groupchat = autogen.GroupChat(
        agents=[user_proxy, outbound_strategist, outbound_copywriter, reviewer],
        messages=[],
        max_round=20)
    manager = autogen.GroupChatManager(groupchat=groupchat)

    user_proxy.initiate_chat(
        manager, message=f"Write a personalized cold email to {lead_data}, here are the material: {research_material}")

    user_proxy.stop_reply_at_receive(manager)
    user_proxy.send(
        "Give me the cold email that just generated again, return ONLY the cold email, and add TERMINATE in the end of the message", manager)

    # return the last message the expert received
    return user_proxy.last_message()["content"]

def send_linkedin_message(linkedin_url: str, message: str):
    api_key = os.getenv('LINKEDIN_API_KEY')  # Ensure your API key is set
    api_endpoint = f'https://api.linkedin.com/v2/messages'
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "recipients": [{"person": {"id": linkedin_url}}],  # Ensure correct payload structure
        "message": {"text": message}
    }
    
    response = requests.post(api_endpoint, headers=headers, json=payload)
    
    if response.status_code == 201:
        print('Message sent successfully')
    else:
        print(f'Error sending message: {response.status_code}')
        return None

def send_message_to_linkedin_lead(lead_data: dict, message: str):
    linkedin_url = lead_data.get('LinkedIn URL')
    if linkedin_url:
        send_linkedin_message(linkedin_url, message)
    else:
        print("LinkedIn URL not found in lead data")

llm_config_outbound_writing_assistant = {
    "functions": [
        {
            "name": "research",
            "description": "research about a given lead, return the research material in report format",
            "parameters": {
                    "type": "object",
                    "properties": {
                        "lead_data": {
                            "type": "object",
                            "description": "The information about a lead",
                        }
                    },
                "required": ["lead_data"],
            },
        },
        {
            "name": "create_outreach_msg",
            "description": "Write an outreach message based on the given research material & lead information",
            "parameters": {
                    "type": "object",
                    "properties": {
                        "research_material": {
                            "type": "string",
                            "description": "research material of a given topic, including reference links when available",
                        },
                        "lead_data": {
                            "type": "object",
                            "description": "A dictionary containing lead data",
                        }
                    },
                "required": ["research_material", "lead_data"],
            },
        },
        {
            "name": "send_message_to_linkedin_lead",
            "description": "Send a message to a LinkedIn lead",
            "parameters": {
                    "type": "object",
                    "properties": {
                        "lead_data": {
                            "type": "object",
                            "description": "The information about a lead",
                        },
                        "message": {
                            "type": "string",
                            "description": "The message to send to the LinkedIn lead",
                        }
                    },
                "required": ["lead_data", "message"],
            },
        },
    ],
    "config_list": config_list}


outbound_writing_assistant = autogen.AssistantAgent(
    name="writing_assistant",
    system_message="You are an outbound assistant, you can use research function to collect information from a lead, and then use create_outreach_msg function to write a personalized outreach message; Reply TERMINATE when your task is done",
    llm_config=llm_config_outbound_writing_assistant,
)

user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    human_input_mode="TERMINATE",
    function_map={
        "create_outreach_msg": create_outreach_msg,
        "research": research,
        "send_message_to_linkedin_lead": send_message_to_linkedin_lead,
    }
)

# Generate Lead Data
# lead_data = {
#     'First Name': 'Chris Wess',
#     'Company Name': 'Wintellisys',
#     'Website URL': 'https://wintellisys.com/',
#     'LinkedIn URL': 'chriswess'
# }

lead_data = {
    'First Name': 'Rahul Kurkure',
    'Company Name': 'cloud.in',
    'Website URL': 'https://www.cloud.in/',
    'LinkedIn URL': 'rahulskurkure'
}

# lead_data = {
#     'First Name': 'Ajinkya Naik',
#     'LinkedIn URL': 'ajinkya-naik-003236b1'
# }

# Research the lead
research_material = user_proxy.initiate_chat(
    outbound_writing_assistant, message=f"research {str({'lead_data': lead_data})}")

# Ensure research_material is correctly retrieved
research_material = user_proxy.last_message()["content"]

# Debug the create_outreach_msg function
def debug_create_outreach_msg(research_material, lead_data: dict):
    try:
        result = create_outreach_msg(research_material, lead_data)
        print("Function executed successfully.")
        return result
    except Exception as e:
        print(f"Error: {e}")

# Debug the create_outreach_msg function
debug_create_outreach_msg(research_material, lead_data)

# Ensure the last drafted message is correctly retrieved
last_drafted_message = user_proxy.last_message()["content"]

# Send the last drafted message to the LinkedIn lead
user_proxy.initiate_chat(
    outbound_writing_assistant, message=f"send_message_to_linkedin_lead {str({'lead_data': lead_data, 'message': last_drafted_message})}")  