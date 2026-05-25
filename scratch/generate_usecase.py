import urllib.request
import zlib
import base64

def encode_plantuml(text):
    zlibbed_str = zlib.compress(text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).translate(
        bytes.maketrans(b'+/', b'-_')
    ).decode('utf-8')

uml_usecase = """
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam backgroundColor white
skinparam BoxPadding 10

skinparam usecase {
  BackgroundColor #E1F5FE
  BorderColor #0288D1
  ArrowColor #0288D1
  ActorBorderColor #2C3E50
}

actor "Administrateur RH" as Admin
actor "Candidat" as Cand

rectangle "Plateforme de Smart Recruitment" {
  usecase "Déposer CV" as UC1
  usecase "Consulter Offres" as UC2
  usecase "Analyser & Classer Candidats" as UC3
  usecase "Discuter avec Chatbot\\n(Ambassadeur IA & Copilote)" as UC4
  usecase "Gérer Offres d'Emploi" as UC5
  usecase "Suivi & Rapports" as UC6
}

Cand -- UC1
Cand -- UC2
Cand -- UC4

Admin -- UC3
Admin -- UC5
Admin -- UC6
Admin -- UC4
@enduml
"""

def fetch_img(uml, filename):
    encoded = encode_plantuml(uml)
    url = f"http://www.plantuml.com/plantuml/png/~1{encoded}"
    
    # Custom Request with browser User-Agent to avoid 403 Forbidden
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    )
    
    with urllib.request.urlopen(req) as response:
        with open(filename, 'wb') as out_file:
            out_file.write(response.read())
            
    print(f"Generated {filename}")

fetch_img(uml_usecase, "cas_utilisation.png")
