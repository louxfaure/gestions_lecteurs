import os
import logging
import json

import base64
import hashlib
import hmac

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

def distribute_user(user_id,user_data) :
    institutions = ['UB','UBM']
    for institution in institutions :
        if settings.DEBUG :
            api_key = settings.ALMA_TEST_API_KEY[institution]
        else :
            api_key = settings.ALMA_API_KEY[institution]
        alma_user = Users(apikey=api_key, service=__name__)
        statut, reponse = alma_user.distribute_user(user_id,user_data)
        if statut == "Success" :
            logger.info("{} :: {} :: {}".format(institution,user_id,"Utilisateur copié avec succés"))
        else :
            logger.error("{} :: {} :: {}".format(institution,user_id,reponse))