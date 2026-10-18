from pathlib import Path
import ast,csv,json
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'REGROUPEMENT.json').read_text(encoding='utf-8'))

def explain(project,path):
    p=Path(path);parts=p.parts;first=parts[0];suffix=p.suffix.lower();text=str(p).replace('\\','/')
    if first=='.git':return 'PROVENANCE','Métadonnées Git','Conserver la provenance et les historiques séparés ; ce fichier ne décrit pas le modèle actif.'
    if '__pycache__' in parts or suffix=='.pyc':return 'CACHE_REGENERABLE','Cache Python','Conservé dans la copie complète ; accélère les imports mais peut être régénéré et ne constitue pas une source.'
    if project=='garry':
        if text=='web/models/garry.json':return 'ACTIF','Poids Garry partagé','Nécessaire pour restituer le niveau appris ; le code seul ne contient pas ces paramètres.'
        if text.startswith('training/continuous/19159dcbbae2412c876e1c729a3b606f/'):return 'ARCHIVE_INVALIDE','Session invalidée','Garder la trace de contamination et de restauration ; ne pas compter cette session comme preuve de progrès.'
        rules={'logic_arena':('MOTEUR','Moteur et API Garry','Règles, agents, décisions et sessions nécessaires au fonctionnement et à leur vérification.'),'web':('INTERFACE','Interface ou ressource navigateur','Jouer, afficher les transitions et exposer les agents et réglages disponibles.'),'tests':('VERIFICATION','Test Garry','Détecter les régressions de règles, niveaux, modèle ou protocole.'),'training':('ARCHIVE_EXPERIMENTALE','Trace ou donnée de session','Reproduire les décisions de promotion et vérifier les résultats ; pas une performance générale garantie.'),'training-runs':('ARCHIVE_EXPERIMENTALE','Expérience antérieure','Conserver les données et résultats des étapes précédentes pour comparaison.'),'versions':('REFERENCE_FIGEE','Ancienne version','Comparer les versions et préserver les références des duels ; ne pas confondre avec le modèle courant.'),'tools':('OUTIL','Harnais ou compilation','Relier les jeux réels ou accélérer la recherche ; garder sources et ressources utilisées.'),'search':('MOTEUR','Recherche spécialisée','Conserver les algorithmes de recherche utilisés avec les évaluations neuronales.'),'examples':('PROTOCOLE','Programme expérimental','Reproduire la préparation, l’apprentissage ou une mesure ; lire le plan avant réutilisation.'),'docs':('DOCUMENTATION_HISTORIQUE','Rapport Garry','Expliquer le protocole et les limites à la date du rapport ; le plan commun fixe les priorités actuelles.')}
    elif project=='input':
        if text=='models/chat/active.json':return 'ACTIF','Sélecteur de checkpoint','Désigner l’adaptation validée plutôt que charger le dernier fichier créé.'
        if text=='models/chat_base.json':return 'ACTIF','Identité et chemin de base','Charger localement la base et conserver sa révision et sa provenance.'
        if text.startswith('models/chat/'):return 'POIDS_OU_BILAN','Adaptation ou trace de sélection','Restaurer les poids, comparer les candidats et comprendre la sélection ; tous les checkpoints ne sont pas actifs.'
        if text.startswith(('models/scratch/','models/pretrained/','models/tokenizer/')):return 'ARCHIVE_EXPERIMENTALE','Premier classifieur ou tokenizer','Conserver la comparaison initiale de compréhension limitée ; distinct du dialogue actuel.'
        rules={'web':('INTERFACE','Conversation ou bilan','Présenter le dialogue et ses mesures ; la recette de l’interface reste une priorité.'),'tests':('VERIFICATION','Test Input','Vérifier format, contexte, données et protocoles sans confondre ces tests avec une maîtrise générale.'),'chat_cache':('POIDS_BASE','Cache Qwen et tokenizer','Recharger les poids préentraînés localement sans nouveau téléchargement.'),'cache':('ARCHIVE_MODELE','Cache des premières expériences','Préserver les bases utilisées par les classifieurs et la reproductibilité.'),'corpus_cache':('CORPUS_ARCHIVE','Corpus importé','Conserver la provenance et éviter un nouveau téléchargement ; la présence ne prouve pas son apprentissage et n’impose pas sa réutilisation.'),'corpus':('PROVENANCE','Manifeste du corpus','Identifier les fichiers, leurs sources, tailles, révisions et emplacements locaux.'),'chat_data':('DONNEES_SUPERVISEES','Dialogues ou exercices','Conserver les exemples réellement prévus et leurs séparations apprentissage/validation/test.'),'data':('ARCHIVE_EXPERIMENTALE','Premier banc de compréhension','Reproduire la classification initiale, distincte des décisions générales.'),'lexicon':('VOCABULAIRE','Lexique, sens ou attribution','Préparer les exercices français avec provenance ; petit échantillon non exhaustif.'),'results':('BILAN','Résultat ou journal','Distinguer apprentissage, sélection, erreurs et coût réel ; lire la date du résultat.')}
    else:
        rules={'weight_cache':('POIDS_RECHERCHE','Poids officiels HRM','Initialiser le prototype avec les poids dont la révision et l’empreinte sont connues.'),'models':('RECHERCHE','Architecture récursive','Étudier la représentation et le raisonnement ; pas un cœur général déjà connecté à Input.'),'tests':('VERIFICATION','Test du prototype','Contrôler l’interface continue, les masques et les gradients ; pas un score de compréhension générale.'),'local_results':('BILAN_RECHERCHE','Contrôle technique HRM','Conserver succès et échecs réels sans les transformer en benchmark général.'),'dataset':('OUTIL_RECHERCHE','Préparation de données amont','Reproduire les protocoles amont ; ne prouve pas que les données ont été téléchargées ou utilisées.'),'config':('CONFIGURATION','Configuration de recherche','Conserver les réglages amont pour comprendre les expériences et leurs ressources.'),'assets':('DOCUMENTATION','Illustration amont','Comprendre l’architecture et conserver la documentation du fork.'),'kaggle':('DONNEE_REFERENCE','Référence ARC incluse par amont','Conserver exactement le contenu livré avec la référence ; aucun nouvel entraînement implicite.')}
    if first in rules:return rules[first]
    if p.name.lower().startswith(('license','copying')):return 'LICENCE','Licence et attribution','Conserver les conditions et auteurs associés au code ou aux données.'
    if suffix=='.md':return 'DOCUMENTATION','Documentation du composant','Expliquer l’état et les protocoles ; en cas de priorité contradictoire, suivre le plan commun.'
    if p.name in ('requirements.txt','specific_requirements.txt','pyproject.toml','local_environment.json'):return 'DEPENDANCES','Versions et dépendances','Reconstituer l’environnement utilisé sans prétendre qu’il est portable tel quel.'
    if suffix=='.py':return 'SOURCE','Module ou programme','Conserver le code exécutable et sa provenance ; consulter son rôle documenté avant usage.'
    return 'CONFIGURATION_OU_RESSOURCE','Ressource du dépôt','Préserver la copie complète et le contexte de fonctionnement ; aucun rôle actif présumé sans lecture du composant.'

