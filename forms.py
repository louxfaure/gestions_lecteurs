from django import forms
# from bootstrap_datepicker_plus import DatePickerInput

class LecteurForm(forms.Form):
    identifiant  = forms.CharField(
        label='Identifiant du lecteur',
        widget=forms.TextInput(attrs={
            "placeholder" : "Identifiant du lecteur",
            "aria-label" : "Identifiant du lecteur",
            "class": "form-control col-md-7",
            "name": "champ_recherche"}),
        required=True
        )
    type_identifiant = forms.ChoiceField(
        choices=     [('PRIMARYIDENTIFIER','Identifiant principal'),
                            ('BARCODE', 'Code-barres')],
        widget=forms.Select(attrs={            
            "aria-label" : "Identifiant du lecteur",
            "class": "custom-select form-control-lg col-md-3"}),
        required=True
        ) 

class ChangeLecteurForm(forms.Form):
    nouvel_identifiant = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "name": "nouvel_identifiant"}),
        label='Identifiant principal',
        required=False
        )
    date_expiration =  forms.DateField(
        widget=forms.widgets.DateInput(format="%m/%d/%Y"),
        required=False,
        label='Date d''expiration au format jj/mm/dddd'
        # input_formats='%d/%m/%Y',
        # required=False
        )

class CategorieUsager(forms.Form):
    CHOICES = (('PEB_attente','Bibliothèque PEB'),
            ('Exterieur_attente','Lecteur extérieur'),
            )
    categorie_usagers = forms.ChoiceField(
        choices= CHOICES,
        widget=forms.Select(attrs={            
            "aria-label" : "Catégorie usagers",
            "class": "custom-select form-control-lg col-md-3"}),
        required=True
        ) 
    etab = forms.CharField(
        widget=forms.HiddenInput(attrs={
            "class": "form-control",
            "name": "nouvel_identifiant"}),
        )