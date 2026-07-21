import os
import json
from datetime import datetime
import unicodedata
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, colorchooser
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement

def charger_gedcom(chemin_gedcom):
    gedcom_parser = Parser()
    gedcom_parser.parse_file(chemin_gedcom)
    return gedcom_parser

def generer_nom_fichier_php(ind_element):
    p = ind_element.get_pointer().replace('@', '')
    n = "".join(ind_element.get_name()[1]).strip().lower()
    pr = "".join(ind_element.get_name()[0]).strip().lower()
    nom_brut = f"{p}-{pr}-{n}"
    nom_nettoye = "".join(c for c in unicodedata.normalize("NFD", nom_brut) if unicodedata.category(c) != 'Mn')
    return f"{nom_nettoye}.php"

def trouver_individu_par_id(target_id, gedcom_parser):
    for e in gedcom_parser.get_root_element().get_child_elements():
        if isinstance(e, IndividualElement) and e.get_pointer() == target_id:
            return e
    return None

def est_individu_vivant(ind_element, annee_actuelle):
    birth_date = "Inconnue"
    a_une_date_deces = False
    for child in ind_element.get_child_elements():
        if child.get_tag() == 'BIRT':
            for sub in child.get_child_elements():
                if sub.get_tag() == 'DATE': birth_date = sub.get_value().strip()
        if child.get_tag() == 'DEAT':
            a_une_date_deces = True

    if a_une_date_deces:
        return False

    annee_naissance = None
    if birth_date and birth_date not in ["Inconnu", "Inconnue", ""]:
        mots = birth_date.split()
        for mot in mots:
            if mot.isdigit() and len(mot) == 4:
                annee_naissance = int(mot)
                break

    if annee_naissance:
        if (annee_actuelle - annee_naissance) >= 100:
            return False
        else:
            return True
    else:
        return True

def obtenir_php_tracking_header(ip_exclue, url_domaine=""):
    ip_filtrage = ip_exclue.strip() if ip_exclue.strip() else "0.0.0.0"
    
    # Construction de la ligne de redirection HTTPS si un domaine est renseigné
    code_redirection_https = ""
    if url_domaine.strip():
        domaine_clean = url_domaine.strip().replace("https://", "").replace("http://", "").rstrip("/")
        code_redirection_https = f"""
if (empty($_SERVER['HTTPS']) || $_SERVER['HTTPS'] === 'off') {{
    $url_securisee = 'https://{domaine_clean}' . $_SERVER['REQUEST_URI'];
    header('HTTP/1.1 301 Moved Permanently');
    header('Location: ' . $url_securisee);
    exit();
}}"""

    return f"""<?php
// Script de compteur et tracking de visites (Compatible Multi-hébergeurs & RGPD)
$fichier_stats = rtrim($_SERVER['DOCUMENT_ROOT'], '/') . '/stats.json';

function obtenir_os($user_agent) {{
    $os_platform = "Inconnu";
    $os_array = array(
        '/windows nt 10/i'      =>  'Windows 10/11',
        '/windows nt 6.3/i'     =>  'Windows 8.1',
        '/windows nt 6.2/i'     =>  'Windows 8',
        '/windows nt 6.1/i'     =>  'Windows 7',
        '/macintosh|mac os x/i' =>  'Mac OS X',
        '/linux/i'              =>  'Linux',
        '/ubuntu/i'             =>  'Ubuntu',
        '/iphone/i'             =>  'iPhone (iOS)',
        '/ipod/i'               =>  'iPod (iOS)',
        '/ipad/i'               =>  'iPad (iOS)',
        '/android/i'            =>  'Android'
    );
    foreach ($os_array as $regex => $value) {{
        if (preg_match($regex, $user_agent)) {{ $os_platform = $value; break; }}
    }}
    return $os_platform;
}}

function est_robot($user_agent) {{
    $bots = array('googlebot', 'bingbot', 'slurp', 'duckduckbot', 'baiduspider', 'yandexbot', 'sogou', 'exabot', 'facebot', 'ia_archiver', 'scan', 'bot');
    foreach ($bots as $bot) {{
        if (strpos(strtolower($user_agent), $bot) !== false) {{ return "Robot/Scan"; }}
    }}
    return "Utilisateur";
}}

$ip_brute = $_SERVER['REMOTE_ADDR'];

if ($ip_brute !== '{ip_filtrage}') {{
    if (strpos($ip_brute, '.') !== false) {{
        $ip = preg_replace('/\\.\\d+$/', '.0', $ip_brute);
    }} else {{
        $ip = preg_replace('/:[a-f0-9]+$/i', ':0', $ip_brute);
    }}

    $page = (dirname($_SERVER['PHP_SELF']) != '/' ? basename(dirname($_SERVER['PHP_SELF'])). '/' : '') . basename($_SERVER['PHP_SELF']);
    $referer = isset($_SERVER['HTTP_REFERER']) ? $_SERVER['HTTP_REFERER'] : 'Direct / Favoris';
    $user_agent = isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : '';
    $date_complete = date('Y-m-d H:i:s');
    $mois = date('Y-m');

    $os = obtenir_os($user_agent);
    $type_visiteur = est_robot($user_agent);

    $nouvelle_visite = array(
        "date" => $date_complete,
        "mois" => $mois,
        "page" => $page,
        "ip" => $ip,
        "referer" => $referer,
        "robot" => $type_visiteur,
        "os" => $os
    );

    $historique = [];
    if (file_exists($fichier_stats)) {{
        $contenu = file_get_contents($fichier_stats);
        $historique = json_decode($contenu, true);
        if (!is_array($historique)) {{ $historique = []; }}
    }}

    $historique[] = $nouvelle_visite;

    if (count($historique) > 5000) {{
        $historique = array_slice($historique, -5000);
    }}

    file_put_contents($fichier_stats, json_encode($historique));
}}{code_redirection_https}
?>
"""

