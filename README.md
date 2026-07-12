# geneasite
# 🧬 GénéaSite

GénéaSite est un script Python qui permet de générer automatiquement un site internet généalogique complet, dynamique et moderne en PHP, à partir d'un simple fichier d'exportation **GEDCOM (.ged)**. 

Ce système a été spécialement conçu et optimisé pour être hébergé gratuitement sur les **Pages Perso de Free**, mais il fonctionne sur n'importe quel serveur supportant le PHP.

---

🔒 Sécurité & Protection des Données (RGPD)

La confidentialité de vos données familiales est notre priorité absolue :
* **Aucun fichier GEDCOM sur le serveur :** Votre fichier `.ged` reste exclusivement sur votre ordinateur. Le script le lit localement, extrait les données, puis génère uniquement des pages PHP anonymisées. Le fichier source n'est jamais transféré sur internet.
* **Protection des personnes vivantes :** Le script détecte automatiquement les personnes de moins de 100 ans sans date de décès. Leurs fiches sont automatiquement verrouillées, affichant la mention `[CONFIDENTIEL]` pour la date/lieu de naissance et masquant leur nom de famille.
* **Anonymisation des Visiteurs (RGPD) :** Le compteur de visites intégré masque le dernier octet des adresses IP des visiteurs (ex: `192.168.1.0`), garantissant une totale conformité avec les règles de la CNIL et du RGPD.

---

⚙️ Fonctionnalités & Options

L'application intègre une interface graphique complète permettant de personnaliser votre site avant la génération :
* **Choix du design :** Configuration personnalisée de la couleur du fond, de la couleur des titres et de la couleur des liens.
* **Gestion des polices :** Support complet des polices universelles (Arial, Verdana, etc.) et intégration automatique et sécurisée de la police moderne *Comic Neue* (via Google Fonts) pour un affichage parfait des accents français sur ordinateurs et smartphones.
* **Moteur de recherche local :** Une barre de recherche prédictive instantanée est intégrée sur l'accueil et sur chaque fiche.
* **Statistiques privées :** Un tableau de bord administrateur sécurisé (`stats.php`) permet de suivre le nombre de visites mensuelles, de distinguer les humains des robots de recherche, et de télécharger ou vider l'historique.
* **Lien de partage :** Un discret lien de crédit est inclus dans le pied de page de votre site (`Généré via l'application GénéaSite`), renvoyant vers le site officiel du projet pour permettre à d'autres passionnés de découvrir et d'utiliser ce script gratuit.

---

🚀 Procédure d'Utilisation

1. Prérequis
Vous devez disposer de Python 3 installé sur votre machine et de la bibliothèque de lecture GEDCOM. Pour l'installer, ouvrez un terminal et tapez :

pip install python-gedcom


2. Lancement du script

    Lancez le script depuis votre terminal ou console :

    python3 generate_site.py


3. Configuration et Génération

    Cliquez sur Parcourir... pour sélectionner votre fichier .ged.

    Remplissez le titre de votre site, votre nom d'auteur et votre adresse e-mail de contact (qui sera automatiquement protégée contre le spam par inversion de chaîne dans le code).

    Personnalisez votre texte d'introduction (les balises HTML comme <b>, <i>, <center> sont acceptées).

    Choisissez vos couleurs et votre police, puis cliquez sur 🚀 Générer le site Internet (PHP).


4. Mise en ligne

Le script crée instantanément un dossier nommé site_web.
Pour le mettre en ligne, connectez-vous à votre espace Free via un logiciel FTP (comme FileZilla) et transférez l'intégralité du contenu de ce dossier site_web à la racine de vos pages perso.

Généré avec passion par JanusEye — Code mis à disposition librement.
