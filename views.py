from django.http import HttpResponse, JsonResponse,  Http404, HttpResponseRedirect
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import LecteurForm, ChangeLecteurForm, CategorieUsager
from .services import main, Alma_Users
import json
import logging

#Initialisation des logs
logger = logging.getLogger(__name__)

@login_required
def recherche_lecteur(request):
    form = LecteurForm(request.POST or None)
    if form.is_valid():
        type_id = form.cleaned_data['type_identifiant']
        id_lecteur = form.cleaned_data['identifiant']
        return HttpResponseRedirect(reverse('lecteur', kwargs={'identifiant': id_lecteur.strip(),'type_identifiant':type_id}))
    return render(request, "gestions_lecteurs/recherche_lecteur.html", locals())

def lecteur(request,identifiant,type_identifiant):
    user = main.UserInNZ(identifiant,type_identifiant)
    datas = ("full_name","primary_id","barcode","job_category","user_group","record_type","account_type","expiry_date","loans","requests")
    user_data_in_table = user.get_user_data_in_table(datas)
    request.session[identifiant] = user.user_data
    form = CategorieUsager(request.POST or None)
    return render(request, "gestions_lecteurs/lecteur.html", locals())


@csrf_exempt #Désactive la protection contre le « Cross site request forgery » pour autoriser les requêtes post depuis un autre domaine
def webhook(request):
    # Reçoit les messages en provenance du webhook alma
    if request.method != 'POST':
        # Si la requête n'est pas du Post c'est peut être le profil de configuration qui teste la connexion 
        try: 
            challenge = { 'challenge' : request.GET["challenge"] } 
        except MultiValueDictKeyError:
            return HttpResponse("Bien reçu. Pas de Challenge.")
        return JsonResponse(challenge)
    # Test l'authentification du web hook
    if not main.test_hmac(request) :
        return HttpResponse("Le HMAC n'a pas été validé",status=500)
    user = json.loads(request.body)
    response, http_code = main.distribute_user(user)
    return HttpResponse(response, status=http_code)


          
        
def lecteur_analytique(request):
    identifiant = request.GET.get('id')
    type_identifiant = request.GET.get('typeid')
    user = services.User(identifiant,type_identifiant)
    datas = ("full_name","primary_id","barcode","job_category","user_group","record_type","account_type","expiry_date","loans","requests")
    user_data_in_table = user.get_user_data_in_table(datas)
    request.session[identifiant] = user.user_data
    return render(request, "gestions_lecteurs/lecteur.html", locals())

def suppr_lecteur(request,identifiant,list_etab):
    results = {}
    for etab in list_etab.split(','):
        results[etab] = {}
        api_key = main.get_api_key(institution=etab)
        api = Alma_Users.Users(apikey=api_key, service='Outils_scoop_lecteurs')
        results[etab]['status'],results[etab]['response'] = api.delete_user(identifiant)
    return render(request, "gestions_lecteurs/suppr-lecteur.html", locals())

def modif_lecteur(request,identifiant):
    form =  ChangeLecteurForm(request.POST or None)
    if form.is_valid():
        user_data = request.session.get(identifiant)
        new_id_lecteur = form.cleaned_data['nouvel_identifiant']
        expiry_date = form.cleaned_data['date_expiration']
        for institution  in user_data:
            if new_id_lecteur:
                user_data[institution]['primary_id'] = new_id_lecteur
            if expiry_date:
                date =  "{}Z".format(expiry_date.strftime("%Y-%m-%d"))
                user_data[institution]['expiry_date'] = date
                user_data[institution]['purge_date'] = date
        request.session[identifiant]=user_data
        return HttpResponseRedirect(reverse('result-modif-lecteur',kwargs={'identifiant': identifiant}))
    return render(request, "gestions_lecteurs/modif-lecteur.html", locals())

def distribution_compte_interne(request,identifiant,type_identifiant):
    user_data = request.session.get(identifiant)
    if request.method == 'POST':
        form = CategorieUsager(request.POST)
        if form.is_valid():
            cat_usager = form.cleaned_data['categorie_usagers']
            institution = form.cleaned_data['etab']
            user_data[institution]['job_category']['value'] = cat_usager
            api_key = main.get_api_key(institution=institution)
            api = Alma_Users.Users(apikey=api_key, service='Outils_scoop_lecteurs')
            status, response = api.update_user(identifiant,
                                                "user_group,job_category,pin_number,preferred_language,campus_code,rs_libraries,user_title,library_notices",
                                                json.dumps(user_data[institution]),
                                                accept='json',
                                                content_type='json')
            alert_type = "alert-success" if status == "Success" else "alert-danger"
            return render(request, "gestions_lecteurs/distribution-compte-interne.html", locals())
        else:
            return HttpResponseRedirect(reverse('lecteur', kwargs={'identifiant': identifiant,'type_identifiant':type_identifiant}))
    else:
            return HttpResponseRedirect(reverse('lecteur', kwargs={'identifiant': identifiant,'type_identifiant':type_identifiant}))

def result_modif_lecteur(request,identifiant):
    results = {}
    user_data = request.session.get(identifiant)
    for institution  in user_data:
        api_key = main.get_api_key(institution=institution)
        api = Alma_Users.Users(apikey=api_key, service='Outils_scoop_lecteurs')
        results[institution] = {}
        results[institution]["status"], results[institution]["response"] = api.update_user(identifiant,
                                                                                        "user_group,job_category,pin_number,preferred_language,campus_code,rs_libraries,user_title,library_notices",
                                                                                            json.dumps(user_data[institution]),
                                                                                            accept='json',
                                                                                            content_type='json') 
    return render(request, "gestions_lecteurs/result-modif-lecteur.html", locals())
