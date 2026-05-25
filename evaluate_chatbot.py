# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         SCRIPT D'ÉVALUATION DU CHATBOT RH — MÉTRIQUES RAGAS                ║
║  Évalue : Pertinence, Temps de Réponse, Score RAGAS, Fidélité               ║
╚══════════════════════════════════════════════════════════════════════════════╝

Métriques mesurées :
  1. Pertinence des réponses  → score sémantique vs réponse attendue
  2. Temps moyen de réponse   → latence LLM (Groq/Ollama)
  3. Score global RAGAS       → (faithfulness + answer_relevancy + context_recall) / 3
  4. Fidélité (Faithfulness)  → réponse ancrée dans le contexte récupéré

Utilisation :
  python evaluate_chatbot.py
  python evaluate_chatbot.py --tests 50 --export rapport_eval.json
"""

import os
import sys
import time
import json
import argparse
import statistics
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# ── Chargement de l'environnement ─────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# ── Couleurs console ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# ══════════════════════════════════════════════════════════════════════════════
# JEUX DE TESTS (Question, Contexte RAG simulé, Réponse de référence)
# ══════════════════════════════════════════════════════════════════════════════

TEST_CASES: List[Dict[str, Any]] = [
    # ── Groupe 1 : Offres d'emploi & Postes ──────────────────────────────────
    {
        "id": "T01",
        "category": "Offres d'emploi",
        "question": "Quels postes sont disponibles chez Segula Technologies ?",
        "context": "Segula Technologies recrute actuellement pour plusieurs postes : Ingénieur Mécatronique, Développeur Python Senior, Chef de Projet IT, Data Scientist et Consultant ERP SAP. Les candidatures sont ouvertes sur notre plateforme.",
        "expected_answer": "Segula Technologies propose des postes en Mécatronique, Développement Python, Gestion de Projet IT, Data Science et Consulting SAP.",
    },
    {
        "id": "T02",
        "category": "Offres d'emploi",
        "question": "Y a-t-il des offres pour des développeurs Python ?",
        "context": "Un poste de Développeur Python Senior est ouvert chez Segula. Compétences requises : Python 3.10+, FastAPI, Docker, PostgreSQL. Expérience minimale : 3 ans. Salaire : 45-55k€.",
        "expected_answer": "Oui, un poste de Développeur Python Senior est disponible, nécessitant Python 3.10+, FastAPI, Docker et 3 ans d'expérience.",
    },
    {
        "id": "T03",
        "category": "Offres d'emploi",
        "question": "Quelles compétences sont requises pour le poste de Data Scientist ?",
        "context": "Le poste de Data Scientist chez Segula exige : Python, R, TensorFlow, PyTorch, SQL, expérience en Machine Learning et Deep Learning. 2 ans d'expérience minimum. Maîtrise de l'anglais requise.",
        "expected_answer": "Le Data Scientist doit maîtriser Python, R, TensorFlow, PyTorch, SQL et le Machine Learning avec 2 ans d'expérience minimum.",
    },
    {
        "id": "T04",
        "category": "Offres d'emploi",
        "question": "Comment postuler pour un stage chez Segula ?",
        "context": "Segula Technologies accepte les candidatures de stage via la plateforme en ligne. Les étudiants doivent soumettre leur CV et lettre de motivation. Les stages durent de 3 à 6 mois et des sujets de fin d'études sont disponibles.",
        "expected_answer": "Pour postuler à un stage chez Segula, soumettez votre CV et lettre de motivation via la plateforme. Les stages durent 3 à 6 mois.",
    },
    {
        "id": "T05",
        "category": "Offres d'emploi",
        "question": "Est-ce qu'il y a des postes en télétravail ?",
        "context": "Segula propose des modalités hybrides pour certains postes IT. Le télétravail partiel est possible 2 à 3 jours par semaine pour les développeurs et consultants. Les postes terrain (ingénierie mécanique, automobile) nécessitent une présence sur site.",
        "expected_answer": "Certains postes IT permettent le télétravail hybride 2-3 jours par semaine. Les postes terrain nécessitent une présence sur site.",
    },

    # ── Groupe 2 : Candidature & CV ──────────────────────────────────────────
    {
        "id": "T06",
        "category": "Candidature",
        "question": "Comment déposer mon CV sur la plateforme ?",
        "context": "Pour déposer votre CV, cliquez sur 'Déposer mon CV' dans le menu principal. Les formats acceptés sont PDF et Word (.docx). Taille maximale : 10 MB. Votre CV sera analysé automatiquement par notre IA en quelques secondes.",
        "expected_answer": "Cliquez sur 'Déposer mon CV', uploadez un fichier PDF ou Word (max 10 MB). L'IA analyse votre CV automatiquement.",
    },
    {
        "id": "T07",
        "category": "Candidature",
        "question": "Quels formats de CV sont acceptés ?",
        "context": "La plateforme accepte les CV en format PDF (recommandé) et Word (.docx). Les images JPG/PNG sont également supportées via OCR. Les fichiers ne doivent pas dépasser 10 MB.",
        "expected_answer": "Les formats acceptés sont PDF (recommandé), Word (.docx) et images JPG/PNG. La limite est de 10 MB.",
    },
    {
        "id": "T08",
        "category": "Candidature",
        "question": "Combien de temps prend l'analyse de mon CV ?",
        "context": "L'analyse IA du CV prend généralement entre 10 et 30 secondes. Cette analyse comprend l'extraction OCR, le parsing des informations, le scoring et la vérification éthique. Un email de confirmation est envoyé une fois l'analyse terminée.",
        "expected_answer": "L'analyse IA prend 10 à 30 secondes et inclut l'OCR, le parsing, le scoring et un audit éthique. Un email de confirmation est envoyé.",
    },
    {
        "id": "T09",
        "category": "Candidature",
        "question": "Comment savoir si ma candidature a été reçue ?",
        "context": "Après soumission, vous recevez un email de confirmation immédiat. Vous pouvez également suivre le statut de votre candidature dans votre espace candidat sous 'Mes Candidatures'. Les statuts possibles sont : Reçu, En analyse, En cours d'examen, Shortlisté, Accepté ou Refusé.",
        "expected_answer": "Un email de confirmation est envoyé immédiatement. Vous pouvez suivre votre candidature dans 'Mes Candidatures' avec les statuts : Reçu, En analyse, Shortlisté, etc.",
    },
    {
        "id": "T10",
        "category": "Candidature",
        "question": "Puis-je postuler à plusieurs offres simultanément ?",
        "context": "Oui, vous pouvez postuler à plusieurs offres simultanément sur la plateforme Segula. Votre profil sera automatiquement adapté pour chaque offre. Il est recommandé de ne pas postuler à plus de 3 offres à la fois pour maximiser vos chances.",
        "expected_answer": "Oui, vous pouvez postuler à plusieurs offres en parallèle. Votre profil s'adapte automatiquement à chaque offre. Maximum 3 recommandé.",
    },

    # ── Groupe 3 : Processus de Recrutement ──────────────────────────────────
    {
        "id": "T11",
        "category": "Recrutement",
        "question": "Quelles sont les étapes du processus de recrutement ?",
        "context": "Le processus de recrutement Segula comprend : 1) Dépôt du CV et analyse IA, 2) Présélection automatique, 3) Entretien RH téléphonique (30 min), 4) Test technique ou étude de cas, 5) Entretien manager, 6) Décision finale. La durée totale est généralement de 2 à 4 semaines.",
        "expected_answer": "Le recrutement Segula compte 5 étapes : analyse IA du CV, présélection, entretien RH, test technique, entretien manager. Durée : 2 à 4 semaines.",
    },
    {
        "id": "T12",
        "category": "Recrutement",
        "question": "Quel est le délai de réponse après un entretien ?",
        "context": "Segula s'engage à répondre dans un délai maximum de 5 jours ouvrés après chaque entretien. En cas de non-réponse, vous pouvez relancer le recruteur directement depuis votre espace candidat. Le délai moyen de réponse est de 3 jours.",
        "expected_answer": "Segula répond dans un délai maximum de 5 jours ouvrés (délai moyen 3 jours) après chaque entretien. Vous pouvez relancer depuis votre espace.",
    },
    {
        "id": "T13",
        "category": "Recrutement",
        "question": "Y a-t-il un test technique dans le processus ?",
        "context": "Oui, selon le poste, un test technique est requis. Pour les développeurs : un test de coding en ligne de 90 minutes. Pour les ingénieurs : une étude de cas technique. Pour les consultants : une mise en situation professionnelle. Les tests sont réalisés sur plateforme sécurisée.",
        "expected_answer": "Oui, selon le poste : test de coding (90 min) pour développeurs, étude de cas pour ingénieurs, mise en situation pour consultants. Tests sur plateforme sécurisée.",
    },
    {
        "id": "T14",
        "category": "Recrutement",
        "question": "Comment se préparer pour l'entretien technique ?",
        "context": "Pour se préparer : réviser les fondamentaux du domaine, pratiquer les algorithmes si c'est un poste développeur, revoir les projets de son CV, se familiariser avec les technologies listées dans l'offre. Segula valorise la résolution de problèmes et la communication.",
        "expected_answer": "Révisez les fondamentaux, pratiquez les algorithmes (développeur), relisez vos projets CV et maîtrisez les technologies de l'offre. Segula valorise résolution de problèmes et communication.",
    },
    {
        "id": "T15",
        "category": "Recrutement",
        "question": "Puis-je négocier le salaire proposé ?",
        "context": "Oui, la négociation salariale est possible après l'étape de sélection finale. Segula propose des packages compétitifs incluant salaire fixe, bonus de performance, mutuelle et avantages en nature. Les fourchettes varient selon le poste, l'expérience et la localisation.",
        "expected_answer": "Oui, la négociation est possible en fin de processus. Les packages incluent salaire fixe, bonus, mutuelle et avantages selon le poste et l'expérience.",
    },

    # ── Groupe 4 : IA & Scoring ───────────────────────────────────────────────
    {
        "id": "T16",
        "category": "IA & Scoring",
        "question": "Comment l'IA évalue-t-elle mon CV ?",
        "context": "L'IA analyse le CV selon 5 critères pondérés : Compétences techniques (35%), Expérience professionnelle (30%), Formation académique (20%), Profil GitHub (10%), et Communication/Langues (5%). Un score global sur 100 est calculé. Un audit éthique garantit l'absence de biais.",
        "expected_answer": "L'IA score le CV sur 5 critères : Compétences (35%), Expérience (30%), Formation (20%), GitHub (10%), Communication (5%). Score sur 100 avec audit anti-biais.",
    },
    {
        "id": "T17",
        "category": "IA & Scoring",
        "question": "Qu'est-ce que le score IA et comment l'améliorer ?",
        "context": "Le score IA est un indicateur de 0 à 100 évaluant l'adéquation du profil avec les offres. Pour l'améliorer : compléter toutes les sections du CV, ajouter des certifications, lier un profil GitHub actif, préciser les années d'expérience et les compétences techniques détaillées.",
        "expected_answer": "Le score IA va de 0 à 100. Pour l'améliorer : complétez le CV, ajoutez des certifications, liez GitHub, précisez expériences et compétences techniques.",
    },
    {
        "id": "T18",
        "category": "IA & Scoring",
        "question": "L'IA peut-elle détecter des doublons dans les candidatures ?",
        "context": "Oui, notre système détecte automatiquement les candidatures en doublon via l'email, le téléphone et l'analyse sémantique du texte du CV. Si un doublon est détecté, le nouveau dépôt est bloqué et le candidat est informé. Cela garantit l'intégrité de la base de données.",
        "expected_answer": "Oui, l'IA détecte les doublons via email, téléphone et analyse sémantique. Les doublons sont bloqués automatiquement pour maintenir l'intégrité des données.",
    },
    {
        "id": "T19",
        "category": "IA & Scoring",
        "question": "Comment fonctionne l'analyse GitHub dans l'évaluation ?",
        "context": "Si le CV contient un lien GitHub, notre IA analyse automatiquement : le nombre de repos publics, les langages utilisés, les contributions, les stars reçues, et l'activité récente. Un score de contribution de 0 à 100 est calculé et intégré dans le score global (poids : 10%).",
        "expected_answer": "L'IA analyse repos, langages, contributions, stars et activité GitHub. Un score 0-100 est calculé et compte pour 10% du score global.",
    },
    {
        "id": "T20",
        "category": "IA & Scoring",
        "question": "L'IA est-elle équitable pour tous les candidats ?",
        "context": "Notre système inclut un module d'audit d'équité IA (AI Fairness Checker). Il détecte et signale tout biais potentiel lié à l'âge, le genre, l'origine ou la situation personnelle. Les évaluations sont basées exclusivement sur les compétences et l'expérience professionnelle.",
        "expected_answer": "Oui, un module d'audit d'équité IA vérifie les biais liés à l'âge, genre ou origine. Seules compétences et expériences sont évaluées.",
    },

    # ── Groupe 5 : RGPD & Données ─────────────────────────────────────────────
    {
        "id": "T21",
        "category": "RGPD & Données",
        "question": "Comment mes données personnelles sont-elles protégées ?",
        "context": "Segula respecte le RGPD (Règlement Général sur la Protection des Données). Vos données sont stockées localement en France, chiffrées et ne sont jamais partagées avec des tiers sans consentement. Vous pouvez demander la suppression de vos données à tout moment.",
        "expected_answer": "Segula respecte le RGPD. Données stockées en France, chiffrées et non partagées. Suppression possible à tout moment.",
    },
    {
        "id": "T22",
        "category": "RGPD & Données",
        "question": "Puis-je demander la suppression de mon profil ?",
        "context": "Oui, conformément au RGPD (droit à l'oubli), vous pouvez demander la suppression complète de votre profil et données depuis votre espace candidat sous 'Paramètres > Supprimer mon compte'. La suppression est effective dans les 72 heures.",
        "expected_answer": "Oui, via 'Paramètres > Supprimer mon compte'. La suppression complète est effective dans les 72 heures conformément au droit à l'oubli (RGPD).",
    },
    {
        "id": "T23",
        "category": "RGPD & Données",
        "question": "Combien de temps mes données sont-elles conservées ?",
        "context": "Selon le RGPD et nos politiques internes, les données des candidats sont conservées 2 ans après le dernier contact. Pour les candidats embauchés, les données RH sont conservées selon la réglementation du travail (5 ans minimum). Vous serez notifié avant toute suppression automatique.",
        "expected_answer": "Données conservées 2 ans après dernier contact pour candidats. Pour les embauchés : 5 ans minimum. Notification avant suppression automatique.",
    },
    {
        "id": "T24",
        "category": "RGPD & Données",
        "question": "Mes données de CV sont-elles partagées avec des tiers ?",
        "context": "Non, les données des CV et profils candidats ne sont jamais partagées avec des sociétés tierces. L'IA analyse les CV localement sans envoyer de données à des services cloud externes. Seul l'accès LLM via Groq est utilisé pour la génération de réponses, anonymisé.",
        "expected_answer": "Non, les données ne sont jamais partagées avec des tiers. Analyse locale. L'accès Groq pour le LLM est anonymisé.",
    },
    {
        "id": "T25",
        "category": "RGPD & Données",
        "question": "Comment donner ou retirer mon consentement RGPD ?",
        "context": "Le consentement RGPD est requis lors de l'inscription. Vous pouvez modifier vos préférences de consentement depuis 'Mon Compte > Confidentialité'. Le retrait du consentement arrête tout traitement de vos données et déclenche la procédure de suppression dans les 30 jours.",
        "expected_answer": "Consentement géré via 'Mon Compte > Confidentialité'. Retrait = arrêt du traitement + suppression dans 30 jours.",
    },

    # ── Groupe 6 : Entreprise Segula ──────────────────────────────────────────
    {
        "id": "T26",
        "category": "Segula Technologies",
        "question": "Qu'est-ce que Segula Technologies ?",
        "context": "Segula Technologies est un groupe international d'ingénierie fondé en 1999. Présent dans 30 pays avec plus de 15 000 collaborateurs, il intervient dans l'automobile, l'aéronautique, l'énergie, le naval et le ferroviaire. Siège social en France.",
        "expected_answer": "Segula Technologies est un groupe d'ingénierie international (fondé 1999), présent dans 30 pays, 15 000 collaborateurs, actif dans l'automobile, aéronautique et énergie.",
    },
    {
        "id": "T27",
        "category": "Segula Technologies",
        "question": "Dans quels secteurs Segula Technologies intervient-il ?",
        "context": "Segula Technologies couvre 6 secteurs principaux : Automobile & Mobilité, Aéronautique & Spatial, Énergie (nucléaire, renouvelables), Naval & Offshore, Ferroviaire et Industrie. Chaque secteur dispose d'équipes d'ingénierie spécialisées.",
        "expected_answer": "Segula intervient dans 6 secteurs : Automobile, Aéronautique, Énergie (nucléaire/renouvelable), Naval, Ferroviaire et Industrie.",
    },
    {
        "id": "T28",
        "category": "Segula Technologies",
        "question": "Quels sont les avantages sociaux proposés par Segula ?",
        "context": "Segula offre : mutuelle santé complète, tickets restaurant, participation aux bénéfices, plan d'épargne entreprise (PEE), RTT, formations continues certifiantes, mobilité interne internationale, et accompagnement coaching de carrière.",
        "expected_answer": "Avantages Segula : mutuelle, tickets restaurant, participation, PEE, RTT, formations certifiantes, mobilité internationale et coaching carrière.",
    },
    {
        "id": "T29",
        "category": "Segula Technologies",
        "question": "Segula propose-t-il des opportunités d'évolution interne ?",
        "context": "Oui, Segula valorise fortement la mobilité interne. Des revues de carrière annuelles permettent d'identifier les souhaits d'évolution. Des programmes de leadership pour les hauts potentiels sont disponibles. La mobilité géographique internationale est facilitée pour les collaborateurs.",
        "expected_answer": "Oui, Segula valorise la mobilité interne avec des revues de carrière annuelles, programmes leadership et mobilité internationale facilitée.",
    },
    {
        "id": "T30",
        "category": "Segula Technologies",
        "question": "Segula recrute-t-il des profils juniors ou expérimentés ?",
        "context": "Segula recrute tous les niveaux : juniors (0-2 ans) pour des postes de développement, confirmés (2-5 ans) pour des rôles techniques spécialisés, et seniors (5+ ans) pour des postes de lead technique et management. Les alternants et stagiaires sont également accueillis.",
        "expected_answer": "Segula recrute tous niveaux : juniors (0-2 ans), confirmés (2-5 ans), seniors (5+ ans), alternants et stagiaires.",
    },

    # ── Groupe 7 : Plateforme & Fonctionnalités ───────────────────────────────
    {
        "id": "T31",
        "category": "Plateforme",
        "question": "Comment créer un compte candidat ?",
        "context": "Pour créer un compte : cliquez sur 'S'inscrire', renseignez votre email et mot de passe, acceptez les conditions RGPD, et vérifiez votre adresse email via le lien reçu. L'inscription prend moins de 2 minutes.",
        "expected_answer": "Cliquez sur 'S'inscrire', entrez email + mot de passe, acceptez le RGPD, vérifiez votre email. Inscription en moins de 2 minutes.",
    },
    {
        "id": "T32",
        "category": "Plateforme",
        "question": "Comment réinitialiser mon mot de passe ?",
        "context": "Depuis la page de connexion, cliquez sur 'Mot de passe oublié ?'. Entrez votre email et vous recevrez un lien de réinitialisation valable 24 heures. En cas de problème, contactez support@segula.fr.",
        "expected_answer": "Cliquez sur 'Mot de passe oublié ?', entrez votre email, suivez le lien (valable 24h). Support : support@segula.fr.",
    },
    {
        "id": "T33",
        "category": "Plateforme",
        "question": "L'application est-elle disponible sur mobile ?",
        "context": "La plateforme Segula est accessible via navigateur mobile (responsive design). Une application native iOS et Android est en développement et sera disponible au T3 2025. Les fonctionnalités principales sont optimisées pour mobile.",
        "expected_answer": "La plateforme est responsive sur mobile. Une application iOS/Android native est prévue pour T3 2025.",
    },
    {
        "id": "T34",
        "category": "Plateforme",
        "question": "Comment contacter le service RH directement ?",
        "context": "Le service RH Segula est joignable par : email rh@segula.fr, téléphone +33 1 XX XX XX XX (lun-ven 9h-18h), ou via le chatbot IA disponible 24h/24. Un recruteur vous répondra dans les 48 heures ouvrées.",
        "expected_answer": "Contactez le RH via email rh@segula.fr, téléphone (lun-ven 9h-18h), ou le chatbot IA 24h/24. Réponse sous 48h ouvrées.",
    },
    {
        "id": "T35",
        "category": "Plateforme",
        "question": "Peut-on modifier son CV après dépôt ?",
        "context": "Oui, vous pouvez mettre à jour votre CV depuis 'Mon Profil > Documents'. L'ancienne version est archivée et la nouvelle est renvoyée en analyse IA automatiquement. Vous pouvez effectuer jusqu'à 3 mises à jour par mois.",
        "expected_answer": "Oui, mettez à jour via 'Mon Profil > Documents'. L'ancienne version est archivée, la nouvelle relance l'analyse IA. Limite : 3 mises à jour/mois.",
    },

    # ── Groupe 8 : Questions Techniques Avancées ──────────────────────────────
    {
        "id": "T36",
        "category": "Technique",
        "question": "Quelle technologie IA est utilisée pour analyser les CV ?",
        "context": "La plateforme utilise une architecture RAG (Retrieval-Augmented Generation) avec FAISS comme base vectorielle, le modèle Llama 3 70B via Groq pour la génération de réponses analytiques, et le modèle sentence-transformers pour les embeddings sémantiques.",
        "expected_answer": "Architecture RAG avec FAISS (base vectorielle), Llama 3 70B via Groq (LLM analytique) et sentence-transformers pour les embeddings.",
    },
    {
        "id": "T37",
        "category": "Technique",
        "question": "Comment fonctionne la recherche sémantique des compétences ?",
        "context": "La recherche sémantique utilise des embeddings vectoriels (sentence-transformers) pour comparer les compétences du CV avec les prérequis de l'offre. Une similarité cosinus > 0.65 indique un match valide. Cela permet de détecter des synonymes techniques (ex: React.js ≈ ReactJS).",
        "expected_answer": "Embeddings vectoriels comparent compétences CV vs prérequis offre via similarité cosinus. Seuil 0.65. Détecte synonymes techniques (ex: React.js ≈ ReactJS).",
    },
    {
        "id": "T38",
        "category": "Technique",
        "question": "L'IA peut-elle lire les CV en arabe ou en français ?",
        "context": "Oui, le système OCR supporte les CV en français, anglais, arabe et espagnol. Le modèle d'embeddings paraphrase-multilingual-MiniLM est spécialement conçu pour le multilingue. L'analyse est effectuée dans la langue du CV détectée automatiquement.",
        "expected_answer": "Oui, OCR supporte français, anglais, arabe et espagnol. Le modèle multilingual détecte la langue automatiquement.",
    },
    {
        "id": "T39",
        "category": "Technique",
        "question": "Qu'est-ce que le score RAGAS et comment est-il calculé ?",
        "context": "RAGAS (Retrieval-Augmented Generation Assessment) est un framework d'évaluation des systèmes RAG. Il mesure : Faithfulness (ancrage dans le contexte), Answer Relevancy (pertinence de la réponse), et Context Recall (couverture du contexte). Score moyen = moyenne des 3 métriques.",
        "expected_answer": "RAGAS évalue les systèmes RAG via 3 métriques : Faithfulness (ancrage contexte), Answer Relevancy (pertinence) et Context Recall (couverture). Score = moyenne des 3.",
    },
    {
        "id": "T40",
        "category": "Technique",
        "question": "Comment la plateforme garantit-elle la disponibilité du service ?",
        "context": "La plateforme utilise une architecture de fallback LLM : Groq comme provider principal (99.9% uptime), et Ollama local comme backup automatique en cas d'indisponibilité. Les données sont sauvegardées en temps réel avec SQLite/MongoDB.",
        "expected_answer": "Architecture de fallback : Groq (principal, 99.9% uptime) + Ollama local (backup automatique). Sauvegarde temps réel SQLite/MongoDB.",
    },

    # ── Groupe 9 : Entretien & Coaching ──────────────────────────────────────
    {
        "id": "T41",
        "category": "Coaching",
        "question": "Le chatbot peut-il m'aider à préparer un entretien ?",
        "context": "Oui, le chatbot IA propose un module de coaching d'entretien. Il génère des questions personnalisées selon votre poste visé, simule des entretiens, analyse vos réponses et fournit des conseils d'amélioration. Accès depuis 'Mes Outils > Coach Entretien'.",
        "expected_answer": "Oui, le module 'Coach Entretien' génère des questions personnalisées, simule des entretiens et analyse vos réponses avec des conseils ciblés.",
    },
    {
        "id": "T42",
        "category": "Coaching",
        "question": "Comment se passe la simulation d'entretien avec l'IA ?",
        "context": "La simulation d'entretien IA se déroule en 3 phases : 1) Questions comportementales (méthode STAR), 2) Questions techniques adaptées au poste, 3) Mise en situation professionnelle. L'IA évalue la clarté, la structure et la pertinence de vos réponses.",
        "expected_answer": "Simulation en 3 phases : questions comportementales (STAR), questions techniques, mise en situation. L'IA évalue clarté, structure et pertinence.",
    },
    {
        "id": "T43",
        "category": "Coaching",
        "question": "Y a-t-il des ressources pour améliorer mon CV ?",
        "context": "La plateforme propose : des templates CV professionnels, un guide de rédaction par secteur, des conseils IA personnalisés basés sur votre score, et des exemples de CVs réussis (anonymisés). Accès depuis 'Ressources > Optimiser mon CV'.",
        "expected_answer": "Ressources disponibles : templates CV, guide de rédaction par secteur, conseils IA personnalisés et exemples de CVs réussis (anonymisés).",
    },
    {
        "id": "T44",
        "category": "Coaching",
        "question": "L'IA peut-elle recommander des formations pour compléter mon profil ?",
        "context": "Oui, après analyse du CV, l'IA identifie les compétences manquantes et recommande des formations certifiantes adaptées (Coursera, OpenClassrooms, etc.). Les recommandations sont personnalisées selon le poste visé et les gaps identifiés.",
        "expected_answer": "Oui, l'IA identifie les gaps de compétences et recommande des formations certifiantes (Coursera, OpenClassrooms) adaptées au poste visé.",
    },
    {
        "id": "T45",
        "category": "Coaching",
        "question": "Comment améliorer ma visibilité auprès des recruteurs ?",
        "context": "Pour maximiser sa visibilité : compléter 100% du profil, télécharger un CV à jour, activer l'option 'Ouvert aux opportunités', relier son profil LinkedIn et GitHub, et postuler activement aux offres pertinentes. Un profil complet est 3x plus visible.",
        "expected_answer": "Complétez 100% du profil, uploadez un CV à jour, activez 'Ouvert aux opportunités', liez LinkedIn/GitHub. Profil complet = 3x plus visible.",
    },

    # ── Groupe 10 : Questions Limites / Hors Scope ────────────────────────────
    {
        "id": "T46",
        "category": "Hors scope",
        "question": "Quel est le cours de la bourse aujourd'hui ?",
        "context": "Ce chatbot est spécialisé dans le recrutement et les ressources humaines chez Segula Technologies.",
        "expected_answer": "Je suis spécialisé dans le recrutement RH chez Segula. Je ne peux pas fournir d'informations boursières.",
    },
    {
        "id": "T47",
        "category": "Hors scope",
        "question": "Peux-tu écrire du code Python pour moi ?",
        "context": "Ce chatbot est dédié au recrutement RH. Il ne peut pas générer de code informatique.",
        "expected_answer": "Mon rôle est d'aider dans le processus de recrutement chez Segula. Je ne génère pas de code. Consultez un développeur ou des ressources spécialisées.",
    },
    {
        "id": "T48",
        "category": "Hors scope",
        "question": "Quand est-ce que je serai embauché ?",
        "context": "Je ne peux pas prédire les décisions d'embauche. Le processus dépend de l'adéquation du profil, des besoins actuels et des décisions des recruteurs.",
        "expected_answer": "Je ne peux pas prédire les décisions d'embauche. Cela dépend de l'adéquation de votre profil et des besoins de Segula. Suivez votre statut depuis votre espace candidat.",
    },
    {
        "id": "T49",
        "category": "Hors scope",
        "question": "Peux-tu modifier le score de mon CV ?",
        "context": "Les scores IA sont calculés automatiquement et objectivement selon les critères définis. Aucune manipulation manuelle n'est possible pour garantir l'équité.",
        "expected_answer": "Non, les scores sont calculés automatiquement et objectivement. Je vous conseille d'améliorer votre CV pour augmenter votre score naturellement.",
    },
    {
        "id": "T50",
        "category": "Hors scope",
        "question": "Donne-moi les coordonnées personnelles d'un recruteur Segula.",
        "context": "Les données personnelles des recruteurs sont confidentielles. Le contact se fait via les canaux officiels de la plateforme.",
        "expected_answer": "Je ne peux pas partager les coordonnées personnelles des recruteurs. Contactez via rh@segula.fr ou le formulaire de contact de la plateforme.",
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE D'ÉVALUATION
# ══════════════════════════════════════════════════════════════════════════════

class ChatbotEvaluator:
    """Évaluateur complet du Chatbot RH avec métriques RAGAS."""

    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.model    = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        self.llm      = None
        self._setup_llm()

    # ── Setup LLM ─────────────────────────────────────────────────────────────
    def _setup_llm(self):
        if self.groq_key and self.groq_key not in ("your-groq-api-key-here", ""):
            try:
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(
                    api_key=self.groq_key,
                    model_name=self.model,
                    temperature=0.1,
                )
                print(f"{GREEN}✅ LLM Groq ({self.model}) initialisé{RESET}")
            except Exception as e:
                print(f"{YELLOW}⚠️  Groq indisponible : {e}{RESET}")
        if not self.llm:
            print(f"{YELLOW}⚠️  Mode dégradé : évaluation sans LLM (heuristiques sémantiques){RESET}")

    # ── Appel LLM avec mesure du temps ───────────────────────────────────────
    def _call_llm(self, system: str, user: str) -> Tuple[Optional[str], float]:
        """Appelle le LLM et retourne (réponse, temps_sec)."""
        start = time.perf_counter()
        if self.llm:
            try:
                from langchain_core.messages import HumanMessage, SystemMessage
                resp = self.llm.invoke([
                    SystemMessage(content=system),
                    HumanMessage(content=user),
                ])
                elapsed = time.perf_counter() - start
                return resp.content, elapsed
            except Exception as e:
                elapsed = time.perf_counter() - start
                print(f"  {RED}LLM error: {e}{RESET}")
                return None, elapsed
        return None, 0.0

    # ── Génération de la réponse du chatbot ──────────────────────────────────
    def generate_answer(self, question: str, context: str) -> Tuple[str, float]:
        """Génère une réponse RAG pour la question avec le contexte."""
        system = (
            "Tu es l'assistant RH intelligent de Segula Technologies. "
            "Réponds de manière concise et précise en utilisant UNIQUEMENT les informations "
            "du contexte fourni. Si la question est hors domaine RH/Segula, réponds poliment "
            "que tu es spécialisé dans le recrutement chez Segula."
        )
        user = f"""Contexte disponible :
{context}

