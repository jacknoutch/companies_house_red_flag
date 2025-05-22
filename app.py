# Standard library imports
import os

# Third party imports
import requests
from dotenv import load_dotenv
from flask import Flask, request

app = Flask(__name__)

load_dotenv()

# Get the environment variable for the Companies House API key
companies_house_api_key = os.getenv('COMPANIES_HOUSE_API_KEY')

@app.route('/', methods=['GET', 'POST'])
def hello_world():

    if request.method == 'POST':
    
        company_number = os.getenv('COMPANY_ID')
        api_url = f"https://api.company-information.service.gov.uk/company/{company_number}/filing-history"

        response = requests.get(api_url, auth=(companies_house_api_key, ''))
        data = response.json()

        return f"API response: {data}"

    return "GET request received"

@app.route('/officers/<string:query>', methods=['GET'])
def officer(query):
    api_url = f"https://api.company-information.service.gov.uk/search/officers"
    response = requests.get(
        api_url,
        params={"q": query,},
        auth=(companies_house_api_key, '')
    )
    data = response.json()

    return f"API response: {data}"