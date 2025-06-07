"""
Panneaux d'outils pour l'édition de contenu
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from config.settings import TEXT_COLORS, HIGHLIGHT_COLORS, DEFAULT_FONT_SIZE


class ToolPanels:
    def __init__(self, parent, content_tab):
        self.parent = parent
        self.content_tab = content_tab

        # Variables d'interface
        self.setup_variables()

        # Créer le notebook pour les outils
        self.tools_notebook = ttk.Notebook(parent)
        self.tools_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.create_all_tabs()

    def setup_variables(self):
        """Initialise les variables d'interface"""
        self.new_text_var = tk.StringVar()
        self.text_x_var = tk.StringVar(value="100")
        self.text_y_var = tk.StringVar(value="100")
        self.font_size_var = tk.StringVar(value=str(DEFAULT_FONT_SIZE))
        self.text_color_var = tk.StringVar(value="black")
        self.highlight_color_var = tk.StringVar(value="yellow")
        self.selected_font_size = tk.StringVar(value=str(DEFAULT_FONT_SIZE))
        self.selected_text_color = tk.StringVar(value="black")

    def create_all_tabs(self):
        """Crée tous les onglets d'outils"""
        self.create_text_tools_tab()
        self.create_selection_tools_tab()
        self.create_annotation_tools_tab()
        self.create_extraction_tab()

    def create_text_tools_tab(self):
        """Onglet d'ajout de texte"""
        text_frame = ttk.Frame(self.tools_notebook)
        self.tools_notebook.add(text_frame, text="Ajout Texte")

        # Ajout de texte
        ttk.Label(
            text_frame, text="Ajouter du texte:", font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=5)

        ttk.Label(text_frame, text="Texte à ajouter:").pack(anchor="w")
        ttk.Entry(text_frame, textvariable=self.new_text_var, width=30).pack(
            fill="x", pady=2
        )

        # Position
        pos_frame = ttk.Frame(text_frame)
        pos_frame.pack(fill="x", pady=5)

        ttk.Label(pos_frame, text="Position - X:").pack(side="left")
        ttk.Entry(pos_frame, textvariable=self.text_x_var, width=8).pack(
            side="left", padx=2
        )

        ttk.Label(pos_frame, text="Y:").pack(side="left", padx=(10, 0))
        ttk.Entry(pos_frame, textvariable=self.text_y_var, width=8).pack(
            side="left", padx=2
        )

        # Formatage
        font_frame = ttk.Frame(text_frame)
        font_frame.pack(fill="x", pady=5)

        ttk.Label(font_frame, text="Taille:").pack(side="left")
        ttk.Entry(font_frame, textvariable=self.font_size_var, width=8).pack(
            side="left", padx=2
        )

        ttk.Label(font_frame, text="Couleur:").pack(side="left", padx=(10, 0))
        ttk.Combobox(
            font_frame, textvariable=self.text_color_var, values=TEXT_COLORS, width=10
        ).pack(side="left", padx=2)

        ttk.Button(text_frame, text="Ajouter Texte", command=self.add_text).pack(
            pady=10
        )

        # Instructions
        self.add_instructions(text_frame)

    def create_selection_tools_tab(self):
        """Onglet d'outils de sélection"""
        selection_frame = ttk.Frame(self.tools_notebook)
        self.tools_notebook.add(selection_frame, text="Sélection")

        # Informations sur la sélection
        ttk.Label(
            selection_frame, text="Sélection courante:", font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=5)

        self.selection_info = tk.Text(
            selection_frame, height=4, width=40, state="disabled"
        )
        self.selection_info.pack(fill="x", pady=5)

        # Actions sur la sélection
        ttk.Label(selection_frame, text="Actions:", font=("Arial", 10, "bold")).pack(
            anchor="w", pady=(10, 5)
        )

        action_frame = ttk.Frame(selection_frame)
        action_frame.pack(fill="x", pady=5)

        ttk.Button(
            action_frame, text="Supprimer", command=self.delete_selected_text
        ).pack(side="left", padx=2)
        ttk.Button(action_frame, text="Copier", command=self.copy_selected_text).pack(
            side="left", padx=2
        )
        ttk.Button(
            action_frame, text="Remplacer", command=self.replace_selected_text
        ).pack(side="left", padx=2)

        # Zone de remplacement
        ttk.Label(selection_frame, text="Texte de remplacement:").pack(
            anchor="w", pady=(10, 0)
        )
        self.replacement_text = tk.Text(selection_frame, height=3, width=40)
        self.replacement_text.pack(fill="x", pady=2)

        # Formatage
        ttk.Separator(selection_frame, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(selection_frame, text="Formatage:", font=("Arial", 10, "bold")).pack(
            anchor="w"
        )

        format_frame = ttk.Frame(selection_frame)
        format_frame.pack(fill="x", pady=5)

        ttk.Label(format_frame, text="Taille:").pack(side="left")
        ttk.Entry(format_frame, textvariable=self.selected_font_size, width=8).pack(
            side="left", padx=2
        )

        ttk.Label(format_frame, text="Couleur:").pack(side="left", padx=(10, 0))
        ttk.Combobox(
            format_frame,
            textvariable=self.selected_text_color,
            values=TEXT_COLORS,
            width=10,
        ).pack(side="left", padx=2)

        ttk.Button(
            selection_frame, text="Appliquer formatage", command=self.apply_formatting
        ).pack(pady=10)

    def create_annotation_tools_tab(self):
        """Onglet d'outils d'annotation"""
        annotation_frame = ttk.Frame(self.tools_notebook)
        self.tools_notebook.add(annotation_frame, text="Annotations")

        # Surlignage
        ttk.Label(
            annotation_frame, text="Surlignage:", font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=5)

        highlight_frame = ttk.Frame(annotation_frame)
        highlight_frame.pack(fill="x", pady=5)

        ttk.Label(highlight_frame, text="Couleur:").pack(side="left")
        ttk.Combobox(
            highlight_frame,
            textvariable=self.highlight_color_var,
            values=HIGHLIGHT_COLORS,
            width=10,
        ).pack(side="left", padx=5)

        ttk.Button(
            annotation_frame, text="Appliquer surlignage", command=self.apply_highlight
        ).pack(pady=5)

        # Notes
        ttk.Separator(annotation_frame, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(annotation_frame, text="Notes:", font=("Arial", 10, "bold")).pack(
            anchor="w"
        )

        ttk.Label(annotation_frame, text="Contenu de la note:").pack(anchor="w")
        self.note_text = tk.Text(annotation_frame, height=4, width=30)
        self.note_text.pack(fill="x", pady=2)

        ttk.Button(annotation_frame, text="Ajouter Note", command=self.add_note).pack(
            pady=5
        )

    def create_extraction_tab(self):
        """Onglet d'extraction de texte"""
        extract_frame = ttk.Frame(self.tools_notebook)
        self.tools_notebook.add(extract_frame, text="Extraction")

        ttk.Label(
            extract_frame, text="Texte extrait:", font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=5)

        self.extracted_text = scrolledtext.ScrolledText(
            extract_frame, height=15, width=35
        )
        self.extracted_text.pack(fill="both", expand=True, pady=5)

        # Boutons d'extraction
        extract_buttons = ttk.Frame(extract_frame)
        extract_buttons.pack(fill="x", pady=5)

        ttk.Button(
            extract_buttons, text="Extraire Page", command=self.extract_current_page
        ).pack(fill="x", pady=1)
        ttk.Button(
            extract_buttons, text="Tout Extraire", command=self.extract_all_text
        ).pack(fill="x", pady=1)
        ttk.Button(
            extract_buttons, text="Sauvegarder Texte", command=self.save_extracted_text
        ).pack(fill="x", pady=1)

    def add_instructions(self, parent):
        """Ajoute les instructions d'utilisation"""
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=10)
        instructions = tk.Text(parent, height=6, width=40, wrap=tk.WORD)
        instructions.pack(fill="x", pady=5)
        instructions.insert(
            "1.0",
            "Instructions:\n"
            "• Mode Sélection: Cliquez et glissez pour sélectionner du texte\n"
            "• Mode Texte: Cliquez où vous voulez ajouter du texte\n"
            "• Mode Surlignage: Cliquez et glissez pour surligner\n"
            "• Double-clic: Sélectionne un mot entier\n"
            "• 'Afficher zones texte': Montre les blocs de texte détectés",
        )
        instructions.config(state="disabled")

    # Méthodes d'interface
    def set_text_position(self, x, y):
        """Met à jour la position pour l'ajout de texte"""
        self.text_x_var.set(str(int(x)))
        self.text_y_var.set(str(int(y)))

    def update_selection_info(self, selected_text):
        """Met à jour les informations de sélection"""
        if hasattr(self, 'text_editing_panel'):
            self.text_editing_panel.update_selection_info(selected_text)

    def clear_selection_info(self):
        """Efface les informations de sélection"""
        if hasattr(self, 'text_editing_panel'):
            self.text_editing_panel.clear_selection_info()

    def get_highlight_color(self):
        """Retourne la couleur de surlignage sélectionnée"""
        return self.highlight_color_var.get()

    # Méthodes d'action
    def add_text(self):
        """Ajoute du texte au PDF"""
        from services.text_service import TextService

        text = self.new_text_var.get().strip()
        if not text:
            messagebox.showwarning("Attention", "Veuillez entrer du texte")
            return

        try:
            text_service = TextService(self.content_tab.pdf_manager)

            x = float(self.text_x_var.get())
            y = float(self.text_y_var.get())
            font_size = float(self.font_size_var.get())
            color = self.text_color_var.get()

            text_service.add_text(text, x, y, font_size, color)
            self.content_tab.display_current_page()

            messagebox.showinfo("Succès", "Texte ajouté avec succès")
            self.new_text_var.set("")

        except ValueError:
            messagebox.showerror("Erreur", "Valeurs numériques invalides")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout de texte: {str(e)}")

    def delete_selected_text(self):
        """Supprime le texte sélectionné"""
        if not self.content_tab.current_selection:
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        from services.text_service import TextService

        try:
            text_service = TextService(self.content_tab.pdf_manager)
            text_service.delete_text(self.content_tab.current_selection)

            self.content_tab.display_current_page()
            self.content_tab.clear_selections()
            self.clear_selection_info()

            messagebox.showinfo("Succès", "Texte supprimé")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression: {str(e)}")

    def copy_selected_text(self):
        """Copie le texte sélectionné"""
        if not self.content_tab.current_selection:
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        self.content_tab.content_frame.clipboard_clear()
        self.content_tab.content_frame.clipboard_append(
            self.content_tab.current_selection["text"]
        )
        messagebox.showinfo("Succès", "Texte copié dans le presse-papiers")

    def replace_selected_text(self):
        """Remplace le texte sélectionné"""
        if not self.content_tab.current_selection:
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        replacement = self.replacement_text.get("1.0", tk.END).strip()
        if not replacement:
            messagebox.showwarning(
                "Attention", "Veuillez entrer le texte de remplacement"
            )
            return

        from services.text_service import TextService

        try:
            text_service = TextService(self.content_tab.pdf_manager)
            font_size = float(self.selected_font_size.get())
            color = self.selected_text_color.get()

            text_service.replace_text(
                self.content_tab.current_selection, replacement, font_size, color
            )

            self.content_tab.display_current_page()
            self.content_tab.clear_selections()
            self.clear_selection_info()
            self.replacement_text.delete("1.0", tk.END)

            messagebox.showinfo("Succès", "Texte remplacé")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du remplacement: {str(e)}")

    def apply_formatting(self):
        """Applique le formatage au texte sélectionné"""
        if not self.content_tab.current_selection:
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        from services.text_service import TextService

        try:
            text_service = TextService(self.content_tab.pdf_manager)
            font_size = float(self.selected_font_size.get())
            color = self.selected_text_color.get()

            text_service.format_text(
                self.content_tab.current_selection, font_size, color
            )

            self.content_tab.display_current_page()
            messagebox.showinfo("Succès", "Formatage appliqué")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du formatage: {str(e)}")

    def apply_highlight(self):
        """Applique le surlignage à la sélection"""
        if not self.content_tab.current_selection:
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        from services.annotation_service import AnnotationService

        try:
            annotation_service = AnnotationService(self.content_tab.pdf_manager)
            color = self.highlight_color_var.get()

            annotation_service.add_highlight(
                self.content_tab.current_selection["rect"], color
            )

            self.content_tab.display_current_page()
            self.content_tab.clear_selections()
            self.clear_selection_info()

            messagebox.showinfo("Succès", "Surlignage appliqué")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du surlignage: {str(e)}")

    def add_note(self):
        """Ajoute une note"""
        note_content = self.note_text.get("1.0", tk.END).strip()
        if not note_content:
            messagebox.showwarning("Attention", "Veuillez entrer le contenu de la note")
            return

        from services.annotation_service import AnnotationService

        try:
            annotation_service = AnnotationService(self.content_tab.pdf_manager)
            annotation_service.add_note(note_content)

            self.content_tab.display_current_page()
            self.note_text.delete("1.0", tk.END)

            messagebox.showinfo("Succès", "Note ajoutée avec succès")

        except Exception as e:
            messagebox.showerror(
                "Erreur", f"Erreur lors de l'ajout de la note: {str(e)}"
            )

    def extract_current_page(self):
        """Extrait le texte de la page courante"""
        from services.text_service import TextService

        try:
            text_service = TextService(self.content_tab.pdf_manager)
            text = text_service.extract_page_text(
                self.content_tab.pdf_manager.current_page
            )

            self.extracted_text.delete("1.0", tk.END)
            self.extracted_text.insert("1.0", text)

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'extraction: {str(e)}")

    def extract_all_text(self):
        """Extrait le texte de tout le PDF"""
        from services.text_service import TextService

        try:
            text_service = TextService(self.content_tab.pdf_manager)
            text = text_service.extract_all_text()

            self.extracted_text.delete("1.0", tk.END)
            self.extracted_text.insert("1.0", text)

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'extraction: {str(e)}")

    def save_extracted_text(self):
        """Sauvegarde le texte extrait"""
        from services.file_service import FileService

        text_content = self.extracted_text.get("1.0", tk.END).strip()
        if not text_content:
            messagebox.showwarning("Attention", "Aucun texte à sauvegarder")
            return

        try:
            file_service = FileService()
            file_service.save_text(text_content)

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

    def reset(self):
        """Réinitialise tous les panneaux"""
        if hasattr(self, 'text_editing_panel'):
            self.text_editing_panel.reset()
