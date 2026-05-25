import urllib.request
import zlib
import base64
import string

def encode_plantuml(text):
    zlibbed_str = zlib.compress(text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).translate(
        bytes.maketrans(b'+/', b'-_')
    ).decode('utf-8')

# 1. Candidat
uml_candidat = """
@startuml
skinparam backgroundColor white
skinparam BoxPadding 10
autonumber
title Diagramme de Séquence : Parcours Candidat

actor "Candidat" as C
participant "Interface UI" as UI
participant "Passerelle API" as API
participant "Agent IA" as IA
database "Base de données" as DB

C -> UI : Déposer CV (Fichier)
UI -> API : POST /upload_cv
API -> IA : process_cv()
activate IA
IA -> IA : Extraction & Scanning
IA -> DB : Sauvegarde du profil
DB --> IA : Confirmation
IA --> API : Retourne Score de qualité
deactivate IA
API --> UI : Données et succès
UI --> C : Affiche le score
@enduml
"""

# 2. Admin
uml_admin = """
@startuml
skinparam backgroundColor white
autonumber
title Diagramme de Séquence : Administrateur RH

actor "Administrateur RH" as Admin
participant "Dashboard UI" as UI
participant "Passerelle API" as API
participant "IA Matching (LLM)" as IA
database "Base de données" as DB

Admin -> UI : Sélectionner Candidat et Offre
UI -> API : Demande d'évaluation
API -> IA : evaluate_candidate()
activate IA
IA -> DB : Récupérer Profil + Critères
DB --> IA : Données utiles
IA -> IA : Analyse LLM-as-a-judge
IA -> DB : Sauvegarde du Match Score
IA --> API : Retourne justification
deactivate IA
API --> UI : Rapport de Matching généré
UI --> Admin : Affiche la recommandation
@enduml
"""

# 3. Employé
uml_employe = """
@startuml
skinparam backgroundColor white
autonumber
title Diagramme de Séquence : Employé (Demande de Congés)

actor "Employé" as E
participant "Portail UI" as UI
participant "Passerelle API" as API
participant "Agent Congés" as IA
database "Base SQL" as DB

E -> UI : Soumet demande de congé
UI -> API : POST /leave_request
API -> IA : handle_request()
activate IA
IA -> DB : Vérif. solde de congés
DB --> IA : Solde suffisant
IA -> DB : Enregistrement de la demande
DB --> IA : Succès
IA --> API : Statut "En attente"
deactivate IA
API --> UI : Confirmation
UI --> E : Affiche message de succès
@enduml
"""

def fetch_img(uml, filename):
    encoded = encode_plantuml(uml)
    url = f"http://www.plantuml.com/plantuml/png/~1{encoded}"
    urllib.request.urlretrieve(url, filename)
    print(f"Generated {filename}")

fetch_img(uml_candidat, "seq_candidat.png")
fetch_img(uml_admin, "seq_admin.png")
fetch_img(uml_employe, "seq_employe.png")
