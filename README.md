# 🧬 GénéaSite — Du GEDCOM au site web PHP

**GénéaSite** est un script Python qui permet de générer automatiquement un site internet généalogique complet, dynamique et moderne en **PHP**, à partir d'un simple fichier d'exportation GEDCOM (`.ged`).

Ce système a été spécialement conçu et optimisé pour être hébergé facilement sur les **Pages Perso de Free**, mais il est également compatible avec n'importe quel autre serveur Web supportant le PHP.

---

## 🔒 Sécurité & Protection des Données (RGPD)

La confidentialité de vos données familiales et le respect de la vie privée sont au cœur du projet :

* **Aucun fichier GEDCOM transféré :** Votre fichier `.ged` reste exclusivement sur votre ordinateur. Le script le lit en local et génère des fichiers PHP prêts à l'emploi. Le fichier source n'est jamais envoyé sur Internet.
* **Non-création des personnes vivantes :** Le script identifie automatiquement les personnes de moins de 100 ans sans date de décès. **Aucune fiche HTML/PHP n'est créée pour elles**. Elles sont totalement absentes du site public ou apparaissent simplement sous la mention non cliquable *`Confidentiel`* au sein des fratries et parentés.
* **Redirection HTTPS & Gestion des adresses :**
  * **Hébergement Free :** Prise en charge automatique de la conversion du login (ex: `nom1.nom2` est converti automatiquement vers `nom1-nom2.pages-perso.free.fr`).
  * **Redirection sécurisée :** Le script intègre la redirection automatique vers le HTTPS si un nom de domaine est configuré.
* **Anonymisation des Visiteurs (RGPD) :** Le compteur de visites anonymise automatiquement l'adresse IP des visiteurs en tronquant le dernier octet (ex: `192.168.1.0`), garantissant une totale conformité avec les recommandations de la CNIL et du RGPD.
* **Page Mentions Légales & Formulaire de Contact :** Génération automatique d'une page `mentions.php` conforme au RGPD et d'un formulaire de contact (`contact.php`) sécurisé sans exposition en clair de votre adresse e-mail.

---

## ⚙️ Fonctionnalités & Options

L'application intègre une interface graphique Tkinter complète pour personnaliser votre site :

* **Sélection de l'hébergeur :** Choix entre **Free** (avec conversion automatique de l'URL) et **Autre hébergeur** (pour nom de domaine personnalisé ou DDNS).
* **Personnalisation visuelle :** Choix des couleurs (fond, titres, liens/accents) et support des balises HTML (`<b>`, `<i>`, `<center>`, etc.) dans les textes de présentation.
* **Gestion des polices :** Support des polices système et intégration automatique de la police moderne *Comic Neue* (via Google Fonts).
* **Moteur de recherche instantané :** Barre de recherche prédictive en JavaScript intégrée sur l'accueil, les fiches individuelles et la page d'erreur 404.
* **Statistiques de visite privées :** Espace d'administration sécurisé par mot de passe (`stats.php`) permettant de suivre les visites mensuelles, de filtrer les robots, de géolocaliser les IP anonymisées, ainsi que de télécharger ou vider le journal (`stats.json`).
* **Filtrage d'IP personnelle :** Option pour exclure votre propre adresse IP des statistiques afin de ne pas fausser le compteur lors de vos visites.

---

## 🚀 Procédure d'Utilisation

### 1. Prérequis
Vous devez disposer de Python 3 installé sur votre machine ainsi que de la bibliothèque de lecture GEDCOM. Pour l'installer, ouvrez votre terminal et tapez :

pip install python-gedcom

### 2. Lancement du script

Lancez l'interface graphique depuis votre terminal :

python generate_site.py
# ou 
python3 generate_site.py

### 3. Configuration et Génération

    Cliquez sur Parcourir... pour sélectionner votre fichier .ged.

    Choisissez le type d'hébergeur (Free ou Non Free) et saisissez votre identifiant ou nom de domaine.

    Renseignez le titre de votre site, le nom de l'auteur, votre e-mail de contact et le mot de passe souhaité pour l'accès aux statistiques.

    (Optionnel) Saisissez votre adresse IP pour ne pas la comptabiliser dans les statistiques.

    Personnalisez l'apparence (couleurs, police, texte d'introduction) puis cliquez sur 🚀 Générer le site Internet (PHP).

### 4. Mise en ligne

Le script crée un dossier nommé site_web.
Pour publier votre site :

    Connectez-vous à votre hébergeur via un client FTP (comme FileZilla).

    Transférez l'intégralité du contenu du dossier site_web à la racine de votre espace d'hébergement.

## 📄 Licence & Crédits

    Auteur : JanusEye
