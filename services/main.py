import os
import logging
import json

import base64
import hashlib
import hmac

from collections import OrderedDict
from django.conf import settings
from .Alma_Users import Users


#Initialisation des logs
logger = logging.getLogger(__name__)

def test_hmac(request):
    """Test le code d'authentification hmac fourni par le WEbHOOK
    Args:
        request (object): requete

    Returns:
        boolean: [description]
    """
    secret_key = settings.WEBHOOK_SECRET_KEY
    signature = request.META.get('HTTP_X_EXL_SIGNATURE')
    if not signature:
        logger.error("Le webhook n'a pas fourni de signature")
        return False
    body = request.body
    key = secret_key.encode('utf-8')
    received_hmac_b64 = signature.encode('utf-8')
    generated_hmac = hmac.new(key=key, msg=body, digestmod=hashlib.sha256).digest()
    generated_hmac_b64 = base64.b64encode(generated_hmac)
    match = hmac.compare_digest(received_hmac_b64, generated_hmac_b64)
    if not match: 
        logger.error("Le HMAC n'est pas valide !")
    else :
        return True
def get_api_key(institution) :
        if settings.DEBUG :
            return settings.ALMA_TEST_API_KEY[institution]
        else :
            return settings.ALMA_API_KEY[institution]

def get_institutions_list() :
        if settings.DEBUG :
            return ['NETWORK','UB','UBM','BXSA']
        else :
            return ['NETWORK','UB','UBM','IEP','INP','BXSA']

def distribute_user(user_id,user_data) :
    institutions = ['UB','UBM']
    for institution in institutions :    
        api_key = get_api_key(institution)
        alma_user = Users(apikey=api_key, service=__name__)
        statut, reponse = alma_user.distribute_user(user_id,user_data)
        if statut == "Success" :
            logger.info("{} :: {} :: {}".format(institution,user_id,"Utilisateur copié avec succés"))
        else :
            logger.error("{} :: {} :: {}".format(institution,user_id,reponse))


class UserInNZ(object):
    """Retourne la liste des institutions où le compte du lecteur est présent. Pour chaque institution retourne le nombre de prêt
    
    Arguments:
        user_id {str} -- identifiant du lecteur
    """
    def __init__(self,user_id, user_id_type):
        self.error = False
        self.error_API = ""
        self.error_institution = ""
        self.error_message =""
        self.user_data = OrderedDict()
        self.nb_prets = 0
        self.nb_demandes = 0
        self.institutions_list = get_institutions_list()
        for institution in self.institutions_list :
            api_key = get_api_key(institution)
            api = Users(apikey=api_key, service=__name__)
            status, user = api.get_user(user_id,user_id_type=user_id_type,user_view='brief',accept='json')
            # print("{} --> {} : {}".format(institution,status,response))
            if status == "Success":
                self.user_data[institution]=user
                self.nb_prets += user["loans"]["value"]
                self.nb_demandes += user["requests"]["value"]
            elif status == "Error":
                self.error = True
                self.error_API = "Get User"
                self.error_institution = institution
                self.error_message = user
                break

    @property
    def get_error_status(self):
        return self.error

    def get_error_message(self):
        return self.error_message

    def ckeck_if_unknowed_user(self):
        if len(self.user_data) == 0:
            return True
        else:
            return False 
    
    def is_not_deletable(self):
        if (self.nb_demandes + self.nb_prets) == 0:
            return "false"
        else:
            return "true"

    def get_user_institutions_string(self):
        return ",".join(self.user_data.keys())

    def get_user_data_in_table(self,datas):
        """Formatte un dictionaire pour afficher les données lecteurs en tableau
        
        Arguments:
            datas {array} -- donées lecteurs que l('on veut voir afficher)
        
        Returns:
            [dict] -- dict[data][inst] = valeur de data
        """
        user_data_in_table=OrderedDict()
        for data in datas:
            user_data_in_table[data] = []
            for inst in self.user_data:
                barcode = "Null"
                if data == 'barcode':
                    for identifier in self.user_data[inst]['user_identifier']:
                        if identifier['id_type']['value'] == 'BARCODE':
                            barcode = identifier['value']
                    user_data_in_table[data].append(barcode)
                else:
                    if data in self.user_data[inst]:
                        if isinstance(self.user_data[inst][data], dict):
                            user_data_in_table[data].append(self.user_data[inst][data]["value"])
                        else: 
                            user_data_in_table[data].append(self.user_data[inst][data])
                    else :
                        user_data_in_table[data].append("Null")
        return user_data_in_table