def generer_page_individu(individu, gedcom_parser, output_dir, config):
    annee_actuelle = datetime.now().year
    est_vivant = est_individu_vivant(individu, annee_actuelle)

    if est_vivant:
        return

    pointer = individu.get_pointer()
    nom = "".join(individu.get_name()[1]).strip()
    prenom = "".join(individu.get_name()[0]).strip()
    
    birth_date = "Inconnue"
    birth_place = "Inconnu"
    death_date = "Inconnu"
    death_place = "Inconnu"

    for child in individu.get_child_elements():
        if child.get_tag() == 'BIRT':
            for sub in child.get_child_elements():
                if sub.get_tag() == 'DATE': birth_date = sub.get_value().strip()
                if sub.get_tag() == 'PLAC': birth_place = sub.get_value().strip()
        if child.get_tag() == 'DEAT':
            for sub in child.get_child_elements():
                if sub.get_tag() == 'DATE': death_date = sub.get_value().strip()
                if sub.get_tag() == 'PLAC': death_place = sub.get_value().strip()

    nom_affichage = nom
    prenom_affichage = prenom
    if death_date != "Inconnu" and death_date != "":
        ligne_deces_html = f"<p><strong>⚰️ Décès :</strong> Le {death_date} — 📍 {death_place}</p>"
    else:
        ligne_deces_html = "<p><strong>⚰️ Décès :</strong> Supposé(e) décédé(e)</p>"

    parents_html = ""
    id_familles_parents = []
    for c in individu.get_child_elements():
        if c.get_tag() == 'FAMC': id_familles_parents.append(c.get_value())

    for root_child in gedcom_parser.get_root_element().get_child_elements():
        if isinstance(root_child, FamilyElement) and root_child.get_pointer() in id_familles_parents:
            id_pere, id_mere = "", ""
            for sub in root_child.get_child_elements():
                if sub.get_tag() == 'HUSB': id_pere = sub.get_value()
                if sub.get_tag() == 'WIFE': id_mere = sub.get_value()
            if id_pere:
                p_obj = trouver_individu_par_id(id_pere, gedcom_parser)
                if p_obj:
                    if est_individu_vivant(p_obj, annee_actuelle):
                        parents_html += "<li><strong>Père :</strong> Confidentiel</li>"
                    else:
                        p_nom = ' '.join(p_obj.get_name()).strip()
                        parents_html += f"<li><strong>Père :</strong> <a href='{generer_nom_fichier_php(p_obj)}'>{p_nom}</a></li>"
            if id_mere:
                m_obj = trouver_individu_par_id(id_mere, gedcom_parser)
                if m_obj:
                    if est_individu_vivant(m_obj, annee_actuelle):
                        parents_html += "<li><strong>Mère :</strong> Confidentiel</li>"
                    else:
                        m_nom = ' '.join(m_obj.get_name()).strip()
                        parents_html += f"<li><strong>Mère :</strong> <a href='{generer_nom_fichier_php(m_obj)}'>{m_nom}</a></li>"

    if not parents_html: parents_html = "<li>Aucun parent répertorié.</li>"

    conjoints_html = ""
    enfants_html = ""
    id_familles_unions = []
    for c in individu.get_child_elements():
        if c.get_tag() == 'FAMS': id_familles_unions.append(c.get_value())

    for root_child in gedcom_parser.get_root_element().get_child_elements():
        if isinstance(root_child, FamilyElement) and root_child.get_pointer() in id_familles_unions:
            id_pere, id_mere = "", ""
            for sub in root_child.get_child_elements():
                if sub.get_tag() == 'HUSB': id_pere = sub.get_value()
                if sub.get_tag() == 'WIFE': id_mere = sub.get_value()

            id_conjoint = id_mere if id_pere == pointer else id_pere
            
            mariage_info = ""
            has_marriage = False
            m_date, m_place = "Date inconnue", "Lieu inconnu"
            for sub in root_child.get_child_elements():
                if sub.get_tag() == 'MARR':
                    has_marriage = True
                    for m_sub in sub.get_child_elements():
                        if m_sub.get_tag() == 'DATE': m_date = m_sub.get_value()
                        if m_sub.get_tag() == 'PLAC': m_place = m_sub.get_value()

            if id_conjoint:
                c_obj = trouver_individu_par_id(id_conjoint, gedcom_parser)
                if c_obj:
                    if est_individu_vivant(c_obj, annee_actuelle):
                        conjoints_html += "<li>💑 Confidentiel</li>"
                    else:
                        if has_marriage:
                            mariage_info = f" - 💍 Mariage le {m_date} à {m_place}"
                        c_nom = ' '.join(c_obj.get_name()).strip()
                        conjoints_html += f"<li>💑 <a href='{generer_nom_fichier_php(c_obj)}'>{c_nom}</a>{mariage_info}</li>"
            
            for sub in root_child.get_child_elements():
                if sub.get_tag() == 'CHIL':
                    id_enfant = sub.get_value()
                    e_obj = trouver_individu_par_id(id_enfant, gedcom_parser)
                    if e_obj:
                        if est_individu_vivant(e_obj, annee_actuelle):
                            enfants_html += "<li>👶 Confidentiel</li>"
                        else:
                            e_nom = ' '.join(e_obj.get_name()).strip()
                            enfants_html += f"<li>👶 <a href='{generer_nom_fichier_php(e_obj)}'>{e_nom}</a></li>"

    if not conjoints_html: conjoints_html = "<li>Célibataire ou aucune union enregistrée.</li>"
    if not enfants_html: enfants_html = "<li>Aucun enfant enregistré.</li>"

    notes_section_html = """        <section class="section-fiche notes-personnelles">
            <h2>✍️ Notes & Notes Historiques</h2>
            <p><em>Aucune note ou histoire enregistrée pour le moment.</em></p>
        </section>"""

    recherche_html = """
    <div class="search-container">
        <input type="text" id="input-recherche" placeholder="🔍 Rechercher une personne..." oninput="filtrerRecherche(this.value, '../')" onkeydown="gererEntreeRecherche(event)">
        <div id="resultats-recherche" class="search-results"></div>
    </div>
    """

    filename = generer_nom_fichier_php(individu)
    filepath = os.path.join(output_dir, "individus", filename)

    html_contact_block = ""
    if config["contact"]:
        html_contact_block = '<p>📧 <a href="../contact.php">Contacter l\'auteur</a></p>'

    php_header = obtenir_php_tracking_header(config.get("mon_ip", ""), config.get("url_domaine", ""))
    html_content = php_header + f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{prenom_affichage} {nom_affichage}</title>
    <link rel="stylesheet" href="../assets/style.css?v=4">
    <style>
        .section-fiche {{ text-align: left; margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background: #fff; }}
        .parentes-list {{ padding-left: 20px; list-style-type: square; }}
    </style>
</head>
<body>

    <main class="container">
        <header>
            <h1>{prenom_affichage} {nom_affichage}</h1>
        </header>

        <div class="encadre" style="border-top: none; background: #fdfdfd; padding: 15px;">
            {recherche_html}
        </div>

        <section class="section-fiche">
            <h2>⏳ Événements de vie</h2>
            <p><strong>👶 Naissance :</strong> {birth_date} — 📍 {birth_place}</p>
            {ligne_deces_html}
        </section>
        
        <section class="section-fiche">
            <h2>👪 Parents</h2>
            <ul class="parentes-list">
                {parents_html}
            </ul>
        </section>

        <section class="section-fiche">
            <h2>💑 Unions & Conjoints</h2>
            <ul class="parentes-list">
                {conjoints_html}
            </ul>
        </section>

        <section class="section-fiche">
            <h2>👶 Enfants</h2>
            <ul class="parentes-list">
                {enfants_html}
            </ul>
        </section>

{notes_section_html}
        
        <footer style="margin-top: 50px; font-size: 0.9em; color: #666; border-top: 1px solid #eee; padding-top: 15px;">
            <p>Données rassemblées par {config['auteur']}</p>
            {html_contact_block}
            <p style="margin-top: 15px; font-size: 0.85em; color: #999;">
                Généré via l'application <a href="http://geneasite.free.fr" target="_blank">GénéaSite, du GEDCOM au site web</a><br>
                <a href="../mentions.php" style="color: #999; text-decoration: underline;">Mentions légales & Confidentialité</a>
            </p>
        </footer>
        <p style="margin-top: 20px;"><a href="../index.php">← Retour à l'accueil principal</a></p>
             
    </main>

    <script src="../assets/donnees_recherche.js"></script>
    <script src="../assets/search.js"></script>
</body>
</html>
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

def generer_page_mentions(output_dir, config):
    hebergeur_texte = "Ce site est hébergé gracieusement sur les Pages Personnelles de Free.<br>SAS Free - 8 rue de la Ville l'Évêque, 75008 Paris, France."
    if config.get("type_hebergeur") == "Non Free":
        hebergeur_texte = "Ce site est hébergé sur des serveurs privés autonomes sous la responsabilité de l'éditeur du site."

    html_body = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mentions légales & Confidentialité - {config['titre_principal']}</title>
    <style>
        body {{ font-family: '{config['police']}', Arial, sans-serif; background-color: {config['c_fond']}; color: #333; line-height: 1.6; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: {config['c_titres']}; border-bottom: 2px solid {config['c_titres']}; padding-bottom: 10px; }}
        h2 {{ color: {config['c_titres']}; margin-top: 20px; }}
        .alert {{ background-color: #fff3cd; border: 1px solid #ffeeba; color: #856404; padding: 15px; border-radius: 4px; margin-bottom: 20px; font-style: italic; }}
        footer {{ margin-top: 40px; text-align: center; font-size: 0.85em; color: #999; border-top: 1px solid #eee; padding-top: 15px; }}
        a {{ color: {config['c_liens']}; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
    
        <a href="index.php" class="retour">← Retour au site</a>
        
        <h1>Mentions Légales & Confidentialité</h1>
        
        <div class="alert">
            <strong>✏️ Note à l'attention de l'administrateur :</strong> Pensez à compléter cette page avec vos informations personnelles en modifiant directement le fichier <code>mentions.php</code>.
        </div>

        <h2>1. Éditeur du site</h2>
        <p>Ce site généalogique est édité à des fins purement personnelles et familiales par :<br>
        <strong>Nom de l'auteur :</strong> {config['auteur']}<br>
        <strong>Contact :</strong> {config['contact']}</p>

        <h2>2. Hébergement</h2>
        <p>{hebergeur_texte}</p>

        <h2>3. Vie privée & RGPD</h2>
        <p>Conformément aux directives du RGPD et de la CNIL :</p>
        <ul>
            <li>Les personnes vivantes (de moins de 100 ans) sont totalement masquées pour des raisons de confidentialité. Aucune fiche n'est créée à leur nom, et elles apparaissent uniquement sous la mention non cliquable <i>Confidentiel</i> dans les fratries.</li>
            <li>Si vous apparaissez sur ce site et souhaitez exercer votre droit de retrait ou de modification, merci de contacter l'auteur via l'adresse ci-dessus.</li>
            <li><strong>Statistiques :</strong> Les adresses IP des visiteurs collectées à des fins statistiques sont immédiatement anonymisées (le dernier octet est tronqué à 0), empêchant toute identification des personnes.</li>
        </ul>

        <footer>
            <p>Généré via l'application <a href="http://geneasite.free.fr" target="_blank">GénéaSite</a></p>
        </footer>
    </div>
</body>
</html>
"""
    php_header = obtenir_php_tracking_header(config.get("mon_ip", ""), config.get("url_domaine", ""))
    html_complet = php_header + "\n" + html_body
    with open(os.path.join(output_dir, "mentions.php"), "w", encoding="utf-8") as f:
        f.write(html_complet)

def generer_page_merci(output_dir, config):
    html_body = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Merci - {config['titre_principal']}</title>
    <link rel="stylesheet" href="assets/style.css?v=4">
</head>
<body>
    <div class="container" style="max-width: 600px; margin: 60px auto; padding: 40px 20px;">
        <h1 style="color: {config['c_titres']};">✉️ Message envoyé !</h1>
        <p style="color: #555; line-height: 1.6; margin: 20px 0; font-size: 1.1em;">
            Votre message a bien été transmitted. L'auteur de l'arbre généalogique vous répondra dans les plus brefs délais.
        </p>
        <p style="margin-top: 30px;"><a href="index.php" class="btn-action btn-dl" style="background-color: {config['c_titres']}; color: white; padding: 10px 20px;">← Retourner à l'accueil</a></p>
    </div>
</body>
</html>
"""
    php_header = obtenir_php_tracking_header(config.get("mon_ip", ""), config.get("url_domaine", ""))
    html_complet = php_header + "\n" + html_body
    with open(os.path.join(output_dir, "merci.php"), "w", encoding="utf-8") as f:
        f.write(html_complet)

def generer_page_contact(output_dir, config):
    html_body = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact - {config['titre_principal']}</title>
    <link rel="stylesheet" href="assets/style.css?v=4">
    <style>
        .form-group {{ margin-bottom: 15px; text-align: left; }}
        label {{ display: block; margin-bottom: 5px; font-weight: bold; color: #333; }}
        input[type="text"], input[type="email"], textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; font-family: inherit; font-size: 1em; }}
        textarea {{ resize: vertical; min-height: 120px; }}
        .btn-submit {{ background-color: {config['c_liens']}; color: white; border: none; padding: 12px 20px; font-size: 1em; font-weight: bold; border-radius: 4px; cursor: pointer; display: block; width: 100%; transition: background 0.2s; }}
        .btn-submit:hover {{ filter: brightness(0.9); }}
        .aide-form {{ font-size: 0.85em; color: #7f8c8d; margin-top: 15px; text-align: left; line-height: 1.4; border-top: 1px dashed #ddd; padding-top: 10px; }}
    </style>
</head>
<body>
    <div class="container" style="max-width: 600px; margin: 40px auto;">
        <a href="index.php" style="display: inline-block; margin-bottom: 15px; text-align: left;">← Retour au site</a>
        
        <h1 style="color: {config['c_titres']};">✉️ Contacter l'auteur</h1>
        <p style="color: #666; margin-bottom: 25px;">Utilisez le formulaire ci-dessous pour envoyer un message concernant les recherches de cet arbre.</p>

        <?php
        $protocol = (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? 'https' : 'http');
        $host = $_SERVER['HTTP_HOST'];
        $directory = rtrim(dirname($_SERVER['SCRIPT_NAME']), '/\\\\');
        $next_url = $protocol . '://' . $host . $directory . '/merci.php';
        ?>

        <form action="https://formsubmit.co/{config['contact']}" method="POST">
            <input type="text" name="_honey" style="display:none">
            <input type="hidden" name="_template" value="table">
            <input type="hidden" name="_next" value="<?php echo $next_url; ?>">

            <div class="form-group">
                <label for="name">Votre nom / pseudo :</label>
                <input type="text" id="name" name="nom" placeholder="Ex: Jean Dupont" required>
            </div>

            <div class="form-group">
                <label for="email">Votre adresse e-mail :</label>
                <input type="email" id="email" name="email" placeholder="Ex: jean.dupont@email.com" required>
            </div>

            <div class="form-group">
                <label for="message">Votre message :</label>
                <textarea id="message" name="message" placeholder="Votre question ou remarque généalogique..." required></textarea>
            </div>

            <button type="submit" class="btn-submit">🚀 Envoyer le message</button>
        </form>

        <div class="aide-form">
            ℹ️ <strong>Note pour le propriétaire du site :</strong> Lors du tout premier envoi de message, vous recevrez un e-mail de confirmation de la part de FormSubmit pour valider et lier définitivement votre formulaire à votre messagerie sans configuration supplémentaire.
        </div>
    </div>
</body>
</html>
"""
    php_header = obtenir_php_tracking_header(config.get("mon_ip", ""), config.get("url_domaine", ""))
    html_complet = php_header + "\n" + html_body
    with open(os.path.join(output_dir, "contact.php"), "w", encoding="utf-8") as f:
        f.write(html_complet)

def execution_generation(config):
    chemin_ged = config["ged_path"]
    output_dir = "./site_web"
    
    if os.path.exists(os.path.join(output_dir, "individus")):
        shutil.rmtree(os.path.join(output_dir, "individus"))
        
    os.makedirs(os.path.join(output_dir, "individus"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "assets"), exist_ok=True)
    
    font_declaration = ""
    police_choisie = config['police']
    
    if police_choisie == "Comic Sans MS":
        font_declaration = """@import url('https://fonts.googleapis.com/css2?family=Comic+Neue:ital,wght@0,300;0,400;0,700;1,400&display=swap');\n"""
        police_alternative = "'Comic Neue', 'Comic Sans MS', cursive, sans-serif"
    else:
        police_alternative = f"'{police_choisie}', 'Segoe UI', Arial, sans-serif"

    with open(os.path.join(output_dir, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(f"""{font_declaration}
        :root {{ 
            --primary-color: {config['c_titres']}; 
            --bg-color: {config['c_fond']}; 
            --accent-color: {config['c_liens']}; 
            --text-color: #333; 
        }}
        * {{ box-sizing: border-box; }}
        body {{ font-family: {police_alternative} !important; background: var(--bg-color); color: var(--text-color); margin: 0; padding: 20px; }}
        .container {{ max-width: 950px; margin: 20px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center; }}
        h1, h2, h3, h4 {{ color: var(--primary-color); font-family: {police_alternative} !important; }}
        .intro-text {{ font-size: 1.1em; color: #555; line-height: 1.6; max-width: 700px; margin: 20px auto; white-space: pre-line; }}
        .encadre {{ border-top: 4px solid var(--accent-color); background-color: #f9fdfa; padding: 20px; max-width: 850px; margin: 25px auto; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }}
        .alphabet {{ font-size: 1.1em; word-spacing: 3px; margin: 15px 0; line-height: 2; }}
        .alphabet a {{ font-weight: bold; margin: 0 4px; padding: 3px 6px; background: #eee; border-radius: 3px; color: #444; text-decoration: none; }}
        .alphabet a:hover {{ background: var(--accent-color); color: white; }}
        ul {{ list-style-type: none; padding: 0; text-align: left; max-width: 600px; margin: 0 auto; }}
        li {{ padding: 10px; border-bottom: 1px solid #eee; }}
        a {{ color: var(--accent-color); text-decoration: none; font-weight: 500; }}
        a:hover {{ text-decoration: underline; }}
        
        .search-container {{ position: relative; max-width: 500px; margin: 10px auto 20px auto; text-align: left; }}
        #input-recherche {{ width: 100%; padding: 12px 15px; border: 2px solid #ddd; border-radius: 25px; font-size: 16px; box-sizing: border-box; outline: none; transition: border-color 0.2s; font-family: inherit; }}
        #input-recherche:focus {{ border-color: var(--accent-color); }}
        .search-results {{ position: absolute; top: 100%; left: 0; right: 0; background: white; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px; max-height: 350px; overflow-y: auto; z-index: 1000; box-shadow: 0 4px 10px rgba(0,0,0,0.1); display: none; }}
        .search-item {{ padding: 10px 15px; border-bottom: 1px solid #eee; cursor: pointer; display: block; color: #333; text-decoration: none; }}
        .search-item:hover {{ background: #f4f6f9; color: var(--accent-color); }}
        
        .table-stats {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 0.85em; text-align: left; }}
        .table-stats th, .table-stats td {{ padding: 8px 10px; border: 1px solid #ddd; }}
        .table-stats th {{ background-color: #f2f2f2; color: var(--primary-color); position: sticky; top: 0; z-index: 10; }}
        .table-stats tr:nth-child(even) {{ background-color: #f9f9f9; }}
        
        .scroll-stats-box {{ max-height: 450px; overflow-y: auto; border: 1px solid #ccc; border-radius: 4px; margin-top: 10px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1); }}
        .btn-action {{ display: inline-block; padding: 8px 14px; margin-right: 10px; font-size: 0.9em; font-weight: bold; border-radius: 4px; cursor: pointer; text-decoration: none; border: none; }}
        .btn-dl {{ background-color: #3498db; color: white; }}
        .btn-dl:hover {{ background-color: #2980b9; text-decoration: none; }}
        .btn-del {{ background-color: #e74c3c; color: white; }}
        .btn-del:hover {{ background-color: #c0392b; text-decoration: none; }}
        """)

    with open(os.path.join(output_dir, "assets", "search.js"), "w", encoding="utf-8") as f:
        f.write("""
        function filtrerRecherche(valeur, prefixeRelatif) {
            const divResultats = document.getElementById('resultats-recherche');
            divResultats.innerHTML = '';
            if (!valeur.trim()) { divResultats.style.display = 'none'; return; }
            
            const requete = valeur.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
            
            const correspondances = baseDonneesRecherche.filter(function(ind) {
                const nomNormalise = ind.nom.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                return nomNormalise.includes(requete);
            });
            
            if (correspondances.length > 0) {
                divResultats.style.display = 'block';
                correspondances.forEach(function(ind) {
                    const lien = document.createElement('a');
                    lien.href = prefixeRelatif + ind.lien;
                    lien.className = 'search-item';
                    lien.textContent = ind.nom;
                    divResultats.appendChild(lien);
                });
            } else {
                divResultats.style.display = 'block';
                const aucun = document.createElement('div');
                aucun.className = 'search-item';
                aucun.style.color = '#888';
                aucun.textContent = 'Aucun résultat trouvé';
                divResultats.appendChild(aucun);
            }
        }

        function gererEntreeRecherche(event) {
            if (event.key === 'Enter') {
                const divResultats = document.getElementById('resultats-recherche');
                if (divResultats && divResultats.style.display === 'block') {
                    const premierLien = divResultats.querySelector('.search-item');
                    if (premierLien && premierLien.href) {
                        window.location.href = premierLien.href;
                    }
                }
            }
        }

        document.addEventListener('click', function(e) {
            if (!e.target.closest('.search-container')) {
                const res = document.getElementById('resultats-recherche');
                if(res) res.style.display = 'none';
            }
        });
        """)

    gedcom_parser = charger_gedcom(chemin_ged)
    child_elements = gedcom_parser.get_root_element().get_child_elements()
    
    dictionnaire_lettres = {}
    liste_recherche = []
    total_individus = 0
    annee_actuelle = datetime.now().year
    
    for element in child_elements:
        if isinstance(element, IndividualElement):
            est_vivant = est_individu_vivant(element, annee_actuelle)
            
            if est_vivant:
                continue
                
            generer_page_individu(element, gedcom_parser, output_dir, config)
            total_individus += 1
            
            nom = "".join(element.get_name()[1]).strip()
            prenom = "".join(element.get_name()[0]).strip()
            filename = f"individus/{generer_nom_fichier_php(element)}"
            
            nom_complet = f"{nom} {prenom}"
            texte_brut = f"{nom} {prenom}".lower()
                
            nom_tri = "".join(c for c in unicodedata.normalize("NFD", texte_brut) if unicodedata.category(c) != 'Mn')
                
            liste_recherche.append({"nom": nom_complet, "lien": filename, "tri": nom_tri})
            
            premiere_lettre = nom[0].upper() if nom else "?"
            if not premiere_lettre.isalpha(): premiere_lettre = "?"
                
            if premiere_lettre not in dictionnaire_lettres:
                dictionnaire_lettres[premiere_lettre] = []
            dictionnaire_lettres[premiere_lettre].append({"nom_complet": nom_complet, "lien": filename, "tri": nom_tri})

    liste_recherche.sort(key=lambda x: x["tri"])
    
    with open(os.path.join(output_dir, "assets", "donnees_recherche.js"), "w", encoding="utf-8") as f:
        liste_recherche_epuree = [{"nom": x["nom"], "lien": x["lien"]} for x in liste_recherche]
        f.write(f"const baseDonneesRecherche = {json.dumps(liste_recherche_epuree, ensure_ascii=False)};")

    lettres_disponibles = sorted(list(dictionnaire_lettres.keys()))
    barre_alphabet_index = " / ".join([f'<a href="patronymes-{l}.php">{l}</a>' for l in lettres_disponibles])

    recherche_racine_html = """
    <div class="search-container">
        <input type="text" id="input-recherche" placeholder="🔍 Rechercher une personne..." oninput="filtrerRecherche(this.value, '')" onkeydown="gererEntreeRecherche(event)">
        <div id="resultats-recherche" class="search-results"></div>
    </div>
    """

    php_header = obtenir_php_tracking_header(config.get("mon_ip", ""), config.get("url_domaine", ""))

    for lettre, individus in dictionnaire_lettres.items():
        individus.sort(key=lambda x: x["tri"])
        liens_individus_html = "".join([f'            <li><a href="{ind["lien"]}">{ind["nom_complet"]}</a></li>\n' for ind in individus])
            
        html_lettre = php_header + f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index - Lettre {lettre}</title>
    <link rel="stylesheet" href="assets/style.css?v=4">
</head>
<body>
    <main class="container">
        <h1>Index des personnes - Lettre {lettre}</h1>
        <div class="alphabet">{barre_alphabet_index}</div>
        
        <div class="encadre" style="border-top: none; background: #fdfdfd; padding: 15px; margin: 20px auto;">
            {recherche_racine_html}
        </div>

        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <ul>
{liens_individus_html}
        </ul>
        <footer style="margin-top: 50px; font-size: 0.9em; color: #666; border-top: 1px solid #eee; padding-top: 15px;">
            <p style="margin-top: 5px; font-size: 0.85em; color: #999;">
                Généré via l'application <a href="http://geneasite.free.fr" target="_blank">GénéaSite, du GEDCOM au site web</a><br>
                <a href="mentions.php" style="color: #999; text-decoration: underline;">Mentions légales & Confidentialité</a>
            </p>
        </footer>
        <p style="margin-top:30px;"><a href="index.php">← Retour à l'accueil</a></p>
   </main>
    <script src="assets/donnees_recherche.js"></script>
    <script src="assets/search.js"></script>
</body>
</html>
"""
        with open(os.path.join(output_dir, f"patronymes-{lettre}.php"), "w", encoding="utf-8") as f:
            f.write(html_lettre)

    html_page_stats = f"""<?php
if (!isset($_SESSION)) {{ session_start(); }}
define('STATS_PASSWORD', '{config.get("stats_password", "admin123")}');

if (isset($_GET['action']) && $_GET['action'] == 'logout') {{
    unset($_SESSION['stats_logged_in']);
    header('Location: stats.php');
    exit;
}}

if (isset($_POST['password'])) {{
    if ($_POST['password'] === STATS_PASSWORD) {{
        $_SESSION['stats_logged_in'] = true;
    }} else {{
        $erreur = 'Mot de passe incorrect !';
    }}
}}

if (!isset($_SESSION['stats_logged_in']) || $_SESSION['stats_logged_in'] !== true) {{
    ?><!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zone Protégée</title>
    <link rel="stylesheet" href="assets/style.css?v=4">
</head>
<body>
    <main class="container" style="max-width: 500px; margin: 60px auto;">
        <h2>🔒 Zone Protégée</h2>
        <p>L'accès aux statistiques de visites est restreint.</p>
        <?php if (isset($erreur)): ?>
            <div style="background: #f8d7da; color: #721c24; padding: 10px; border-radius: 6px; margin-bottom:15px; font-weight:bold;">
                <?php echo $erreur; ?>
            </div>
        <?php endif; ?>
        <form method="post" action="stats.php">
            <input type="password" name="password" placeholder="Entrez le mot de passe" required 
                   style="width: 80%; padding: 12px; font-size: 1.05em; border: 2px solid #ddd; border-radius: 6px; text-align: center; margin-bottom: 20px;">
            <br>
            <button type="submit" class="btn-action btn-dl" style="border:none; padding: 10px 20px; font-size:1em;">Valider et Ouvrir</button>
        </form>
        <p style="margin-top:20px;"><a href="index.php">← Retour à l'accueil</a></p>
    </main>
</body>
</html><?php
    exit;
}}

$fichier_stats = rtrim($_SERVER['DOCUMENT_ROOT'], '/') . '/stats.json';

if (isset($_GET['action']) && $_GET['action'] == 'download') {{
    if (file_exists($fichier_stats)) {{
        header('Content-Type: application/json');
        header('Content-Disposition: attachment; filename="stats.json"');
        readfile($fichier_stats);
        exit;
    }}
}}

if (isset($_POST['action']) && $_POST['action'] == 'clear') {{
    file_put_contents($fichier_stats, json_encode([]));
    header('Location: stats.php?msg=deleted');
    exit;
}}

if (file_exists($fichier_stats)) {{
    $donnees_brutes = file_get_contents($fichier_stats);
    $visites = json_decode($donnees_brutes, true);
}} else {{
    $visites = [];
}}
if (!is_array($visites)) {{ $visites = []; }}

$visites_inverses = array_reverse($visites);
$dernieres_50_visites = array_slice($visites_inverses, 0, 50);

$stats_par_mois = [];
foreach ($visites_inverses as $v) {{
    $m = isset($v['mois']) ? $v['mois'] : substr($v['date'], 0, 7);
    if (!isset($stats_par_mois[$m])) {{
        $stats_par_mois[$m] = array("total" => 0, "utilisateurs" => 0, "robots" => 0);
    }}
    $stats_par_mois[$m]['total']++;
    if (isset($v['robot']) && $v['robot'] === "Robot/Scan") {{
        $stats_par_mois[$m]['robots']++;
    }} else {{
        $stats_par_mois[$m]['utilisateurs']++;
    }}
}}
?><!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Administration - Statistiques privées</title>
    <link rel="stylesheet" href="assets/style.css?v=4">
</head>
<body>
    <main class="container" style="text-align: left;">
        <h2>📊 Tableau de bord privé des statistiques</h2>
        
        <div style="margin-bottom: 20px;">
            <a href="index.php" style="margin-right:20px;">← Retourner à l'accueil</a>
            <a href="stats.php?action=download" class="btn-action btn-dl">💾 Télécharger stats.json</a>
            <a href="stats.php?action=logout" class="btn-action btn-del" style="background-color: #7f8c8d;">🔒 Déconnexion</a>
            
            <form action="stats.php" method="post" style="display: inline;" onsubmit="return confirm('⚠️ Êtes-vous sûr de vouloir supprimer définitivement tout l\'historique des statistiques ?');">
                <input type="hidden" name="action" value="clear">
                <button type="submit" class="btn-action btn-del">🗑️ Effacer les statistiques</button>
            </form>
        </div>

        <?php if (isset($_GET['msg']) && $_GET['msg'] == 'deleted'): ?>
            <div style="background-color: #d4edda; color: #155724; padding: 10px; border-radius: 4px; margin-bottom: 20px;">
                ✨ Le fichier de statistiques a été vidé avec succès.
            </div>
        <?php endif; ?>
        
        <div class="encadre" style="margin: 20px 0; max-width: 100%;">
            <h4>📅 50 dernières visites enregistrées (Affichage défilant)</h4>
            
            <div class="scroll-stats-box">
                <table class="table-stats" style="margin-top:0;">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Page visitée</th>
                            <th>Adresse IP anonymisée</th>
                            <th>Provenance</th>
                            <th>Type</th>
                            <th>Système</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php if (empty($dernieres_50_visites)): ?>
                            <tr><td colspan="6" style="text-align:center; color:#888; padding: 20px;">Aucun enregistrement disponible dans le fichier.</td></tr>
                        <?php else: ?>
                            <?php foreach ($dernieres_50_visites as $visite): ?>
                                <tr>
                                    <td><strong><?php echo htmlspecialchars($visite['date']); ?></strong></td>
                                    <td><code><?php echo htmlspecialchars($visite['page']); ?></code></td>
                                    <td>
                                        <a href="https://ipapi.co/<?php echo urlencode($visite['ip']); ?>/" target="_blank" rel="noopener noreferrer" style="color: var(--accent-color); text-decoration: underline; font-weight: bold;">
                                            <?php echo htmlspecialchars($visite['ip']); ?> 🔗
                                        </a>
                                    </td>
                                    <td style="font-size:0.9em; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="<?php echo htmlspecialchars($visite['referer']); ?>"><?php echo htmlspecialchars($visite['referer']); ?></td>
                                    <td><span style="color: <?php echo (isset($visite['robot']) && $visite['robot'] === 'Robot/Scan') ? '#c0392b':'#27ae60'; ?>; font-weight:bold;"><?php echo htmlspecialchars(isset($visite['robot']) ? $visite['robot'] : 'Utilisateur'); ?></span></td>
                                    <td><?php echo htmlspecialchars(isset($visite['os']) ? $visite['os'] : 'Inconnu'); ?></td>
                                </tr>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="encadre" style="margin: 20px 0; max-width: 500px;">
            <h4>📈 Historique global par mois</h4>
            <table class="table-stats">
                <thead>
                    <tr>
                        <th>Mois</th>
                        <th>Visites globales</th>
                        <th>Humains</th>
                        <th>Robots / Scans</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($stats_par_mois)): ?>
                        <tr><td colspan="4" style="text-align:center; color:#888;">Aucun historique mensuel.</td></tr>
                    <?php else: ?>
                        <?php ksort($stats_par_mois); foreach ($stats_par_mois as $le_mois => $valeurs): ?>
                            <tr>
                                <td><strong><?php echo htmlspecialchars($le_mois); ?></strong></td>
                                <td><?php echo $valeurs['total']; ?></td>
                                <td style="color:#27ae60; font-weight:bold;"><?php echo $valeurs['utilisateurs']; ?></td>
                                <td style="color:#c0392b;"><?php echo $valeurs['robots']; ?></td>
                            </tr>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </main>
</body>
</html>
"""
    with open(os.path.join(output_dir, "stats.php"), "w", encoding="utf-8") as f:
        f.write(html_page_stats)

    html_contact_block = ""
    if config["contact"]:
        html_contact_block = '<p>📧 <a href="contact.php">Contacter l\'auteur</a></p>'

    html_accueil = php_header + f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accueil - Généalogie</title>
    <link rel="stylesheet" href="assets/style.css?v=4">
</head>
<body>

    <main class="container">
        <header>
            <h1 style="font-size: 2.5em; margin-bottom: 5px;">{config['titre_principal']}</h1>
            <div class="intro-text">{config['introduction']}</div>
        </header>
        
        <div class="encadre">
            <h3 style="margin-top:0;">👤 Statistiques Arbre</h3>
            <p>Ce site rassemble des données sur <strong>{total_individus}</strong> personnes.</p>
            
            <hr style="border:0; border-top: 1px dashed #ddd; margin: 15px 0;">
            {recherche_racine_html}
            <hr style="border:0; border-top: 1px dashed #ddd; margin: 15px 0;">

            <h4 style="margin-bottom: 5px;">Parcourir par nom de famille</h4>
            <div class="alphabet">
                {barre_alphabet_index}
            </div>
        </div>

        <footer style="margin-top: 50px; font-size: 0.9em; color: #666; border-top: 1px solid #eee; padding-top: 15px;">
            <p>Données rassemblées par {config['auteur']}</p>
            {html_contact_block}
            <p style="margin-top: 15px; font-size: 0.85em; color: #999; line-height: 1.5;">
                Généré via l'application <a href="http://geneasite.free.fr" target="_blank">GénéaSite, du GEDCOM au site web</a><br>
                <a href="mentions.php" style="color: #999; text-decoration: underline;">Mentions légales & Confidentialité</a>
            </p>
        </footer>
        
    </main>

    <script src="assets/donnees_recherche.js"></script>
    <script src="assets/search.js"></script>
</body>
</html>
"""
    with open(os.path.join(output_dir, "index.php"), "w", encoding="utf-8") as f:
        f.write(html_accueil)
        
    generer_page_mentions(output_dir, config)
    generer_page_contact(output_dir, config)
    generer_page_merci(output_dir, config)
    
    # Adaptations spécifiques du .htaccess si hébergeur Free
    code_htaccess = ""
    if config.get("type_hebergeur") == "Free":
        code_htaccess = """# 1. Activation de PHP 5.6 sur les serveurs Pages Perso de Free.fr
<IfDefine Free>
php56 1 
</IfDefine>

# 2. Empêche la navigation par index (Sécurisation des répertoires /individus et /assets)
Options -Indexes

# 3. Redirection 404 personnalisée vers notre fichier PHP d'erreur
ErrorDocument 404 /404.php
"""
    else:
        code_htaccess = """# Empêche la navigation par index
Options -Indexes

# Redirection 404 personnalisée
ErrorDocument 404 /404.php
"""

    with open(os.path.join(output_dir, ".htaccess"), "w", encoding="utf-8", newline="\n") as f:
        f.write(code_htaccess)

    html_404 = php_header + f"""<?php
    $root_path = rtrim(dirname($_SERVER['SCRIPT_NAME']), '/\\\\');
    if ($root_path === '/' || $root_path === '\\\\') {{
        $root_path = '';
    }}
    ?><!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page introuvable - 404</title>
    <link rel="stylesheet" href="<?php echo $root_path; ?>/assets/style.css?v=4">
</head>
<body>
    <main class="container" style="max-width: 600px; margin: 60px auto; padding: 40px 20px;">
        <h1 style="font-size: 4em; margin: 0; color: #e74c3c;">🕵️‍♂️ 404</h1>
        <h2 style="margin-top: 10px;">Page introuvable ou inexistante</h2>
        <p style="color: #666; line-height: 1.6; margin: 20px 0;">
            L'ancêtre ou le fichier que vous recherchez n'existe pas ou l'adresse du site a changé. 
            Nous vous invitons à utiliser la barre de recherche ci-dessous pour le retrouver.
        </p>
        
        <div class="encadre" style="border-top-color: #e74c3c; background: #fffaf9; padding: 15px; text-align: left;">
            <div class="search-container">
                <input type="text" id="input-recherche" placeholder="🔍 Rechercher une personne..." oninput="filtrerRecherche(this.value, '<?php echo $root_path; ?>/')" onkeydown="gererEntreeRecherche(event)">
                <div id="resultats-recherche" class="search-results"></div>
            </div>
        </div>
        
        <p style="margin-top: 30px;"><a href="<?php echo $root_path; ?>/index.php" class="btn-action btn-dl" style="background-color: {config['c_titres']}; color: white; padding: 10px 20px;">← Retourner à l'accueil principal</a></p>
    </main>
    <script src="<?php echo $root_path; ?>/assets/donnees_recherche.js"></script>
    <script src="<?php echo $root_path; ?>/assets/search.js"></script>
</body>
</html>
"""
    with open(os.path.join(output_dir, "404.php"), "w", encoding="utf-8") as f:
        f.write(html_404)
            
    messagebox.showinfo("Succès", f"✨ Le site en PHP a été généré avec succès.")

class ApplicationConfiguration:
    def __init__(self, root):
        self.root = root
        self.root.title("GénéaSite - Configuration Web (Free & Multi-Hébergeurs)")
        self.root.geometry("720x980")
        self.root.configure(padx=15, pady=15)

        self.color_fond = "#f4f6f9"
        self.color_titres = "#2c3e50"
        self.color_liens = "#27ae60"

        frame_aide_generale = tk.Frame(root, bg="#ebf5fb", bd=1, relief="solid", padx=10, pady=8)
        frame_aide_generale.pack(fill="x", pady=(0, 10))
        
        lbl_aide_titre = tk.Label(frame_aide_generale, text="💡 GUIDE DE MISE EN FORME (Pour le Titre et l'Introduction) :", 
                                  font=("Arial", 11, "bold"), fg="#1b4f72", bg="#ebf5fb")
        lbl_aide_titre.pack(anchor="w", pady=(0, 4))
        
        texte_explications = (
            "Vous pouvez embellir vos textes en ajoutant directement des balises HTML :\n"
            "• <b>Mon texte</b> : pour mettre en gras.\n"
            "• <i>Mon texte</i> : pour mettre en italique.\n"
            "• <center>Mon texte</center> : pour centrer les mots ou lignes.\n"
            "• <span style='color:red;'>Mon texte</span> : pour changer la couleur."
        )
        lbl_aide_corps = tk.Label(frame_aide_generale, text=texte_explications, 
                                  font=("Arial", 10, "bold"), fg="#212f3d", bg="#ebf5fb", justify="left")
        lbl_aide_corps.pack(anchor="w")

        # ---------------- SÉLECTION HÉBERGEUR & DOMAINE ----------------
        frame_hebergeur = tk.LabelFrame(root, text=" 🌐 Hébergement & Configuration Domaine ", font=("Arial", 10, "bold"), fg="#2c3e50", padx=10, pady=8)
        frame_hebergeur.pack(fill="x", pady=(0, 10))

        tk.Label(frame_hebergeur, text="Votre hébergeur web :", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", pady=2)
        self.var_hebergeur = tk.StringVar(value="Free")
        self.menu_hebergeur = tk.OptionMenu(frame_hebergeur, self.var_hebergeur, "Free", "Non Free (Autre hébergeur)", command=self.adapter_champ_domaine)
        self.menu_hebergeur.grid(row=0, column=1, sticky="w", padx=10, pady=2)

        self.lbl_domaine = tk.Label(frame_hebergeur, text="Identifiant Free (ex: nom1.nom2) :", font=("Arial", 9, "bold"))
        self.lbl_domaine.grid(row=1, column=0, sticky="w", pady=2)
        
        self.entry_domaine = tk.Entry(frame_hebergeur, width=40)
        self.entry_domaine.insert(0, "ma-genealogie")
        self.entry_domaine.grid(row=1, column=1, sticky="w", padx=10, pady=2)

        self.lbl_aide_free = tk.Label(frame_hebergeur, text="💡 Chez Free, un login 'nom1.nom2' devient 'nom1-nom2.pages-perso.free.fr' en HTTPS.", font=("Arial", 8, "italic"), fg="#7f8c8d")
        self.lbl_aide_free.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 0))

        # ---------------- DONNÉES DU SITE ----------------
        tk.Label(root, text="Fichier GEDCOM (.ged) :", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,2))
        frame_file = tk.Frame(root)
        frame_file.pack(fill="x", pady=(0, 10))
        self.entry_ged = tk.Entry(frame_file, width=50)
        self.entry_ged.pack(side="left", fill="x", expand=True, padx=(0,5))
        tk.Button(frame_file, text="Parcourir...", command=self.parcourir_ged).pack(side="right")

        tk.Label(root, text="Titre principal du site (Accepte les balises HTML) :", font=("Arial", 10, "bold")).pack(anchor="w")
        self.entry_titre = tk.Entry(root, width=70)
        self.entry_titre.insert(0, "Ma généalogie")
        self.entry_titre.pack(fill="x", pady=(0, 10))

        tk.Label(root, text="Nom de l'auteur / Famille :", font=("Arial", 10, "bold")).pack(anchor="w")
        self.entry_auteur = tk.Entry(root, width=70)
        self.entry_auteur.insert(0, "Auteur")
        self.entry_auteur.pack(fill="x", pady=(0, 10))

        tk.Label(root, text="Adresse Email de contact (Optionnel) :", font=("Arial", 10, "bold")).pack(anchor="w")
        self.entry_contact = tk.Entry(root, width=70)
        self.entry_contact.insert(0, "Mon adresse mail")
        self.entry_contact.pack(fill="x", pady=(0, 10))

        tk.Label(root, text="Mot de passe d'accès aux Statistiques (stats.php) :", font=("Arial", 10, "bold")).pack(anchor="w")
        self.entry_stats_pass = tk.Entry(root, width=70, show="*")
        self.entry_stats_pass.insert(0, "admin123")
        self.entry_stats_pass.pack(fill="x", pady=(0, 10))

        tk.Label(root, text="Votre adresse IP à exclure du tracking (Optionnel) :", font=("Arial", 10, "bold")).pack(anchor="w")
        self.entry_ip = tk.Entry(root, width=70)
        self.entry_ip.insert(0, "mon IP")
        self.entry_ip.pack(fill="x", pady=(0, 10))

        tk.Label(root, text="Police de caractères générale du site :", font=("Arial", 10, "bold")).pack(anchor="w")
        self.var_police = tk.StringVar(value="Segoe UI")
        polices = ["Segoe UI", "Arial", "Arial Narrow", "Calibri", "Cambria", "Comic Sans MS", "Garamond", "Georgia", "Times New Roman", "Verdana"]
        self.menu_police = tk.OptionMenu(root, self.var_police, *polices)
        self.menu_police.pack(anchor="w", pady=(0, 10))

        tk.Label(root, text="Design & Couleurs :", font=("Arial", 10, "bold")).pack(anchor="w")
        frame_colors = tk.Frame(root)
        frame_colors.pack(fill="x", pady=(0, 10))
        self.btn_fond = tk.Button(frame_colors, text="Couleur Fond", bg=self.color_fond, command=lambda: self.choisir_couleur('fond'))
        self.btn_fond.pack(side="left", padx=5)
        self.btn_titres = tk.Button(frame_colors, text="Couleur Titres", fg="white", bg=self.color_titres, command=lambda: self.choisir_couleur('titres'))
        self.btn_titres.pack(side="left", padx=5)
        self.btn_liens = tk.Button(frame_colors, text="Couleur Liens/Accents", fg="white", bg=self.color_liens, command=lambda: self.choisir_couleur('liens'))
        self.btn_liens.pack(side="left", padx=5)

        tk.Label(root, text="Texte d'introduction sur la page d'accueil (Accepte les balises HTML) :", font=("Arial", 10, "bold")).pack(anchor="w")
        self.txt_intro = scrolledtext.ScrolledText(root, width=70, height=5, wrap=tk.WORD)
        texte_par_defaut = (
            "Ce site a été mis en ligne pour vous présenter mes recherches généalogiques,\n\n"
            "avec toutes les personnes qui peuvent constituer notre famille.\n\n"
            "N'hésitez pas à naviguer à travers ces pages ou à utiliser la <b style='color:#27ae60;'>barre de recherche</b>. Bonne découverte."
        )
        self.txt_intro.insert(tk.END, texte_par_defaut)
        self.txt_intro.pack(fill="both", expand=True, pady=(0, 10))

        tk.Button(root, text="🚀 Générer le site Internet (PHP)", font=("Arial", 12, "bold"), bg="#27ae60", fg="white", height=2, command=self.lancer_generation).pack(fill="x")

    def adapter_champ_domaine(self, choix):
        if choix == "Free":
            self.lbl_domaine.config(text="Identifiant Free (ex: nom1.nom2) :")
            self.lbl_aide_free.config(text="💡 Chez Free, un login 'nom1.nom2' devient 'nom1-nom2.pages-perso.free.fr' en HTTPS.")
        else:
            self.lbl_domaine.config(text="Nom de domaine complet :")
            self.lbl_aide_free.config(text="💡 Exemple : www.mon-site-genealogie.fr (Saisir sans http/https).")

    def parcourir_ged(self):
        filename = filedialog.askopenfilename(filetypes=[("Fichiers GEDCOM", "*.ged"), ("Tous les fichiers", "*.*")])
        if filename:
            self.entry_ged.delete(0, tk.END)
            self.entry_ged.insert(0, filename)

    def choisir_couleur(self, type_couleur):
        color = colorchooser.askcolor()[1]
        if color:
            if type_couleur == 'fond':
                self.color_fond = color
                self.btn_fond.config(bg=color)
            elif type_couleur == 'titres':
                self.color_titres = color
                self.btn_titres.config(bg=color)
            elif type_couleur == 'liens':
                self.color_liens = color
                self.btn_liens.config(bg=color)

    def calculer_url_domaine(self):
        type_h = self.var_hebergeur.get()
        saisie = self.entry_domaine.get().strip()
        
        if not saisie:
            return ""

        if type_h == "Free":
            # Nettoyage et conversion automatique du login Free
            saisie_propre = saisie.lower().replace("http://", "").replace("https://", "").replace(".pages-perso.free.fr", "").strip()
            login_nettoye = saisie_propre.replace(".", "-")
            return f"{login_nettoye}.pages-perso.free.fr"
        else:
            return saisie.replace("http://", "").replace("https://", "").rstrip("/")

    def lancer_generation(self):
        if not self.entry_ged.get().strip():
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier GEDCOM valide.")
            return

        ip_saisie = self.entry_ip.get().strip()
        if ip_saisie == "mon IP":
            ip_saisie = ""

        config = {
            "ged_path": self.entry_ged.get().strip(),
            "titre_principal": self.entry_titre.get().strip() or "Ma généalogie",
            "auteur": self.entry_auteur.get().strip() or "Auteur",
            "contact": self.entry_contact.get().strip(),
            "stats_password": self.entry_stats_pass.get().strip() or "admin123",
            "mon_ip": ip_saisie,
            "police": self.var_police.get(),
            "c_fond": self.color_fond,
            "c_titres": self.color_titres,
            "c_liens": self.color_liens,
            "introduction": self.txt_intro.get("1.0", tk.END).strip(),
            "type_hebergeur": self.var_hebergeur.get(),
            "url_domaine": self.calculer_url_domaine()
        }
        try:
            execution_generation(config)
            self.root.destroy()
            os._exit(0)
        except Exception as e:
            messagebox.showerror("Erreur lors de la génération", f"Une erreur est survenue :\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ApplicationConfiguration(root)
    root.mainloop()
