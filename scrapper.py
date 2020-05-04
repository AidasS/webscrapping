from flask import Flask
from flask import request
from flask_restful import Api, Resource, reqparse
from requests import get
from requests import post
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import datetime
import json

app = Flask(__name__)
api = Api(app)
    

def get_company_url(code:str)->str:
    """
    Method for retrieving URL in Rekvizitai.lt website of any commercial company in Lithunia by company code
    Arguments:
        code (str) -- Litnianian company code
    Returns:
        str -- ural of desired company
    """
    params = {'name':'', 'city':0,'word':'','code':code,'catUrlKey':'','ok':'','resetFilter':0,'order':1}
    url = "https://rekvizitai.vz.lt/imones/1"
    try:
        with closing(post(url, params)) as response:
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup.find_all("div", class_="info")[0].find('a').get('href')
            else:
                return None
    except RequestException as e:
        raise RequestException(f'Error during requests to {url} : {str(e)}')
         

def get_url_content(url:str):
    """
    Method returns raw html content from given url
    Arguments:
        url (str)
    Returns:
        str -- raw html from given url
    """
    try:
        with closing(get(url, stream=True)) as reply:
            if reply.status_code == 200:
                return reply.content
            else:
                return None
    except RequestException as e:
        raise RequestException(f'Error during requests to {url} : {str(e)}')

class CompanyModel():

    name:str
    code:str
    address:str
    website:str
    employees:int
    sodracode:int
    averagesalary:float
    turnoveryear:int
    turnoverrange:str
    cardate:str
    cars:int
    regaddress:str
    regdate: datetime
    legalform:str
    status:str
    industry:str

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

def clean_string(text:str)->str:
    return text.get_text().replace('\r', '').replace('\t', '').replace('\n','')

def parse_content(raw_html):

    company = CompanyModel()

    html_soup1 = BeautifulSoup(raw_html[0], 'html.parser')
    table=html_soup1.find('div',class_='info')
    html_soup2 = BeautifulSoup(raw_html[1], 'html.parser')
    table2=html_soup2.find('div',class_='info')
    

    company.name = html_soup1.find("div", class_="name floatLeft").find('h1').get_text()
    company.code = table.find("td", text="Įmonės kodas").find_next_sibling("td").text
    company.address = table.find("td", text="Adresas").find_next_sibling("td").text
    company.website = table.find("td", text="Tinklalapis").find_next_sibling("td").text if table.find("td", text="Tinklalapis") else None
    company.employees = clean_string(table.find("td", text="Darbuotojai").find_next_sibling("td")).split(' ')[0] if table.find("td", text="Darbuotojai") else 0
    company.sodracode = clean_string(table.find("td", text="SD draudėjo kodas").find_next_sibling("td")).split(' ') if table.find("td", text="SD draudėjo kodas") else 0
    company.averagesalary = clean_string(table.find("td", text="Vidutinis atlyginimas").find_next_sibling("td")).split(" €")[0].replace(",", ".") if table.find("td", text="Vidutinis atlyginimas") else 0
    company.turnoverrange = clean_string(table.find("td", text="Pardavimo pajamos").find_next_sibling("td")).split(": ")[1].split(" €")[0] if table.find("td", text="Pardavimo pajamos") else 0
    company.turnoveryear = clean_string(table.find("td", text="Pardavimo pajamos").find_next_sibling("td")).split(": ")[0] if table.find("td", text="Pardavimo pajamos") else 0
    company.cardate = clean_string(table.find("td", text="Transportas").find_next_sibling("td")).split(": ")[0] if table.find("td", text="Transportas") else 0
    company.cars = clean_string(table.find("td", text="Transportas").find_next_sibling("td")).split(': ')[1].split(' ')[0] if table.find("td", text="Transportas") else 0

    company.regaddress = clean_string(table2.find("td", text="Registracijos adresas").find_next_sibling("td")) if table2.find("td", text="Registracijos adresas") else 0
    company.regdate = clean_string(table2.find("td", text="Įregistruotas").find_next_sibling("td")) if table2.find("td", text="Įregistruotas") else 0
    company.legalform = clean_string(table2.find("td", text="Teisinė forma").find_next_sibling("td")) if table2.find("td", text="Teisinė forma") else 0
    company.status = clean_string(table2.find("td", text="Teisinis statusas").find_next_sibling("td")) if table2.find("td", text="Teisinis statusas") else 0

    industry = table2.find("td",  text="EVRK 2 red. veikla").find_next_sibling("td") if table2.find("td", text="EVRK 2 red. veikla") else None
    for match in industry.find_all('span'):
        match.replaceWith('')
    company.industry = clean_string(industry)

    return company





class Company(Resource):
    def post(self):
        """
        POST Request
        Arguments:
            {} -- company code egz.: {"code", "304232351"}
        Returns:
            {} -- parameters and values about requested company

        """
        try:
            json_data = request.get_json(force=True)
            if "code" not in json_data or len(json_data["code"]) != 9:
                return "Wrong parameter", 400

            url = get_company_url(json_data["code"])

            url_list = []
            html_list = []
            url_list.append(url)
            url_list.append(url+'juridinis-asmuo/')

            for u in url_list:
                raw_html = get_url_content(u)
                if raw_html == None or len(raw_html) == 0:
                    return f"Company with code {json_data['code']} was not found", 400
                html_list.append(raw_html)

            result = parse_content(html_list).toJSON()

            return result, 200
        except Exception as e:
            return e, 400
        
api.add_resource(Company, "/getdata/")
if __name__ == '__main__':
    app.run(debug=True)



    