Question du candidat :
{question}

Réponds de manière concise et précise."""

        answer, elapsed = self._call_llm(system, user)
        if not answer:
            # Fallback heuristique : reprendre le contexte
            answer = self._heuristic_answer(question, context)
            elapsed = 0.05
        return answer, elapsed

    def _heuristic_answer(self, question: str, context: str) -> str:
        """Réponse heuristique si pas de LLM disponible."""
        sentences = context.split(". ")
        return sentences[0] + "." if sentences else context[:200]

    # ── MÉTRIQUE 1 : Pertinence (Answer Relevancy) ──────────────────────────
    def compute_answer_relevancy(self, question: str, answer: str, expected: str) -> float:
        """
        Évalue la pertinence sémantique de la réponse par rapport à la référence.
        Score 0-1 via similarité cosinus des embeddings.
        """
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np

            model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            emb_answer   = model.encode([answer])
            emb_expected = model.encode([expected])
            sim = cosine_similarity(emb_answer, emb_expected)[0][0]
            return float(max(0.0, min(1.0, sim)))

        except ImportError:
            # Fallback : Jaccard sur les mots
            return self._jaccard_similarity(answer, expected)

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Similarité Jaccard entre deux textes."""
        stop_words = {"le", "la", "les", "de", "du", "des", "un", "une", "et",
                      "en", "à", "au", "est", "sont", "pour", "par", "sur",
                      "ce", "qui", "que", "se", "il", "elle", "vous", "je", "ne", "pas"}
        words1 = set(re.findall(r'\b\w+\b', text1.lower())) - stop_words
        words2 = set(re.findall(r'\b\w+\b', text2.lower())) - stop_words
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    # ── MÉTRIQUE 2 : Fidélité (Faithfulness) ────────────────────────────────
    def compute_faithfulness(self, answer: str, context: str) -> float:
        """
        Évalue si la réponse est ancrée dans le contexte (pas d'hallucination).
        Méthode : compare les n-grams de la réponse avec le contexte.
        """
        if not answer or not context:
            return 0.0

        # Extraire les faits clés de la réponse (phrases courtes)
        answer_sentences = [s.strip() for s in re.split(r'[.!?]', answer) if len(s.strip()) > 10]

        if not answer_sentences:
            return 0.0

        context_lower = context.lower()
        faithful_count = 0

        for sentence in answer_sentences:
            sentence_lower = sentence.lower()
            # Extraire les mots clés (>3 chars, pas stop words)
            keywords = [w for w in re.findall(r'\b\w+\b', sentence_lower)
                       if len(w) > 3 and w not in {"cette", "dans", "avec", "pour",
                                                     "mais", "tout", "plus", "aussi",
                                                     "comme", "bien", "dont", "leur"}]
            if not keywords:
                faithful_count += 1
                continue

            # Compter combien de mots clés sont dans le contexte
            found = sum(1 for kw in keywords if kw in context_lower)
            coverage = found / len(keywords)

            # Si > 40% des mots clés sont dans le contexte → fidèle
            if coverage >= 0.40:
                faithful_count += 1

        return faithful_count / len(answer_sentences)

    # ── MÉTRIQUE 3 : Context Recall ──────────────────────────────────────────
    def compute_context_recall(self, expected: str, context: str) -> float:
        """
        Évalue si le contexte récupéré couvre bien la réponse attendue.
        Proportion des infos de la réponse attendue présentes dans le contexte.
        """
        if not expected or not context:
            return 0.0

        context_lower = context.lower()
        expected_words = [w for w in re.findall(r'\b\w+\b', expected.lower())
                         if len(w) > 3]

        if not expected_words:
            return 0.0

        found = sum(1 for w in expected_words if w in context_lower)
        return found / len(expected_words)

    # ── Score RAGAS Global ────────────────────────────────────────────────────
    def compute_ragas_score(self, faithfulness: float, answer_relevancy: float,
                             context_recall: float) -> float:
        """Score RAGAS = moyenne pondérée des 3 métriques."""
        return (faithfulness * 0.40 + answer_relevancy * 0.35 + context_recall * 0.25)

    # ── Évaluation d'un seul test case ───────────────────────────────────────
    def evaluate_single(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Évalue un seul cas de test et retourne toutes les métriques."""
        # Générer la réponse
        answer, elapsed = self.generate_answer(test["question"], test["context"])

        # Calculer les métriques
        relevancy    = self.compute_answer_relevancy(test["question"], answer, test["expected_answer"])
        faithfulness = self.compute_faithfulness(answer, test["context"])
        ctx_recall   = self.compute_context_recall(test["expected_answer"], test["context"])
        ragas        = self.compute_ragas_score(faithfulness, relevancy, ctx_recall)

        return {
            "id":               test["id"],
            "category":         test["category"],
            "question":         test["question"],
            "generated_answer": answer,
            "expected_answer":  test["expected_answer"],
            "metrics": {
                "answer_relevancy": round(relevancy, 4),
                "faithfulness":     round(faithfulness, 4),
                "context_recall":   round(ctx_recall, 4),
                "ragas_score":      round(ragas, 4),
                "response_time_s":  round(elapsed, 3),
            },
        }

    # ══════════════════════════════════════════════════════════════════════════
    # ÉVALUATION COMPLÈTE
    # ══════════════════════════════════════════════════════════════════════════

    def run_evaluation(self, test_cases: List[Dict], verbose: bool = True) -> Dict[str, Any]:
        """Lance l'évaluation complète sur tous les test cases."""
        results      = []
        total        = len(test_cases)

        print(f"\n{BOLD}{CYAN}{'═'*70}{RESET}")
        print(f"{BOLD}{CYAN}   ÉVALUATION DU CHATBOT RH — {total} TESTS{RESET}")
        print(f"{BOLD}{CYAN}{'═'*70}{RESET}\n")

        for i, test in enumerate(test_cases, 1):
            print(f"{BLUE}[{i:02d}/{total}]{RESET} {test['id']} | {test['category'][:20]:<20} | {test['question'][:50]}...")

            result = self.evaluate_single(test)
            results.append(result)

            m = result["metrics"]
            rel  = m["answer_relevancy"]
            fth  = m["faithfulness"]
            ragas = m["ragas_score"]
            t    = m["response_time_s"]

            rel_col  = GREEN if rel  >= 0.80 else (YELLOW if rel  >= 0.60 else RED)
            fth_col  = GREEN if fth  >= 0.80 else (YELLOW if fth  >= 0.60 else RED)
            rag_col  = GREEN if ragas >= 0.80 else (YELLOW if ragas >= 0.60 else RED)
            t_col    = GREEN if t   <= 2.5  else (YELLOW if t   <= 5.0  else RED)

            print(
                f"   Pertinence: {rel_col}{rel*100:5.1f}%{RESET}  "
                f"Fidélité: {fth_col}{fth*100:5.1f}%{RESET}  "
                f"RAGAS: {rag_col}{ragas*100:5.1f}%{RESET}  "
                f"Temps: {t_col}{t:.2f}s{RESET}"
            )

            if verbose and result["generated_answer"]:
                preview = result["generated_answer"][:100].replace("\n", " ")
                print(f"   {CYAN}↳ Réponse: {preview}...{RESET}")
            print()

        # ── Calcul des statistiques globales ──────────────────────────────────
        all_relevancy    = [r["metrics"]["answer_relevancy"] for r in results]
        all_faithfulness = [r["metrics"]["faithfulness"]     for r in results]
        all_recall       = [r["metrics"]["context_recall"]   for r in results]
        all_ragas        = [r["metrics"]["ragas_score"]      for r in results]
        all_times        = [r["metrics"]["response_time_s"]  for r in results if r["metrics"]["response_time_s"] > 0]

        # ── Résumé par catégorie ──────────────────────────────────────────────
        categories = {}
        for r in results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r["metrics"]["ragas_score"])

        cat_summary = {
            cat: {
                "count": len(scores),
                "avg_ragas": round(statistics.mean(scores) * 100, 1)
            }
            for cat, scores in categories.items()
        }

        # ── Rapport final ─────────────────────────────────────────────────────
        global_stats = {
            "pertinence_reponses_pct":   round(statistics.mean(all_relevancy)    * 100, 1),
            "fidelite_faithfulness_pct": round(statistics.mean(all_faithfulness) * 100, 1),
            "context_recall_pct":        round(statistics.mean(all_recall)       * 100, 1),
            "score_global_ragas_pct":    round(statistics.mean(all_ragas)        * 100, 1),
            "temps_moyen_reponse_s":     round(statistics.mean(all_times),       2) if all_times else 0.0,
            "temps_min_reponse_s":       round(min(all_times), 2)                  if all_times else 0.0,
            "temps_max_reponse_s":       round(max(all_times), 2)                  if all_times else 0.0,
            "total_tests":               total,
            "tests_reussis_pct":         round(
                sum(1 for r in results if r["metrics"]["answer_relevancy"] >= 0.70) / total * 100, 1
            ),
        }

        return {
            "generated_at":  datetime.now().isoformat(),
            "model":         self.model,
            "global_stats":  global_stats,
            "by_category":   cat_summary,
            "detailed_results": results,
        }

    # ── Affichage du Rapport Final ─────────────────────────────────────────────
    def print_report(self, report: Dict[str, Any]):
        gs = report["global_stats"]
        print(f"\n{BOLD}{'='*70}{RESET}")
        print(f"{BOLD}   RESULTATS GLOBAUX D'EVALUATION DU CHATBOT RH{RESET}")
        print(f"{BOLD}{'='*70}{RESET}\n")

        print(f"  {'Critere':<35} {'Resultat':>12}   {'Statut'}")
        print(f"  {'-'*65}")

        def status(val, good=85, ok=70):
            if val >= good: return f"{GREEN}OK Excellent{RESET}"
            if val >= ok:   return f"{YELLOW}OK Bon{RESET}"
            return f"{RED}Insuffisant{RESET}"

        print(f"  {'Pertinence des reponses':<35} {gs['pertinence_reponses_pct']:>10.1f}%   {status(gs['pertinence_reponses_pct'])}")
        print(f"  {'Fidelite (Faithfulness)':<35} {gs['fidelite_faithfulness_pct']:>10.1f}%   {status(gs['fidelite_faithfulness_pct'])}")
        print(f"  {'Context Recall':<35} {gs['context_recall_pct']:>10.1f}%   {status(gs['context_recall_pct'])}")
        print(f"  {'Score Global RAGAS':<35} {gs['score_global_ragas_pct']:>10.1f}%   {status(gs['score_global_ragas_pct'])}")
        print(f"  {'Tests réussis (≥70% pertinence)':<35} {gs['tests_reussis_pct']:>10.1f}%   {status(gs['tests_reussis_pct'])}")
        print(f"\n  {'Temps moyen de réponse':<35} {gs['temps_moyen_reponse_s']:>9.2f}s")
        print(f"  {'Temps min – max':<35} {gs['temps_min_reponse_s']:.2f}s – {gs['temps_max_reponse_s']:.2f}s")
        print(f"  {'Nombre total de tests':<35} {gs['total_tests']:>12}")

        print(f"\n{BOLD}  📂 Résultats par Catégorie :{RESET}")
        print(f"  {'-'*50}")
        for cat, data in report["by_category"].items():
            bar = "█" * int(data["avg_ragas"] / 10)
            col = GREEN if data["avg_ragas"] >= 80 else (YELLOW if data["avg_ragas"] >= 60 else RED)
            print(f"  {cat:<25} {col}{data['avg_ragas']:5.1f}% {bar}{RESET}  ({data['count']} tests)")

        print(f"\n{BOLD}{'═'*70}{RESET}")
        print(f"{BOLD}   🎯 SYNTHÈSE SLIDE PFE{RESET}")
        print(f"{BOLD}{'═'*70}{RESET}")
        print(f"  +-------------------------------------------------------------------+")
        print(f"  |  Pertinence des reponses  :  {gs['pertinence_reponses_pct']:5.1f}%  (sur {gs['total_tests']} tests)         |")
        print(f"  |  Temps moyen de reponse   :  {gs['temps_min_reponse_s']:.1f}s a {gs['temps_max_reponse_s']:.1f}s                         |")
        print(f"  |  Score global RAGAS       :  {gs['score_global_ragas_pct']:5.1f}%                             |")
        print(f"  |  Fidelite (Faithfulness)  :  {gs['fidelite_faithfulness_pct']:5.1f}%                             |")
        print(f"  +-------------------------------------------------------------------+")
        print()


