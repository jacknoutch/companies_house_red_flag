# Standard library imports
import os

# Third party imports
import requests
from dotenv import load_dotenv
from flask import Flask

app = Flask(__name__)

load_dotenv()

# Get the environment variable for the Companies House API key
companies_house_api_key = os.getenv('COMPANIES_HOUSE_API_KEY')

@app.route('/')
def hello_world():
    
    company_number = os.getenv('COMPANY_ID')
    api_url = f"https://api.company-information.service.gov.uk/company/{company_number}"

    response = requests.get(api_url, auth=(companies_house_api_key, ''))
    data = response.json()

    return f"API response: {data}"