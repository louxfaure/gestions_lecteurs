# -*- coding: utf-8 -*-
import os
# external imports
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
import logging
import xml.etree.ElementTree as ET
import time
import sys
from math import *


__version__ = '0.1.0'
__api_version__ = 'v1'



FORMATS = {
    'json': 'application/json',
    'xml': 'application/xml'
}

RESOURCES = {
    'get_user' : 'users/{user_id}?view={user_view}&expand={user_expand}',
    'get_user_with_id_type' : 'users/{user_id}?user_id_type={user_id_type}&view={user_view}&expand={user_expand}',
    'retrieve_user_by_id' : 'users?limit=10&offset=0&q=primary_id~{user_id}',
    'delete_user' : 'users/{user_id}',
    'update_user' : 'users/{user_id}?user_id_type=all_unique&send_pin_number_letter=false&recalculate_roles=true&registration_rules=false',
    'distribute_user' : 'users?social_authentication=false&send_pin_number_letter=false&source_institution_code=33PUDB_NETWORK&source_user_id={user_id}&registration_rules=false',
    'create_user' : 'users?social_authentication=false&send_pin_number_letter=false&registration_rules=false'
}
NS = {'sru': 'http://www.loc.gov/zing/srw/',
        'marc': 'http://www.loc.gov/MARC21/slim',
        'xmlb' : 'http://com/exlibris/urm/general/xmlbeans'
         }


