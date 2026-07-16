import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

class EditeurFicheIndividuNeophyte:
    def __init__(self, root):
        self.root = root
        self.root.title("GeneWebGen - Éditeur de Fiches (Visuel)")
        
        # Résolution optimisée pour éviter de masquer le bouton Enregistrer
        self.root.geometry("800x750")
        self.root.configure(padx=10, pady=10, bg="#f5f6fa")

        # Configuration des chemins
        self.dossier_individus = "./site_web/individus"
        self.dossier_images = "./site_web/assets/images"
        self.fichier_actuel = None
        self.contenu_html_complet = ""

        # --- STYLE GÉNÉRAL ---
        font_titre = ("Arial", 10, "bold")
        font_bouton = ("Arial", 9, "bold")

        # --- ÉTAPE 1 : RECHERCHE DE LA FICHE ---
        frame_recherche = tk.LabelFrame(root, text=" 🔍 1. Sélectionner la fiche généalogique ", font=font_titre, padx=10, pady=8, bg="white", bd=1, relief="solid")
        frame_recherche.pack(fill="x", pady=(0, 10))
        
        frame_input = tk.Frame(frame_recherche, bg="white")
        frame_input.pack(fill="x")
        
        self.entry_recherche = tk.Entry(frame_input, font=("Arial", 11), bd=2, relief="groove")
        self.entry_recherche.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=2)
        self.entry_recherche.bind("<Return>", lambda event: self.rechercher_et_charger())
        
        btn_charger = tk.Button(frame_input, text="📁 Ouvrir", font=font_bouton, bg="#2980b9", fg="white", bd=0, padx=12, command=self.rechercher_et_charger, cursor="hand2")
        btn_charger.pack(side="right", ipady=2)

        self.lbl_statut_fichier = tk.Label(frame_recherche, text="⚠️ Aucune fiche sélectionnée.", fg="#e74c3c", font=("Arial", 9, "bold"), bg="white")
        self.lbl_statut_fichier.pack(anchor="w", pady=(4, 0))

        # --- ÉTAPE 2 : ZONE D'ÉDITION ---
        self.frame_edition = tk.LabelFrame(root, text=" ✍️ 2. Rédiger l'histoire et ajouter des photos ", font=font_titre, padx=10, pady=8, bg="white", bd=1, relief="solid")
        self.frame_edition.pack(fill="both", expand=True, pady=(0, 10))

        # Barre d'outils visuels
        frame_outils = tk.Frame(self.frame_edition, bg="#eaeaea", padx=5, pady=5)
        frame_outils.pack(fill="x", pady=(0, 5))
        
        self.btn_gras = tk.Button(frame_outils, text="<b> Gras", font=("Arial", 9, "bold"), command=lambda: self.inserer_formatage("gras"), state="disabled")
        self.btn_gras.pack(side="left", padx=2)

        self.btn_centre = tk.Button(frame_outils, text="↔ Centrer", font=("Arial", 9), command=lambda: self.inserer_formatage("centre"), state="disabled")
        self.btn_centre.pack(side="left", padx=2)

        self.btn_liste = tk.Button(frame_outils, text="• Liste", font=("Arial", 9), command=lambda: self.inserer_formatage("liste"), state="disabled")
        self.btn_liste.pack(side="left", padx=2)

        self.btn_image = tk.Button(frame_outils, text="🖼️ Ajouter une Photo", font=font_bouton, bg="#d35400", fg="white", bd=0, padx=10, command=self.inserer_image, state="disabled", cursor="hand2")
        self.btn_image.pack(side="right", padx=2)

        # Zone d'édition principale
        self.txt_notes = scrolledtext.ScrolledText(self.frame_edition, wrap=tk.WORD, font=("Arial", 11), bd=1, relief="solid")
        self.txt_notes.pack(fill="both", expand=True)
        self.txt_notes.config(state="disabled")

        # --- ÉTAPE 3 : BOUTON ENREGISTRER ---
        self.btn_sauver = tk.Button(root, text="💾 ENREGISTRER LES MODIFICATIONS", font=("Arial", 11, "bold"), bg="#27ae60", fg="white", bd=0, height=2, command=self.sauvegarder_fiche, state="disabled", cursor="hand2")
        self.btn_sauver.pack(fill="x")

    def rechercher_et_charger(self):
        recherche = self.entry_recherche.get().strip().lower()
        if not recherche:
            messagebox.showwarning("Champ vide", "Veuillez inscrire un nom ou un identifiant.")
            return

        if not os.path.exists(self.dossier_individus):
            messagebox.showerror("Erreur", f"Dossier '{self.dossier_individus}' introuvable.")
            return

        fichiers = os.listdir(self.dossier_individus)
        # Modification ici : on cible les fichiers finissant par .php
        fichiers_trouves = [f for f in fichiers if recherche in f.lower() and f.endswith(".php")]

        if not fichiers_trouves:
            messagebox.showerror("Introuvable", f"Aucune fiche pour '{recherche}'.")
            return
        
        if len(fichiers_trouves) > 1:
            popup = tk.Toplevel(self.root)
            popup.title("Choix de la fiche")
            popup.geometry("400x250")
            popup.transient(self.root)
            popup.grab_set()
            
            tk.Label(popup, text="Plusieurs fiches trouvées. Double-cliquez :", font=("Arial", 10, "bold")).pack(pady=5)
            
            listbox = tk.Listbox(popup, font=("Arial", 10))
            listbox.pack(fill="both", expand=True, padx=10, pady=5)
            for f in fichiers_trouves:
                # Modification ici : remplacement de .php pour un affichage propre
                listbox.insert(tk.END, f.replace(".php", "").replace("-", " "))
                
            def on_select(event):
                if not listbox.curselection(): return
                index = listbox.curselection()[0]
                choix_real = fichiers_trouves[index]
                popup.destroy()
                self.charger_fichier_php(choix_real)
                
            listbox.bind("<Double-Button-1>", on_select)
            return

        self.charger_fichier_php(fichiers_trouves[0])

    def desactiver_interface(self):
        """Réinitialise et bloque l'accès à la zone d'édition"""
        self.txt_notes.delete("1.0", tk.END)
        self.txt_notes.config(state="disabled")
        self.btn_gras.config(state="disabled")
        self.btn_centre.config(state="disabled")
        self.btn_liste.config(state="disabled")
        self.btn_image.config(state="disabled")
        self.btn_sauver.config(state="disabled")
        self.fichier_actuel = None

    def charger_fichier_php(self, nom_fichier):
        chemin_test = os.path.join(self.dossier_individus, nom_fichier)
        
        with open(chemin_test, "r", encoding="utf-8") as f:
            contenu_test = f.read()

        # Sécurité : Bloquer si la fiche contient les marqueurs de protection de contemporains
        if "🔒 Fiche restreinte" in contenu_test or "(Masqué)" in contenu_test:
            self.desactiver_interface()
            self.lbl_statut_fichier.config(text="🔒 Accès refusé : Cette fiche concerne un contemporain protégé.", fg="#e74c3c")
            messagebox.showerror("Accès Restreint", "Sécurité : L'édition d'anecdotes et d'histoires est bloquée pour les personnes contemporaines masquées afin de respecter leur confidentialité.")
            return

        self.fichier_actuel = chemin_test
        self.contenu_html_complet = contenu_test

        pattern = r'(<section class="section-fiche notes-personnelles">.*?<h2>✍️ Notes & Notes Historiques</h2>\s*)(.*?)(</section>)'
        match = re.search(pattern, self.contenu_html_complet, re.DOTALL)

        if match:
            contenu_notes = match.group(2).strip()
            
            # Ajustement du message indicatif
            if "[Vous pouvez éditer ce fichier" in contenu_notes:
                contenu_notes = ""
            else:
                contenu_notes = re.sub(r'</p>\s*<p>', '\n\n', contenu_notes)
                contenu_notes = re.sub(r'<br\s*/?>', '\n', contenu_notes)
                contenu_notes = re.sub(r'<p>|</p>', '', contenu_notes)

            self.txt_notes.config(state="normal")
            self.btn_gras.config(state="normal")
            self.btn_centre.config(state="normal")
            self.btn_liste.config(state="normal")
            self.btn_image.config(state="normal")
            self.btn_sauver.config(state="normal")
            
            self.txt_notes.delete("1.0", tk.END)
            self.txt_notes.insert(tk.END, contenu_notes.strip())
            
            # Modification ici : remplacement de .php pour le statut vert
            self.lbl_statut_fichier.config(text=f"🟢 Fiche active : {nom_fichier.replace('.php', '').upper()}", fg="#27ae60")
        else:
            messagebox.showerror("Erreur", "Structure de la fiche incompatible.")

    def inserer_formatage(self, type_format):
        try:
            selection = self.txt_notes.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.txt_notes.delete(tk.SEL_FIRST, tk.SEL_LAST)
            if type_format == "gras":
                self.txt_notes.insert(tk.INSERT, f"<b>{selection}</b>")
            elif type_format == "centre":
                self.txt_notes.insert(tk.INSERT, f'<div style="text-align:center;">{selection}</div>')
        except tk.TclError:
            if type_format == "gras":
                self.txt_notes.insert(tk.INSERT, "<b>Texte en gras</b>")
            elif type_format == "centre":
                self.txt_notes.insert(tk.INSERT, '<div style="text-align:center;">Texte centré</div>')
            elif type_format == "liste":
                self.txt_notes.insert(tk.INSERT, "\n• Élément de liste\n")

    def inserer_image(self):
        chemin_image_source = filedialog.askopenfilename(
            title="Sélectionner la photo",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")]
        )
        if not chemin_image_source: return

        os.makedirs(self.dossier_images, exist_ok=True)
        nom_image = os.path.basename(chemin_image_source)
        chemin_destination = os.path.join(self.dossier_images, nom_image)

        try:
            shutil.copy2(chemin_image_source, chemin_destination)
        except Exception as e:
            messagebox.showerror("Erreur", f"Copie image impossible : {e}")
            return

        code_html_image = f'\n<div style="text-align:center; margin:20px 0;">\n    <img src="../assets/images/{nom_image}" alt="Photo" style="max-width:100%; max-height:420px; border-radius:6px; box-shadow: 0 4px 12px rgba(0,0,0,0.12);">\n</div>\n'
        self.txt_notes.insert(tk.INSERT, code_html_image)

    def sauvegarder_fiche(self):
        if not self.fichier_actuel: return

        texte_a_sauver = self.txt_notes.get("1.0", tk.END).strip()

        if not texte_a_sauver:
            texte_a_sauver = "<p><em>Aucune note ou histoire enregistrée pour le moment.</em></p>"
        else:
            lignes = texte_a_sauver.split("\n\n")
            blocs_finaux = []
            for bloc in lignes:
                bloc_strip = bloc.strip()
                if not bloc_strip: continue
                if bloc_strip.startswith("<div") or bloc_strip.startswith("<img") or bloc_strip.startswith("<p"):
                    blocs_finaux.append(bloc_strip)
                else:
                    blocs_finaux.append(f"<p>{bloc_strip.replace('\n', '<br>')}</p>")
            texte_a_sauver = "\n            ".join(blocs_finaux)

        pattern = r'(<section class="section-fiche notes-personnelles">.*?<h2>✍️ Notes & Notes Historiques</h2>\s*)(.*?)(</section>)'
        
        def remplacement(match):
            return f"{match.group(1)}\n            {texte_a_sauver}\n        {match.group(3)}"

        nouveau_html_total, count = re.subn(pattern, remplacement, self.contenu_html_complet, flags=re.DOTALL)

        if count > 0:
            try:
                with open(self.fichier_actuel, "w", encoding="utf-8") as f:
                    f.write(nouveau_html_total)
                self.contenu_html_complet = nouveau_html_total
                messagebox.showinfo("Succès !", "💾 Enregistrement réussi !")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur écriture :\n{e}")
        else:
            messagebox.showerror("Erreur", "Échec de l'application des modifications.")

if __name__ == "__main__":
    root = tk.Tk()
    app = EditeurFicheIndividuNeophyte(root)
    root.mainloop()
