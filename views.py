from django.http import HttpResponse, JsonResponse
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .services import main
import json
import logging


#Initialisation des logs
logger = logging.getLogger(__name__)


@csrf_exempt #Désactive la protection contre le « Cross site request forgery » pour autoriser les requêtes post depuis un autre domaine
def webhook(request):
    if request.method != 'POST':
        # Si la requête n'est pas du Post c'est peut être le profil de configuration qui teste la connexion 
        try: 
            challenge = { 'challenge' : request.GET["challenge"] } 
        except MultiValueDictKeyError:
            return HttpResponse("Bien reçu. Pas de Challenge.")
        return JsonResponse(challenge)
    # Test l'authentification du web hook
    if not main.test_hmac(request) :
        return HttpResponse("Le HMAC n'apas été validé",status=500)
    user = json.loads(request.body)
    # logger.debug(json.dumps(user, indent=4, sort_keys=True))
    event=user["event"]["value"]
    logger.debug(event)
    if event != 'USER_CREATED' :
        logger.info("Type de requête non traité")
        return HttpResponse("Type de requête non traité", status=418)  
    user_data = user["webhook_user"]["user"]
    user_id = user_data["primary_id"]
    main.distribute_user(user_id,json.dumps(user_data))
    return HttpResponse("User bien reçu", status=200)        
        

