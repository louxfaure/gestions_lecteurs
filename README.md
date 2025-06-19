# Django SCOOP_UTILS : Gestion des lecteurs
Module Django avec tout une série de programme permettant de faciliter la gestion des lecteurs dans une configuration réseau :
## Distribution des lecteurs dans toutes les institutions 
### Distribution des lecteurs institutionnels
#### Description fonctionnelle
La gestion des lecteurs est centralisée dans la zone réseau d'Alma. Les lecteurs institutionnels sont chargés dans cette zone réseau. Lorsqu'un lecteur se présente pour la première fois au bureau de son institution et que l'opérateur recherche son compte en scannant le code-barres de sa carte, si le compte n'est pas trouvé dans l'institution, il est copié et lié depuis la zone réseau. Cependant, ce mécanisme ne fonctionne pas via SIP2, et de nombreux lecteurs se sont trouvés dans l'incapacité d'emprunter des documents via l'automate.

Pour remédier à cela, nous avons activé un webhook Alma et développé une application web. Chaque fois qu'un lecteur institutionnel, qu'il soit étudiant ou enseignant, est créé par le chargeur de lecteurs dans la zone réseau, Alma appelle une URL dédiée en transmettant les informations du lecteur. Le compte est alors copié et lié dans toutes les institutions du réseau. Ainsi, tout compte d'un nouvellement inscrit est immédiatement présent dans toutes les instances de notre réseau.

#### Brève description technique
![](diagramme.png)
Si l'appelle vient de la Zone réseau (institution == 33PUDB_NETWORK) et que le compte est créé (event == USER_CREATED), le programme copie/lie le compte dans les institutions en convoquant l'API [Get user details](https://developers.exlibrisgroup.com/alma/apis/docs/users/R0VUIC9hbG1hd3MvdjEvdXNlcnMve3VzZXJfaWR9/). La recherche du lecteur dans l'institution suffit à copier le lecteur.
### Distribution des comptes de lecteurs extérieurs ou des comptes des bibliothèques pour le PEB
#### Description fonctionnelle
Tout lecteur inscrit dans une bibliothèque de notre réseau doit pouvoir emprunter des documents dans toutes les institutions du réseau. Malheureusement, Alma n'est capable de distribuer les informations des usagers que de la zone réseau vers les institutions. Les lecteurs extérieurs sont inscrits par les bibliothécaires dans Alma. Leur point d'entrée dans le système est donc l'instance Alma de l'institution de la bibliothèque où ils ont effectué leur inscription. Ainsi, un lecteur inscrit par l'Université de Bordeaux n'est pas visible par l'Université Bordeaux Montaigne.

Pour résoudre ce problème, nous avons activé les webhooks lecteurs dans nos cinq instances Alma. Chaque fois qu'un compte pour un lecteur extérieur est créé ou modifié dans une institution, une requête GET est envoyée à notre application web. Cette requête contient toutes les informations du lecteur. L'application utilise les API Alma pour créer ou mettre à jour le compte dans toutes les institutions.
#### Description technique
Si lappelle ne vient pas de la zobne réseau et qu'il s'agit d'une création ou modification de compte (event == USER_CREATED ou event == USER_UPDATE), le programme copie/lie le compte dans les institutions en convoquant l'API [Create user](https://developers.exlibrisgroup.com/alma/apis/docs/users/UE9TVCAvYWxtYXdzL3YxL3VzZXJz/) ou [Update user](https://developers.exlibrisgroup.com/alma/apis/docs/users/UFVUIC9hbG1hd3MvdjEvdXNlcnMve3VzZXJfaWR9/)..

## Interface de gestion des comptes lecteurs au niveau central
Interface web qui permet d'afficher tous les comptes d'un même lecteur dans toutes les institution. Elle permet de :
 - Supprimer tous les comptes
 - Modifier la date  d'expiration
 - Modifier l'identifiant principal
- 
