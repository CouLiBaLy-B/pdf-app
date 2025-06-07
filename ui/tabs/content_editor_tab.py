"""
Onglet pour l'édition de contenu PDF
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import fitz
import io

from config.settings import DEFAULT_ZOOM, MIN_ZOOM, MAX_ZOOM, ZOOM_STEP
from core.coordinate_utils import CoordinateConverter
from ui.components.pdf_canvas import PDFCanvas
from ui.components.tool_panels import ToolPanels


class ContentEditorTab:
    def __init__(self, notebook, pdf_manager):
        self.notebook = notebook
        self.pdf_manager = pdf_manager

        # Variables d'état
        self.zoom_level = DEFAULT_ZOOM
        self.coordinate_converter = CoordinateConverter(self.zoom_level)
        self.current_selection = None
        self.current_selection_rect = None
        self.text_blocks = []

        # Variables d'interface
        self.page_var = tk.StringVar(value="0")
        self.zoom_var = tk.StringVar(value="100%")
        self.mode_var = tk.StringVar(value="select")

        self.create_tab()

    def create_tab(self):
        """Crée l'onglet éditeur de contenu"""
        self.content_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.content_frame, text="Éditeur de Contenu")

        # Barre de navigation
        self.create_navigation_bar()

        # Frame principal avec deux panneaux
        main_content_frame = ttk.Frame(self.content_frame)
        main_content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Panneau gauche - Canvas PDF
        self.create_pdf_viewer(main_content_frame)

        # Panneau droit - Outils
        self.create_tool_panels(main_content_frame)

    def create_navigation_bar(self):
        """Crée la barre de navigation"""
        nav_frame = ttk.Frame(self.content_frame)
        nav_frame.pack(fill="x", padx=5, pady=5)

        # Navigation des pages
        ttk.Button(nav_frame, text="◀◀", command=self.first_page).pack(
            side="left", padx=2
        )
        ttk.Button(nav_frame, text="◀", command=self.prev_page).pack(
            side="left", padx=2
        )

        page_entry = ttk.Entry(nav_frame, textvariable=self.page_var, width=5)
        page_entry.pack(side="left", padx=5)
        page_entry.bind("<Return>", self.goto_page)

        self.total_pages_label = ttk.Label(nav_frame, text="/ 0")
        self.total_pages_label.pack(side="left", padx=2)

        ttk.Button(nav_frame, text="▶", command=self.next_page).pack(
            side="left", padx=2
        )
        ttk.Button(nav_frame, text="▶▶", command=self.last_page).pack(
            side="left", padx=2
        )

        # Contrôles de zoom
        ttk.Separator(nav_frame, orient="vertical").pack(side="left", padx=10, fill="y")
        ttk.Label(nav_frame, text="Zoom:").pack(side="left", padx=5)
        ttk.Button(nav_frame, text="-", command=self.zoom_out).pack(side="left", padx=2)
        ttk.Label(nav_frame, textvariable=self.zoom_var).pack(side="left", padx=5)
        ttk.Button(nav_frame, text="+", command=self.zoom_in).pack(side="left", padx=2)

        # Modes d'interaction
        ttk.Separator(nav_frame, orient="vertical").pack(side="left", padx=10, fill="y")
        self.create_mode_selection(nav_frame)

    def create_mode_selection(self, parent):
        """Crée les boutons de sélection de mode"""
        ttk.Label(parent, text="Mode:").pack(side="left", padx=5)

        mode_frame = ttk.Frame(parent)
        mode_frame.pack(side="left", padx=5)

        ttk.Radiobutton(
            mode_frame,
            text="Sélection",
            variable=self.mode_var,
            value="select",
            command=self.change_mode,
        ).pack(side="left", padx=2)
        ttk.Radiobutton(
            mode_frame,
            text="Texte",
            variable=self.mode_var,
            value="text",
            command=self.change_mode,
        ).pack(side="left", padx=2)
        ttk.Radiobutton(
            mode_frame,
            text="Surlignage",
            variable=self.mode_var,
            value="highlight",
            command=self.change_mode,
        ).pack(side="left", padx=2)

        ttk.Button(
            parent, text="Afficher zones texte", command=self.toggle_text_blocks
        ).pack(side="left", padx=10)

    def create_pdf_viewer(self, parent):
        """Crée le visualiseur PDF"""
        left_frame = ttk.LabelFrame(parent, text="Aperçu PDF Interactif")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.pdf_canvas = PDFCanvas(left_frame, self)

    def create_tool_panels(self, parent):
        """Crée les panneaux d'outils"""
        right_frame = ttk.LabelFrame(parent, text="Outils d'édition", width=350)
        right_frame.pack(side="right", fill="y")
        right_frame.pack_propagate(False)

        self.tool_panels = ToolPanels(right_frame, self)

    # Méthodes de navigation
    def first_page(self):
        if self.pdf_manager.pdf_document and self.pdf_manager.current_page > 0:
            self.pdf_manager.current_page = 0
            self.display_current_page()

    def prev_page(self):
        if self.pdf_manager.pdf_document and self.pdf_manager.current_page > 0:
            self.pdf_manager.current_page -= 1
            self.display_current_page()

    def next_page(self):
        if (
            self.pdf_manager.pdf_document
            and self.pdf_manager.current_page < self.pdf_manager.total_pages - 1
        ):
            self.pdf_manager.current_page += 1
            self.display_current_page()

    def last_page(self):
        if (
            self.pdf_manager.pdf_document
            and self.pdf_manager.current_page < self.pdf_manager.total_pages - 1
        ):
            self.pdf_manager.current_page = self.pdf_manager.total_pages - 1
            self.display_current_page()

    def goto_page(self, event=None):
        try:
            page_num = int(self.page_var.get()) - 1
            if 0 <= page_num < self.pdf_manager.total_pages:
                self.pdf_manager.current_page = page_num
                self.display_current_page()
            else:
                self.page_var.set(str(self.pdf_manager.current_page + 1))
                messagebox.showwarning(
                    "Attention",
                    f"Page invalide. Utilisez 1-{self.pdf_manager.total_pages}",
                )
        except ValueError:
            self.page_var.set(str(self.pdf_manager.current_page + 1))
            messagebox.showerror("Erreur", "Numéro de page invalide")

    # Méthodes de zoom
    def zoom_in(self):
        if self.zoom_level < MAX_ZOOM:
            self.zoom_level += ZOOM_STEP
            self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
            self.coordinate_converter.set_zoom(self.zoom_level)
            self.display_current_page()

    def zoom_out(self):
        if self.zoom_level > MIN_ZOOM:
            self.zoom_level -= ZOOM_STEP
            self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
            self.coordinate_converter.set_zoom(self.zoom_level)
            self.display_current_page()

    def on_canvas_click_outside_selection(self):
        """Appelé quand on clique en dehors d'une sélection"""
        # Vous pouvez choisir de garder ou effacer la sélection
        # Pour l'instant, on la garde jusqu'à ce qu'une nouvelle sélection soit faite
        pass

    def change_mode(self):
        """Change le mode d'interaction"""
        mode = self.mode_var.get()
        cursor_map = {"select": "crosshair", "text": "xterm", "highlight": "hand2"}
        self.pdf_canvas.set_cursor(cursor_map.get(mode, "crosshair"))
        # Ne pas effacer les sélections lors du changement de mode
        # self.clear_selections()  # Commenté pour garder la sélection

    def display_current_page(self):
        """Affiche la page courante"""
        if not self.pdf_manager.pdf_document:
            return

        try:
            page = self.pdf_manager.get_page()
            if not page:
                return

            # Créer l'image avec zoom
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=mat)

            # Convertir en image PIL puis Tkinter
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            self.current_image = ImageTk.PhotoImage(img)

            # Afficher dans le canvas
            self.pdf_canvas.display_image(self.current_image)

            # Mettre à jour les informations
            self.page_var.set(str(self.pdf_manager.current_page + 1))
            self.load_text_blocks()

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage: {str(e)}")

    def undo_last_edit(self):
        """Annule la dernière modification sur la page courante"""
        if not self.pdf_manager.pdf_document:
            return False

        current_page = self.pdf_manager.current_page

        if (
            hasattr(self.pdf_canvas, "text_editing_service")
            and self.pdf_canvas.text_editing_service
        ):
            # Effacer les modifications de la page courante
            self.pdf_canvas.text_editing_service.clear_page_edits(current_page)

            # Recharger la page depuis le document original
            page = self.pdf_manager.get_page()
            if page:
                # Supprimer toutes les annotations ajoutées
                annots = list(page.annots())
                for annot in annots:
                    page.delete_annot(annot)

            # Rafraîchir l'affichage
            self.display_current_page()
            return True

        return False

    def load_text_blocks(self):
        """Charge les blocs de texte de la page courante (filtrés)"""
        if not self.pdf_manager.pdf_document:
            return

        current_page = self.pdf_manager.current_page

        # Utiliser les blocs filtrés si le service d'édition est disponible
        if (
            hasattr(self.pdf_canvas, "text_editing_service")
            and self.pdf_canvas.text_editing_service
        ):
            self.text_blocks = (
                self.pdf_canvas.text_editing_service.get_filtered_text_blocks(current_page)
            )
        else:
            page = self.pdf_manager.get_page()
            if page:
                self.text_blocks = page.get_text("dict")["blocks"]

    def toggle_text_blocks(self):
        """Affiche/masque les zones de texte"""
        if not self.pdf_manager.pdf_document:
            return

        self.pdf_canvas.toggle_text_blocks(self.text_blocks, self.zoom_level)

    def clear_selections(self):
        """Efface toutes les sélections"""
        self.pdf_canvas.clear_selections()
        self.current_selection = None
        self.current_selection_rect = None
        # Effacer aussi les informations dans les panneaux d'outils
        if hasattr(self, 'tool_panels'):
            self.tool_panels.clear_selection_info()

    def delete_selected_text(self):
        """Supprime le texte sélectionné"""
        if not self.has_selection():
            from tkinter import messagebox

            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return False

        try:
            selection = self.current_selection
            page_num = selection["page"]
            rect = selection["rect"]

            # Masquer la zone de texte
            self.pdf_canvas.text_editing_service.hide_text_area(page_num, rect)

            # Effacer la sélection
            self.clear_selections()

            # Rafraîchir l'affichage
            self.display_current_page()

            return True

        except Exception as e:
            from tkinter import messagebox

            messagebox.showerror("Erreur", f"Erreur lors de la suppression: {str(e)}")
            return False

    def replace_selected_text(self, new_text):
        """Remplace le texte sélectionné"""
        if not self.has_selection():
            from tkinter import messagebox

            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return False

        try:
            selection = self.current_selection
            page_num = selection["page"]
            rect = selection["rect"]

            # Vérifier si le service d'édition est disponible
            if (
                hasattr(self.pdf_canvas, "text_editing_service")
                and self.pdf_canvas.text_editing_service
            ):
                # Remplacer le texte avec préservation du formatage
                self.pdf_canvas.text_editing_service.replace_text_area(
                    page_num, rect, new_text
                )
            else:
                # Fallback : remplacement simple
                self._simple_text_replacement(page_num, rect, new_text)

            # Effacer la sélection
            self.clear_selections()

            # Rafraîchir l'affichage
            self.display_current_page()

            return True

        except Exception as e:
            from tkinter import messagebox

            messagebox.showerror("Erreur", f"Erreur lors du remplacement: {str(e)}")
            return False

    def get_current_selection(self):
        """Retourne la sélection courante"""
        return self.current_selection

    def has_selection(self):
        """Vérifie s'il y a une sélection active"""
        return self.current_selection is not None and self.current_selection.get('text', '').strip() != ''

    def save_edits(self):
        """Sauvegarde les modifications dans le PDF"""
        if not self.pdf_manager.pdf_document:
            return False

        try:
            from tkinter import filedialog, messagebox

            # Demander où sauvegarder
            file_path = filedialog.asksaveasfilename(
                title="Sauvegarder le PDF modifié",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            )

            if file_path:
                # Sauvegarder le document avec les modifications
                self.pdf_manager.pdf_document.save(file_path, garbage=4, deflate=True)
                messagebox.showinfo("Succès", f"PDF sauvegardé : {file_path}")
                return True

        except Exception as e:
            from tkinter import messagebox

            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

        return False

    def apply_text_changes(self, new_text):
        """Applique les changements de texte à la sélection courante"""
        if not self.has_selection():
            from tkinter import messagebox
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return False

        try:
            # Ici vous pouvez ajouter la logique pour appliquer les changements
            # Par exemple, utiliser un service d'édition de texte
            selection = self.current_selection
            print(f"Modification du texte: '{selection['text']}' -> '{new_text}'")
            print(f"Position: {selection['rect']}")
            print(f"Page: {selection['page']}")

            # Après modification, rafraîchir l'affichage
            self.display_current_page()
            return True

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erreur", f"Erreur lors de la modification: {str(e)}")
            return False

    def on_pdf_loaded(self):
        """Appelé quand un nouveau PDF est chargé"""
        if self.pdf_manager.pdf_document:
            self.total_pages_label.config(text=f"/ {self.pdf_manager.total_pages}")
            # Initialiser le service d'édition de texte
            self.pdf_canvas.initialize_text_editing_service()
            self.display_current_page()
        else:
            self.total_pages_label.config(text="/ 0")
            self.pdf_canvas.clear()

    def reset(self):
        """Réinitialise l'onglet"""
        self.zoom_level = DEFAULT_ZOOM
        self.zoom_var.set("100%")
        self.coordinate_converter.set_zoom(self.zoom_level)
        self.page_var.set("0")
        self.total_pages_label.config(text="/ 0")
        self.mode_var.set("select")
        self.clear_selections()
        self.pdf_canvas.clear()

        # Réinitialiser le service d'édition
        if hasattr(self.pdf_canvas, "text_editing_service"):
            self.pdf_canvas.text_editing_service = None

        if hasattr(self, "tool_panels"):
            self.tool_panels.reset()

    def estimate_text_dimensions(self, text):
        """Estime les dimensions du texte avec le formatage actuel"""
        if not self.has_selection():
            return None, None

        formatting = self.get_formatting_info()
        if formatting and hasattr(self.pdf_canvas, "text_editing_service"):
            return self.pdf_canvas.text_editing_service.calculate_text_dimensions(
                text, formatting
            )

        # Estimation simple par défaut
        return len(text) * 7, 14

    def _simple_text_replacement(self, page_num, rect, new_text):
        """Remplacement simple sans préservation du formatage (fallback)"""
        page = self.pdf_manager.pdf_document[page_num]

        # Masquer l'ancien texte
        white_rect = page.add_rect_annot(rect)
        white_rect.set_colors(stroke=[1, 1, 1], fill=[1, 1, 1])
        white_rect.set_border(width=0)
        white_rect.update()

        # Ajouter le nouveau texte
        text_point = fitz.Point(rect.x0 + 2, rect.y0 + 12)
        page.insert_text(text_point, new_text, fontsize=12, color=[0, 0, 0])

    def get_formatting_info(self):
        """Retourne les informations de formatage de la sélection courante"""
        if not self.has_selection():
            return None

        if (
            hasattr(self.pdf_canvas, "text_editing_service")
            and self.pdf_canvas.text_editing_service
        ):
            selection = self.current_selection
            return self.pdf_canvas.text_editing_service.analyze_text_formatting(
                selection["page"], selection["rect"]
            )

        return None