class Users(object):
    """A set of function for interact with Alma Apis in area "User"
    """

    def __init__(self, apikey ,service='AlmaPy'):
        if apikey is None:
            raise Exception("Please supply an API key")
        self.apikey = apikey
        self.endpoint = 'https://api-eu.hosted.exlibrisgroup.com'
        self.service = service
        self.logger = logging.getLogger(__name__)

    @property
    #Construit la requête et met en forme les réponses
    def baseurl(self):
        """Construct base Url for Alma Api
        
        Returns:
            string -- Alma Base URL
        """
        return '{}/almaws/{}/'.format(self.endpoint, __api_version__)

    def fullurl(self, resource, ids={}):
        self.logger.debug(self.baseurl + RESOURCES[resource].format(**ids))
        return self.baseurl + RESOURCES[resource].format(**ids)

    def headers(self, accept='json', content_type=None):
        headers = {
            "User-Agent": "pyalma/{}".format(__version__),
            "Authorization": "apikey {}".format(self.apikey),
            "Accept": FORMATS[accept]
        }
        if content_type is not None:
            headers['Content-Type'] = FORMATS[content_type]
        return headers
    def get_error_message(self, response, accept):
        """Extract error code & error message of an API response
        
        Arguments:
            response {object} -- API REsponse
        
        Returns:
            int -- error code
            str -- error message
        """
        error_code, error_message = '',''
        if accept == 'xml':
            root = ET.fromstring(response.text)
            error_message = root.find(".//xmlb:errorMessage",NS).text if root.find(".//xmlb:errorMessage",NS).text else response.text 
            error_code = root.find(".//xmlb:errorCode",NS).text if root.find(".//xmlb:errorCode",NS).text else '???'
        else :
            try :
             content = response.json()
            except : 
                # Parfois l'Api répond avec du xml même si l'en tête demande du Json cas des erreurs de clefs d'API 
                root = ET.fromstring(response.text)
                error_message = root.find(".//xmlb:errorMessage",NS).text if root.find(".//xmlb:errorMessage",NS).text else response.text 
                error_code = root.find(".//xmlb:errorCode",NS).text if root.find(".//xmlb:errorCode",NS).text else '???'
                return error_code, error_message 
            error_message = content['errorList']['error'][0]['errorMessage']
            error_code = content['errorList']['error'][0]['errorCode']
        return error_code, error_message
    
    def request(self, httpmethod, resource, ids, params={}, data=None,
                accept='json', content_type=None, nb_tries=0, in_url=None):
        #20190905 retry request 3 time s in case of requests.exceptions.ConnectionError
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        response = session.request(
            method=httpmethod,
            headers=self.headers(accept=accept, content_type=content_type),
            url= self.fullurl(resource, ids) if in_url is None else in_url,
            params=params,
            data=data)
        
        try:
            response.raise_for_status()  
        except requests.exceptions.HTTPError:
            error_code, error_message= self.get_error_message(response,accept)
            self.logger.error("Alma_Apis :: HTTP Status: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
            if error_code in ['401861','401890'] :
                return 'Error', error_code
            return 'Error', "{} -- {}".format(error_code, error_message)
        except requests.exceptions.ConnectionError:
            error_code, error_message= self.get_error_message(response,accept)
            self.logger.error("Alma_Apis :: Connection Error: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
            return 'Error', "{} -- {}".format(error_code, error_message)
        except requests.exceptions.RequestException:
            error_code, error_message= self.get_error_message(response,accept)
            self.logger.error("Alma_Apis :: Connection Error: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
            return 'Error', "{} -- {}".format(error_code, error_message)
        return "Success", response

            

    
    def extract_content(self, response):
        ctype = response.headers['Content-Type']
        if 'json' in ctype:
            return response.json()
        else:
            return response.content.decode('utf-8')


    def distribute_user(self, user_id, data, content_type='json', accept='json'):
        """Distribue un lecteur de la zone réseau dans l'institution.

        Args:
            user_id (_type_): primary_id du lecteur
            data (_type_): retour de get_user en json sur la NZ
            content_type (str, optional): _description_. Defaults to 'json'.
            accept (str, optional): _description_. Defaults to 'json'.

        Returns:
            _type_: _description_
        """


        status, response = self.request('POST', 'distribute_user', 
                                {'user_id': user_id},
                                data=data, content_type = content_type, accept = accept)
        self.logger.debug(response)                        
        if status == 'Error':
            return status, response
        else:
            return status, self.extract_content(response)

    def create_user(self, user_id, data, content_type='json', accept='json'):
        """Créé un lecteur de la zone réseau dans l'institution.

        Args:
            user_id (_type_): primary_id du lecteur
            data (_type_): retour de get_user en json sur la NZ
            content_type (str, optional): _description_. Defaults to 'json'.
            accept (str, optional): _description_. Defaults to 'json'.

        Returns:
            _type_: _description_
        """
        status, response = self.request('POST', 'create_user',
                                {'user_id': user_id}, 
                                data=data, content_type = content_type, accept = accept)
        if status == 'Error':
            return status, response
        else:
            return status, self.extract_content(response)

    def get_user(self, user_id, user_data = None, user_id_type='PRIMARYIDENTIFIER' , user_expand='loans,requests', user_view='brief',accept='json'):
        """Retourne un usager à partir d'un identifiant
        
        Arguments:
            user_id {str} -- identifiant du lecteur
        
        Keyword Arguments:
            user_id_type {str} -- type d'identifiant sure lequel effectué la recherche BARCODE ou PRIMARYIDENTIFIER (default: {'PRIMARYIDENTIFIER'})
            user_expand {str} -- informations supllémentaires: (default: {'loans'})
            user_view {str} -- affichage complet full ou brief  (default: {'brief'})
            accept {str} -- format de sortie xml ou json (default: {'json'})
        
        Returns:
            status {str} -- Success or Error
            response {str} -- Message d'erreurs ou Lecteur 
        """
        url = 'get_user'
        if  user_id_type != 'PRIMARYIDENTIFIER' :
            url = 'get_user_with_id_type'
        status,response = self.request('GET', url,
                                {'user_id' : user_id,
                                'user_id_type' : user_id_type,
                                'user_view' : user_view,
                                'user_expand' : user_expand},
                                accept=accept)
        if status == 'Success':
            return status, self.extract_content(response)
        else:
            return status, response

    def delete_user(self, user_id, accept='xml'):
        """Supprime un usager à partir de son identifiant
        
        Arguments:
            user_id {str} -- identifiant du lecteur
        
        
        Returns:
            [type] -- [description]
        """
        status,response = self.request('DELETE', 'delete_user',
                                {'user_id' : user_id},
                                accept=accept)
        if status == 'Error':
            return status, response
        else:
            return status, response.status_code

    def update_user(self, user_id, data, accept='json',content_type='json'):
        """Mets à jour lesinformations utilistaeurs
        
        Arguments:
            user_id {str} -- identifiant de l'utilisateur Primary Id ou Barcode
            force_update {str} -- Par défaut certains champs sont protégés. Pour forcer leurs mis àjour il faut renseigner le paramètre override.
            Valeurs par défaut :user_group, job_category, pin_number, preferred_language, campus_code, rs_libraries, user_title, library_notices
            data {json ou xml} -- object lecteur en json ou xml selon le parmètre passer à accept
        
        Keyword Arguments:
            accept {str} -- xml ou json (default: {'xml'})
        
        Returns:
            status {str} -- Success or Error
            response {str} -- Message d'erreurs ou Lecteur MOdifié
        """ 

        status,response = self.request('PUT', 'update_user',
                                {'user_id' : user_id},
                                data=data,
                                accept=accept,
                                content_type=content_type)
        if status == 'Error':
            if response == '401861':
                status, response = self.create_user(user_id=user_id,data=data)
            return status, response
        else:
            return status,  self.extract_content(response)
    