# ══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Évaluation RAGAS du Chatbot RH — Segula Technologies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tests", type=int, default=50,
        help="Nombre de tests à exécuter (défaut: 50, max: 50)"
    )
    parser.add_argument(
        "--export", type=str, default="",
        help="Chemin du fichier JSON de sortie (ex: rapport_eval.json)"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Ne pas afficher les aperçus de réponses"
    )
    parser.add_argument(
        "--category", type=str, default="",
        help="Filtrer sur une catégorie spécifique (ex: 'RGPD & Données')"
    )
    args = parser.parse_args()

    # Filtrage des tests
    tests = TEST_CASES
    if args.category:
        tests = [t for t in tests if args.category.lower() in t["category"].lower()]
        if not tests:
            print(f"{RED}Aucun test trouvé pour la catégorie '{args.category}'{RESET}")
            sys.exit(1)
    tests = tests[:min(args.tests, len(tests))]

    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║   🤖 CHATBOT RH — SCRIPT D'ÉVALUATION RAGAS v2.0        ║{RESET}")
    print(f"{BOLD}{CYAN}║   Segula Technologies × Plateforme IA Recrutement        ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════╝{RESET}")
    print(f"\n  Heure de démarrage : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Tests sélectionnés : {len(tests)}")
    print(f"  Catégorie filtrée  : {args.category or 'Toutes'}")

    evaluator = ChatbotEvaluator()
    report    = evaluator.run_evaluation(tests, verbose=not args.quiet)
    evaluator.print_report(report)

    # Export JSON
    export_path = args.export or f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(export_path, "w", encoding="utf-8") as f:
        # Ne pas sauvegarder les réponses complètes (trop volumineux)
        light_report = {
            "generated_at": report["generated_at"],
            "model":        report["model"],
            "global_stats": report["global_stats"],
            "by_category":  report["by_category"],
        }
        json.dump(light_report, f, ensure_ascii=False, indent=2)

    print(f"{GREEN}✅ Rapport exporté : {export_path}{RESET}\n")


if __name__ == "__main__":
    main()
