# Standard library imports
import os

# Third party imports
import requests
from dotenv import load_dotenv
from flask import flash, Flask, redirect, request, render_template, url_for

app = Flask(__name__)

# Set a secret key for the Flask app
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Set environment variables
load_dotenv()
companies_house_api_key = os.getenv('COMPANIES_HOUSE_API_KEY')

# Custom filters
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
@app.route('/company/<string:company_number>', methods=['GET'])
def index(company_number=None):

    company_data = None

    get_company_url = f"https://api.company-information.service.gov.uk/company/{company_number}"

    response = requests.get(get_company_url, auth=(companies_house_api_key, ''))
    company_data = response.json()

    company_name = company_data.get('company_name')
    previous_company_names = company_data.get('previous_company_names', [])

    get_company_officers_url = f"https://api.company-information.service.gov.uk/company/{company_number}/officers"
    officers_response = requests.get(get_company_officers_url, auth=(companies_house_api_key, ''))
    officers_data = officers_response.json()['items']

    company_events = get_company_events(company_data)
    officer_events = get_officer_events(officers_data)

    timeline_events = [
        event for event in company_events + officer_events
    ]

    timeline_events.sort(key=lambda x: x['date'])

    context = {
        'company_data': company_data,
        'company_name': company_name,
        'previous_company_names': previous_company_names,
        'officers_data': officers_data,
        'timeline_data': timeline_events,
    }

    return render_template('index.html', context=context)



@app.route('/officers/<string:officer_id>/appointments', methods=['GET'])
def officer(officer_id):
    api_url = f"https://api.company-information.service.gov.uk/officers/{officer_id}/appointments"
    response = requests.get(
        api_url,
        auth=(companies_house_api_key, '')
    )
    officer_data = response.json()

    context = {
        "officer_data": officer_data,
    }

    return render_template("appointments.html", context=context)

@app.route('/companies/officer/<string:officer_id>', methods=['GET'])
def officer_companies(officer_id):
    api_url = f"https://api.company-information.service.gov.uk/officers/{officer_id}/appointments"
    response = requests.get(api_url, auth=(companies_house_api_key, ''))
    officer_data = response.json()['items']
    officer_data.sort(key=lambda x: x['date of birth']['year'] if 'date of birth' in x and 'year' in x['date of birth'] else 0)

    context = {
        "officer_data": officer_data,
    }

    return render_template("index.html", context=context)


@app.route('/search/officer/<string:query>', methods=['GET'])
def search_officer(query):
    api_url = f"https://api.company-information.service.gov.uk/search/officers"
    response = requests.get(
        api_url,
        params={
            "q": query,
            "items_per_page": 1000,
        },
        auth=(companies_house_api_key, '')
    )
    officer_data = response.json()['items']
    officer_data = create_sort_dob_key(officer_data)
    officer_data.sort(key=lambda x: x['dob_sort_key'])

    context = {
        "officer_data": officer_data
    }

    return render_template("search.html", context=context)


@app.route('/search/company/<string:query>', methods=['GET'])
def search_company(query):
    api_url = f"https://api.company-information.service.gov.uk/search/companies"
    response = requests.get(
        api_url,
        params={
            "q": query,
            "items_per_page": 1000,
        },
        auth=(companies_house_api_key, '')
    )
    company_data = response.json()

    context = {
        "company_data": company_data
    }

    return render_template("search.html", context=context)


@app.route('/handle_data', methods=['POST'])
def handle_data():
    
    company_number = request.form.get('company_number')
    if company_number:
        
        # Validate the company number; it must be a string of 8 characters
        if not isinstance(company_number, str) or len(company_number) != 8:
            flash("Invalid company number. It must be a string of 8 characters.")
            return redirect(url_for('index'))
        
        return redirect(url_for('index', company_number=company_number))

    company_name = request.form.get('company_name')
    if company_name:
    
        return redirect(url_for('search_company', query=company_name))
    
    officer_name = request.form.get('officer_name')
    if officer_name:

        return redirect(url_for('search_officer', query=officer_name))
    
    flash("Please enter valid form details and resubmit.")
    return redirect(url_for('index'))


def get_company_events(company_data):
    events = []
    if 'date_of_creation' in company_data:
        events.append({
            "date": company_data.get('date_of_creation'),
            "description": "Company created"
        })

    if 'previous_company_names' in company_data:
        for name_change in company_data['previous_company_names']:
            events.append({
                "date": name_change.get('effective_from'),
                "description": f"Company name changed to: {name_change.get('name')}"
            })
            events.append({
                "date": name_change.get('ceased_on'),
                "description": f"Company name changed from: {name_change.get('name')}"
            })
    return events


def get_officer_events(officer_data):
    events = []
    for officer in officer_data:
        if 'appointed_on' in officer:
            events.append({
                "date": officer.get('appointed_on'),
                "description": f"Appointed as officer of company: {officer.get('name')}"
            })
        if 'resigned_on' in officer:
            events.append({
                "date": officer.get('resigned_on'),
                "description": f"Resigned as officer of company: {officer.get('name')}"
            })

    return events


def create_sort_dob_key(officers):
    for officer in officers:
        year, month = extract_dob(officer)
        officer['dob_sort_key'] = (year, month)
    return officers


def extract_dob(officer):
    if 'date_of_birth' in officer and 'year' in officer['date_of_birth'] and 'month' in officer['date_of_birth']:
        return officer['date_of_birth']['year'], officer['date_of_birth']['month']
    return 0, 0