rows=[]
for project in manifest['projects']:
    dest=Path(project['destination']);label=dest.name
    for entry in project['files']:
        status,role,reason=explain(label,entry['path']);p=dest/entry['path'];description=''
        if p.suffix=='.py':
            try:description=(ast.get_docstring(ast.parse(p.read_text(encoding='utf-8-sig'))) or '').replace('\n',' ')[:300]
            except (OSError,UnicodeError,SyntaxError):pass
        rows.append({'ensemble':label,'chemin':str(p.relative_to(ROOT)),'statut':status,'role':role,'justification':reason,'documentation_module':description,'octets_copie':entry['bytes'],'sha256_a_la_copie':entry['sha256']})
# Include the conversation's pre-existing resources without importing or hashing libraries.
for base,dirs,files in __import__('os').walk(ROOT):
    current=Path(base);relative=current.relative_to(ROOT)
    if not relative.parts:dirs[:]=[d for d in dirs if d not in ('projets','recherche','.git')]
    for name in files:
        p=current/name;rel=p.relative_to(ROOT)
        if name=='CATALOGUE-FICHIERS.csv':continue
        first=rel.parts[0]
        if first=='work':
            category=rel.parts[1] if len(rel.parts)>1 else ''
            if category in ('text-env','python-deps','browsers','compiler'):status='ENVIRONNEMENT';role='Dépendance ou outil local';reason='Conserver l’environnement et les ressources déjà employés ; les prérequis machine restent documentés séparément.'
            else:status='ARCHIVE_PREPARATOIRE';role='Préparation historique';reason='Conserver les étapes de travail ; éditer les projets regroupés pour la suite et ne pas relancer un ancien script sans lire le plan.'
        elif first=='outputs':status='PREUVE_HISTORIQUE';role='Rapport, capture ou trace';reason='Étayer les résultats annoncés et les erreurs rencontrées, en tenant compte de la date et du protocole.'
        else:status='DOCUMENTATION_OU_CONTROLE';role='Documentation commune ou manifeste';reason='Rendre le dossier compréhensible et vérifiable, avec ses décisions et limites.'
        try:size=p.stat().st_size
        except OSError:size=''
        rows.append({'ensemble':'conversation','chemin':str(rel),'statut':status,'role':role,'justification':reason,'documentation_module':'','octets_copie':size,'sha256_a_la_copie':''})
fields=list(rows[0])
with (ROOT/'CATALOGUE-FICHIERS.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields,delimiter=';');writer.writeheader();writer.writerows(rows)
print(json.dumps({'catalogue_entries':len(rows),'copied_project_files':manifest['total_files'],'note':'SHA-256 recorded for copied project files; existing workspace tools inventoried without new hashing'}))
