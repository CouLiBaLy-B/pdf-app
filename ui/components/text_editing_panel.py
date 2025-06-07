"""
Panneau pour l'édition de texte avec préservation du formatage
"""

import tkinter as tk
from tkinter import ttk, messagebox


class TextEditingPanel:
    def __init__(self, parent, content_tab):
        self.parent = parent
        self.content_tab = content_tab
        self.current_formatting = None

        self.create_panel()

    def create_panel(self):
        """Crée le panneau d'édition de texte"""
        # Frame principal
        main_frame = ttk.LabelFrame(self.parent, text="Édition de Texte")
        main_frame.pack(fill="x", padx=5, pady=5)

        # Informations sur la sélection
        self.create_selection_info(main_frame)

        # Informations de formatage
        self.create_formatting_info(main_frame)

        # Outils d'édition
        self.create_editing_tools(main_frame)

        # Zone de remplacement de texte
        self.create_replacement_area(main_frame)

        # Boutons d'action
        self.create_action_buttons(main_frame)

    def create_selection_info(self, parent):
        """Crée la zone d'information sur la sélection"""
        info_frame = ttk.LabelFrame(parent, text="Sélection Actuelle")
        info_frame.pack(fill="x", padx=5, pady=5)

        # Texte sélectionné
        ttk.Label(info_frame, text="Texte:").pack(anchor="w", padx=5, pady=2)

        self.selected_text_var = tk.StringVar()
        self.selected_text_label = ttk.Label(
            info_frame,
            textvariable=self.selected_text_var,
            background="white",
            relief="sunken",
            wraplength=300,
        )
        self.selected_text_label.pack(fill="x", padx=5, pady=2)

        # Position et taille
        self.position_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.position_var).pack(
            anchor="w", padx=5, pady=2
        )

    def create_formatting_info(self, parent):
        """Crée la zone d'information sur le formatage"""
        format_frame = ttk.LabelFrame(parent, text="Formatage Détecté")
        format_frame.pack(fill="x", padx=5, pady=5)

        self.formatting_var = tk.StringVar(value="Aucune sélection")
        formatting_label = ttk.Label(
            format_frame,
            textvariable=self.formatting_var,
            wraplength=300,
            justify="left",
        )
        formatting_label.pack(anchor="w", padx=5, pady=5)

        # Aperçu du formatage
        self.preview_frame = ttk.Frame(format_frame)
        self.preview_frame.pack(fill="x", padx=5, pady=2)

        ttk.Label(self.preview_frame, text="Aperçu:").pack(anchor="w")
        self.preview_label = ttk.Label(
            self.preview_frame,
            text="Exemple de texte",
            background="white",
            relief="sunken",
            font=("Arial", 10),
        )
        self.preview_label.pack(fill="x", pady=2)

    def create_editing_tools(self, parent):
        """Crée les outils d'édition"""
        tools_frame = ttk.LabelFrame(parent, text="Outils")
        tools_frame.pack(fill="x", padx=5, pady=5)

        # Boutons d'édition rapide
        buttons_frame = ttk.Frame(tools_frame)
        buttons_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(
            buttons_frame, text="Supprimer", command=self.delete_selected_text, width=12
        ).pack(side="left", padx=2)

        ttk.Button(
            buttons_frame, text="Copier", command=self.copy_selected_text, width=12
        ).pack(side="left", padx=2)

        ttk.Button(
            buttons_frame, text="Annuler", command=self.undo_last_edit, width=12
        ).pack(side="left", padx=2)

    def create_replacement_area(self, parent):
        """Crée la zone de remplacement de texte"""
        replace_frame = ttk.LabelFrame(parent, text="Remplacer par")
        replace_frame.pack(fill="x", padx=5, pady=5)

        # Zone de texte pour le remplacement
        text_frame = ttk.Frame(replace_frame)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.replacement_text = tk.Text(
            text_frame, height=4, width=40, wrap=tk.WORD, font=("Arial", 10)
        )
        self.replacement_text.pack(side="left", fill="both", expand=True)

        # Scrollbar pour la zone de texte
        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.replacement_text.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.replacement_text.configure(yscrollcommand=scrollbar.set)

        # Options avancées
        options_frame = ttk.LabelFrame(replace_frame, text="Options")
        options_frame.pack(fill="x", padx=5, pady=2)

        # Préservation du formatage
        self.preserve_formatting_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Préserver le formatage original",
            variable=self.preserve_formatting_var,
            command=self.toggle_formatting_preservation,
        ).pack(anchor="w", padx=5, pady=2)

        # Ajustement automatique de l'espace
        self.auto_adjust_space_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Ajuster automatiquement l'espace",
            variable=self.auto_adjust_space_var,
        ).pack(anchor="w", padx=5, pady=2)

        # Aperçu en temps réel
        self.live_preview_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Aperçu en temps réel",
            variable=self.live_preview_var,
            command=self.toggle_live_preview,
        ).pack(anchor="w", padx=5, pady=2)

    def create_action_buttons(self, parent):
        """Crée les boutons d'action"""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill="x", padx=5, pady=5)

        # Bouton d'aperçu
        ttk.Button(action_frame, text="Aperçu", command=self.preview_replacement).pack(
            side="left", padx=2
        )

        ttk.Button(
            action_frame,
            text="Remplacer",
            command=self.replace_selected_text,
            style="Accent.TButton",
        ).pack(side="left", padx=2, fill="x", expand=True)

        ttk.Button(
            action_frame,
            text="Sauvegarder",
            command=self.save_document,
            style="Accent.TButton",
        ).pack(side="right", padx=2)

    def update_selection_info(self, selected_text):
        """Met à jour les informations de sélection"""
        self.selected_text_var.set(
            selected_text[:100] + "..." if len(selected_text) > 100 else selected_text
        )

        if self.content_tab.current_selection:
            rect = self.content_tab.current_selection["rect"]
            page = self.content_tab.current_selection["page"]
            self.position_var.set(
                f"""Page {page + 1}
                - Position: ({rect.x0:.1f}, {rect.y0:.1f})
                - Taille: {rect.width:.1f}×{rect.height:.1f}
                """
            )

            # Analyser et afficher le formatage
            self.analyze_and_display_formatting(page, rect)

        # Pré-remplir la zone de remplacement avec le texte sélectionné
        self.replacement_text.delete(1.0, tk.END)
        self.replacement_text.insert(1.0, selected_text)

        # Lier l'événement de modification pour l'aperçu en temps réel
        self.replacement_text.bind("<KeyRelease>", self.on_text_change)

    def analyze_and_display_formatting(self, page_num, rect):
        """Analyse et affiche les informations de formatage"""
        if (
            hasattr(self.content_tab.pdf_canvas, "text_editing_service")
            and self.content_tab.pdf_canvas.text_editing_service
        ):
            service = self.content_tab.pdf_canvas.text_editing_service

            # Obtenir les informations de formatage
            self.current_formatting = service.analyze_text_formatting(page_num, rect)

            # Afficher les informations
            format_info = service.get_text_formatting_info(page_num, rect)
            self.formatting_var.set(format_info)

            # Mettre à jour l'aperçu
            self.update_preview()
        else:
            self.formatting_var.set("Formatage non disponible")
            self.current_formatting = None

    def update_preview(self):
        """Met à jour l'aperçu du formatage"""
        if not self.current_formatting:
            return

        try:
            # Créer une police pour l'aperçu
            font_size = max(
                8, min(16, int(self.current_formatting["font_size"] * 0.8))
            )  # Adapter la taille
            font_family = "Arial"  # Police par défaut pour l'aperçu

            font_style = "normal"
            font_weight = "normal"

            if self.current_formatting["font_flags"] & 2**4:  # Bold
                font_weight = "bold"
            if self.current_formatting["font_flags"] & 2**6:  # Italic
                font_style = "italic"

            preview_font = (
                font_family,
                font_size,
                f"{font_weight} {font_style}".strip(),
            )

            # Mettre à jour le label d'aperçu
            preview_text = self.replacement_text.get(1.0, tk.END).strip()
            if not preview_text:
                preview_text = "Exemple de texte"

            self.preview_label.config(
                text=(
                    preview_text[:50] + "..."
                    if len(preview_text) > 50
                    else preview_text
                ),
                font=preview_font,
            )

        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'aperçu: {e}")

    def toggle_formatting_preservation(self):
        """Active/désactive la préservation du formatage"""
        if self.preserve_formatting_var.get():
            self.update_preview()
        else:
            # Réinitialiser l'aperçu avec une police standard
            self.preview_label.config(font=("Arial", 10))

    def toggle_live_preview(self):
        """Active/désactive l'aperçu en temps réel"""
        if self.live_preview_var.get():
            self.replacement_text.bind("<KeyRelease>", self.on_text_change)
        else:
            self.replacement_text.unbind("<KeyRelease>")

    def on_text_change(self, event=None):
        """Appelé quand le texte de remplacement change"""
        if self.live_preview_var.get() and self.preserve_formatting_var.get():
            self.update_preview()

    def preview_replacement(self):
        """Affiche un aperçu du remplacement"""
        if not self.content_tab.has_selection():
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        new_text = self.replacement_text.get(1.0, tk.END).strip()
        if not new_text:
            messagebox.showwarning(
                "Attention", "Veuillez saisir le texte de remplacement"
            )
            return

        # Calculer les dimensions estimées
        if self.current_formatting and hasattr(
            self.content_tab.pdf_canvas, "text_editing_service"
        ):
            service = self.content_tab.pdf_canvas.text_editing_service
            estimated_width, estimated_height = service.calculate_text_dimensions(
                new_text, self.current_formatting
            )

            original_rect = self.content_tab.current_selection["rect"]

            preview_info = f"""Aperçu du remplacement:

Texte original: "{self.content_tab.current_selection['text'][:50]}..."
Nouveau texte: "{new_text[:50]}..."

Dimensions originales: {original_rect.width:.1f} × {original_rect.height:.1f}
Dimensions estimées: {estimated_width:.1f} × {estimated_height:.1f}

Formatage: {self.formatting_var.get()}
"""

            messagebox.showinfo("Aperçu", preview_info)
        else:
            messagebox.showinfo("Aperçu", f"Nouveau texte: {new_text}")

    def clear_selection_info(self):
        """Efface les informations de sélection"""
        self.selected_text_var.set("Aucune sélection")
        self.position_var.set("")
        self.formatting_var.set("Aucune sélection")
        self.replacement_text.delete(1.0, tk.END)
        self.current_formatting = None
        self.preview_label.config(text="Exemple de texte", font=("Arial", 10))

    def delete_selected_text(self):
        """Supprime le texte sélectionné"""
        if not self.content_tab.has_selection():
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        # Demander confirmation
        result = messagebox.askyesno(
            "Confirmation", "Êtes-vous sûr de vouloir supprimer le texte sélectionné ?"
        )

        if result:
            success = self.content_tab.delete_selected_text()
            if success:
                self.clear_selection_info()
                messagebox.showinfo("Succès", "Texte supprimé avec succès")

    def copy_selected_text(self):
        """Copie le texte sélectionné dans le presse-papiers"""
        if not self.content_tab.has_selection():
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        selected_text = self.content_tab.current_selection["text"]
        self.content_tab.notebook.clipboard_clear()
        self.content_tab.notebook.clipboard_append(selected_text)
        messagebox.showinfo("Succès", "Texte copié dans le presse-papiers")

    def replace_selected_text(self):
        """Remplace le texte sélectionné"""
        if not self.content_tab.has_selection():
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        new_text = self.replacement_text.get(1.0, tk.END).strip()
        if not new_text:
            messagebox.showwarning(
                "Attention", "Veuillez saisir le texte de remplacement"
            )
            return

        # Vérifier si le formatage doit être préservé
        preserve_format = self.preserve_formatting_var.get()
        auto_adjust = self.auto_adjust_space_var.get()

        # Afficher un aperçu détaillé avant remplacement
        if self.current_formatting and preserve_format:
            service = self.content_tab.pdf_canvas.text_editing_service
            estimated_width, estimated_height = service.calculate_text_dimensions(
                new_text, self.current_formatting
            )
            original_rect = self.content_tab.current_selection["rect"]

            preview_msg = f"""Remplacer le texte avec les paramètres suivants:

Texte original: "{self.content_tab.current_selection['text'][:50]}..."
Nouveau texte: "{new_text[:50]}..."

Formatage préservé: {preserve_format}
Ajustement automatique: {auto_adjust}

Dimensions originales: {original_rect.width:.1f} × {original_rect.height:.1f}
Dimensions estimées: {estimated_width:.1f} × {estimated_height:.1f}

Continuer?"""
        else:
            preview_msg = f"Remplacer '{self.content_tab.current_selection['text'][:30]}...' par '{new_text[:30]}...' ?"

        # Demander confirmation
        result = messagebox.askyesno("Confirmation", preview_msg)

        if result:
            success = self.content_tab.replace_selected_text(new_text)
            if success:
                self.clear_selection_info()
                messagebox.showinfo("Succès", "Texte remplacé avec succès")

    def undo_last_edit(self):
        """Annule la dernière modification"""
        result = messagebox.askyesno(
            "Confirmation", "Annuler toutes les modifications de cette page ?"
        )

        if result:
            success = self.content_tab.undo_last_edit()
            if success:
                self.clear_selection_info()
                messagebox.showinfo("Succès", "Modifications annulées")
            else:
                messagebox.showwarning("Attention", "Aucune modification à annuler")

    def save_document(self):
        """Sauvegarde le document"""
        success = self.content_tab.save_edits()
        if not success:
            messagebox.showwarning("Attention", "Aucune modification à sauvegarder")

    def reset(self):
        """Réinitialise le panneau"""
        self.clear_selection_info()
        self.preserve_formatting_var.set(True)
        self.auto_adjust_space_var.set(True)
        self.live_preview_var.set(False)
