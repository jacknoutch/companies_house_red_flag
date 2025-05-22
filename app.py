# Standard library imports
import os

# Third party imports
import requests
from dotenv import load_dotenv
from flask import Flask, redirect, request, render_template

app = Flask(__name__)

load_dotenv()

# Get the environment variable for the Companies House API key
companies_house_api_key = os.getenv('COMPANIES_HOUSE_API_KEY')


# Custom filtesr
@app.template_filter('format_date')
def format_date(date_str):
    """Format date string from YYYY-MM-DD to DD MMM YYYY."""
    if date_str:
        # Split the date string into components
        year, month, day = date_str.split('-')
        # Create a dictionary to map month numbers to month names
        month_names = {
            '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
            '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
            '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
        }
        # Format the date string
        date_str = f"{day} {month_names[month]} {year}"
    return date_str


@app.route('/', methods=['GET'])
@app.route('/<string:company_number>', methods=['GET'])
def index(company_number=None):

    data = None

    get_company_url = f"https://api.company-information.service.gov.uk/company/{company_number}"

    response = requests.get(get_company_url, auth=(companies_house_api_key, ''))
    data = response.json()

    company_name = data.get('company_name')
    previous_company_names = data.get('previous_company_names', [])

    get_company_officers_url = f"https://api.company-information.service.gov.uk/company/{company_number}/officers"
    officers_response = requests.get(get_company_officers_url, auth=(companies_house_api_key, ''))
    officers_data = officers_response.json()

    context = {
        'company_data': data,
        'company_name': company_name,
        'previous_company_names': previous_company_names,
        'officers_data': officers_data,
    }
    
    return render_template('index.html', context=context)



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


@app.route('/companies/officer/<string:officer_id>', methods=['GET'])
def officer_companies(officer_id):
    api_url = f"https://api.company-information.service.gov.uk/officers/{officer_id}/appointments"
    response = requests.get(api_url, auth=(companies_house_api_key, ''))
    data = response.json()

    return f"API response: {data}"


@app.route('/handle_data', methods=['POST'])
def handle_data():
    # Handle the data sent from the form
    data = request.form['company_number']
    # Process the data as needed
    return redirect('/' + data)