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
    """Détermine la clef d'API à utiliser en fonction de l'institution et du  statut de débogage.
    Si le mode Debug est activé on travaille sur les instances de test 

    Args:
        institution (string): code institution

    Returns:
        string: clef api
    """
    if settings.DEBUG :
        return settings.ALMA_TEST_API_KEY[institution]
    else :
        return settings.ALMA_API_KEY[institution]

def get_institutions_list(distribute=False,institution=None) :
    """Fourni la liste des codes institutions du réseau en fonction de l'activation ou non du mode débogage.
    Si le mode débug est actif, on travaille sur les instances de tests donc la liste des institutions est limitée.
    Si la liste est demandée pour le service de distribution des comptes utilisateurs on supprime l'instance dans laquelle les données ont été extraite.
    En plus dans le acs où les données proviennent d'une instanc"e autre que la NZ on supprime la NETWORK car il s'agit d'utilisateurs non gérés dans cette insatnce

    Args:
        distribute (bool, optional): Liste demandée par le service distribute user ? Defaults to False.
        institution (_type_, optional): _description_. Defaults to None.

    Returns:
        _array: liste des codes institutions
    """

    institutions_list = []
    if settings.DEBUG :
        institutions_list = ['NETWORK','UB','BXSA']
    else :
        institutions_list = ['NETWORK','UB','UBM','IEP','INP','BXSA']
    if distribute :
        institutions_list.remove(institution)
        if institution != 'NETWORK' :
            institutions_list.remove('NETWORK')
    return institutions_list

def copy_nz_user_in_inst(method,institutions_list,user_id,user_data):
    for institution in institutions_list :
        logger.debug(institution)
        logger.debug(method)
        user_data['user_role'][0]['scope']['value'] = "33PUDB_{}".format(institution)
        logger.debug(user_data)
        api_key = get_api_key(institution)
        alma_user = Users(apikey=api_key, service=__name__)
        actions = {
        'GET': alma_user.get_user,
        'UPDATE': alma_user.update_user,
        'POST' : alma_user.create_user
        }
        statut, reponse = actions[method].__call__(user_id,json.dumps(user_data))
        if statut == "Success" :
            logger.info("{} :: {} :: {}".format(institution,user_id,"Utilisateur copié avec succés"))
        else :
            logger.error("{} :: {} :: {}".format(institution,user_id,reponse))
    return "Utilisateur traité avec succès", 200

def distribute_user(user) :
    """Copie un utilisateur dans les différentes instances Alma

    Args:
        user (string): données utilisateurs dump json
    """
    inst_origine=user["institution"]["value"][7:]
    institutions = get_institutions_list(distribute=True,institution=inst_origine)
    event=user["event"]["value"]
    user_data = user["webhook_user"]["user"]
    user_id = user_data["primary_id"]
    if inst_origine == 'NETWORK' :
        if event != 'USER_CREATED' :
            logger.info("Type de requête non traité")
            return "Type de requête non traité", 418
        else :
            return copy_nz_user_in_inst('GET',institutions,user_id,user_data)
    else :
        if user_data['user_role'] :
            if "desc" in  user_data['user_role'][0]['scope'] :
                user_data['user_role'][0]['scope'].pop('desc')
            if "expiry_date" in user_data['user_role'][0] :
                user_data['user_role'][0].pop('expiry_date')
        if event == 'USER_CREATED' and user_data["job_category"]["value"] in ['Exterieur','PEB'] :
            return copy_nz_user_in_inst('POST',institutions,user_id,user_data)
        elif event == 'USER_UPDATED' and user_data["job_category"]["value"] in ['Exterieur','PEB'] :
            return copy_nz_user_in_inst('UPDATE',institutions,user_id,user_data)
        else :
            logger.info("Type de requête non traité")
            return "Type de requête non traité", 418


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
            elif status == "Error" and user in ["401861","401890"] :
                continue
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
