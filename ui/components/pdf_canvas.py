"""
Composant Canvas pour l'affichage et l'interaction avec le PDF
"""

import tkinter as tk
from tkinter import ttk
import fitz

from services.text_editing_service import TextEditingService


class PDFCanvas:
    def __init__(self, parent, content_tab):
        self.parent = parent
        self.content_tab = content_tab

        # Variables d'interaction
        self.selection_start = None
        self.selection_start_pdf = None
        self.current_selection_rect = None
        self.text_block_rects = []
        self.persistent_selection_rect = None

        self.text_editing_service = None

        self.create_canvas()
        self.bind_events()

    def initialize_text_editing_service(self):
        """Initialise le service d'édition de texte"""
        if self.content_tab.pdf_manager.pdf_document:

            self.text_editing_service = TextEditingService(self.content_tab.pdf_manager)

    def create_canvas(self):
        """Crée le canvas avec scrollbars"""
        canvas_frame = ttk.Frame(self.parent)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg="white", cursor="crosshair")

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            canvas_frame, orient="vertical", command=self.canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            canvas_frame, orient="horizontal", command=self.canvas.xview
        )

        self.canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Placement des éléments
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

    def bind_events(self):
        """Lie les événements de souris"""
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

    def on_click(self, event):
        """Gestion du clic"""
        if not self.content_tab.pdf_manager.pdf_document:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        pdf_x, pdf_y = self.content_tab.coordinate_converter.canvas_to_pdf(
            canvas_x, canvas_y
        )

        mode = self.content_tab.mode_var.get()

        if mode == "text":
            # Mode ajout de texte
            self.content_tab.tool_panels.set_text_position(pdf_x, pdf_y)
        elif mode in ["select", "highlight"]:
            # Modes sélection et surlignage
            self.selection_start = (canvas_x, canvas_y)
            self.selection_start_pdf = (pdf_x, pdf_y)

    def on_drag(self, event):
        """Gestion du glissement"""
        if not self.content_tab.pdf_manager.pdf_document or not self.selection_start:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Effacer le rectangle précédent
        if self.current_selection_rect:
            self.canvas.delete(self.current_selection_rect)

        # Dessiner le nouveau rectangle
        self.current_selection_rect = self.canvas.create_rectangle(
            self.selection_start[0],
            self.selection_start[1],
            canvas_x,
            canvas_y,
            outline="red",
            width=2,
            fill="",
            stipple="gray25",
        )

    def on_release(self, event):
        """Gestion du relâchement"""
        if not self.content_tab.pdf_manager.pdf_document or not self.selection_start:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        pdf_x, pdf_y = self.content_tab.coordinate_converter.canvas_to_pdf(
            canvas_x, canvas_y
        )

        mode = self.content_tab.mode_var.get()

        # Effacer le rectangle de sélection temporaire
        if self.current_selection_rect:
            self.canvas.delete(self.current_selection_rect)
            self.current_selection_rect = None

        if mode == "select":
            self.select_text_in_area(
                self.selection_start_pdf[0], self.selection_start_pdf[1], pdf_x, pdf_y
            )
        elif mode == "highlight":
            self.highlight_area(
                self.selection_start_pdf[0], self.selection_start_pdf[1], pdf_x, pdf_y
            )

        self.selection_start = None

    def on_motion(self, event):
        """Gestion du mouvement de souris"""
        if not self.content_tab.pdf_manager.pdf_document:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Changer le curseur si on survole du texte
        if self.is_over_text(canvas_x, canvas_y):
            if self.content_tab.mode_var.get() == "select":
                self.canvas.config(cursor="xterm")
        else:
            # Restaurer le curseur par défaut SANS effacer la sélection
            mode = self.content_tab.mode_var.get()
            cursor_map = {"select": "crosshair", "text": "xterm", "highlight": "hand2"}
            self.canvas.config(cursor=cursor_map.get(mode, "crosshair"))

    def on_double_click(self, event):
        """Gestion du double-clic pour sélectionner un mot"""
        if not self.content_tab.pdf_manager.pdf_document:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        pdf_x, pdf_y = self.content_tab.coordinate_converter.canvas_to_pdf(
            canvas_x, canvas_y
        )

        self.select_word_at_position(pdf_x, pdf_y)

    def select_text_in_area(self, x1, y1, x2, y2):
        """Sélectionne le texte dans une zone"""
        page = self.content_tab.pdf_manager.get_page()
        if not page:
            return

        rect = fitz.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        current_page = self.content_tab.pdf_manager.current_page

        # Vérifier si la zone est masquée
        if self.text_editing_service and self.text_editing_service.is_text_hidden(
            current_page, rect
        ):
            self.content_tab.current_selection = None
            self.content_tab.current_selection_rect = None
            self.content_tab.tool_panels.clear_selection_info()
            self.clear_persistent_selection()
            return

        selected_text = page.get_textbox(rect)

        if selected_text.strip():
            # Stocker la sélection dans content_tab
            self.content_tab.current_selection = {
                "text": selected_text,
                "rect": rect,
                "page": self.content_tab.pdf_manager.current_page,
            }
            # Stocker aussi le rectangle de sélection
            self.content_tab.current_selection_rect = rect

            self.content_tab.tool_panels.update_selection_info(selected_text)
            self.create_persistent_selection(rect)
        else:
            # Effacer la sélection si aucun texte trouvé
            self.content_tab.current_selection = None
            self.content_tab.current_selection_rect = None
            self.content_tab.tool_panels.clear_selection_info()
            self.clear_persistent_selection()

    def select_word_at_position(self, x, y):
        """Sélectionne le mot à la position donnée"""
        page = self.content_tab.pdf_manager.get_page()
        if not page:
            return

        current_page = self.content_tab.pdf_manager.current_page

        # Utiliser les mots filtrés si le service d'édition est disponible
        if self.text_editing_service:
            words = self.text_editing_service.get_filtered_words(current_page)
        else:
            words = page.get_text("words")

        point_rect = fitz.Rect(x - 5, y - 5, x + 5, y + 5)

        for word in words:
            word_rect = fitz.Rect(word[:4])
            if word_rect.intersects(point_rect):
                # Stocker la sélection dans content_tab
                self.content_tab.current_selection = {
                    "text": word[4],
                    "rect": word_rect,
                    "page": current_page,
                }
                # Stocker aussi le rectangle de sélection
                self.content_tab.current_selection_rect = word_rect

                self.content_tab.tool_panels.update_selection_info(word[4])
                self.create_persistent_selection(word_rect)
                return

        # Si aucun mot trouvé, effacer la sélection
        self.content_tab.current_selection = None
        self.content_tab.current_selection_rect = None
        self.content_tab.tool_panels.clear_selection_info()
        self.clear_persistent_selection()

    def create_persistent_selection(self, rect):
        """Crée une sélection persistante"""
        # Effacer l'ancienne sélection persistante
        self.clear_persistent_selection()

        canvas_coords = [
                self.content_tab.coordinate_converter.pdf_to_canvas(rect.x0, rect.y0),
                self.content_tab.coordinate_converter.pdf_to_canvas(rect.x1, rect.y1),
        ]

        self.persistent_selection_rect = self.canvas.create_rectangle(
                canvas_coords[0][0],
                canvas_coords[0][1],
                canvas_coords[1][0],
                canvas_coords[1][1],
                outline="blue",
                width=2,
                fill="lightblue",
                stipple="gray12",
                tags="persistent_selection"
        )

    def clear_persistent_selection(self):
        """Efface la sélection persistante"""
        if self.persistent_selection_rect:
            self.canvas.delete(self.persistent_selection_rect)
            self.persistent_selection_rect = None

    def highlight_selection(self, rect):
        """Met en surbrillance une sélection"""
        canvas_coords = [
            self.content_tab.coordinate_converter.pdf_to_canvas(rect.x0, rect.y0),
            self.content_tab.coordinate_converter.pdf_to_canvas(rect.x1, rect.y1),
        ]

        if self.current_selection_rect:
            self.canvas.delete(self.current_selection_rect)

        self.current_selection_rect = self.canvas.create_rectangle(
            canvas_coords[0][0],
            canvas_coords[0][1],
            canvas_coords[1][0],
            canvas_coords[1][1],
            outline="red",
            width=2,
            fill="",
            stipple="gray25",
        )

    def highlight_area(self, x1, y1, x2, y2):
        """Applique un surlignage dans une zone"""
        from services.annotation_service import AnnotationService

        try:
            annotation_service = AnnotationService(self.content_tab.pdf_manager)
            color = self.content_tab.tool_panels.get_highlight_color()

            rect = fitz.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            annotation_service.add_highlight(rect, color)

            self.content_tab.display_current_page()

        except Exception as e:
            from tkinter import messagebox

            messagebox.showerror("Erreur", f"Erreur lors du surlignage: {str(e)}")

    def is_over_text(self, canvas_x, canvas_y):
        """Vérifie si on survole du texte (en excluant les zones masquées)"""
        pdf_x, pdf_y = self.content_tab.coordinate_converter.canvas_to_pdf(
            canvas_x, canvas_y
        )

        current_page = self.content_tab.pdf_manager.current_page

        # Vérifier si le point est dans une zone masquée
        if self.text_editing_service:
            point = fitz.Point(pdf_x, pdf_y)
            if self.text_editing_service.is_text_hidden(current_page, point):
                return False

            # Utiliser les blocs filtrés
            text_blocks = self.text_editing_service.get_filtered_text_blocks(current_page)
        else:
            text_blocks = self.content_tab.text_blocks

        for block in text_blocks:
            if "lines" in block:
                bbox = block["bbox"]
                if bbox[0] <= pdf_x <= bbox[2] and bbox[1] <= pdf_y <= bbox[3]:
                    return True
        return False

    def toggle_text_blocks(self, text_blocks, zoom_level):
        """Affiche/masque les zones de texte"""
        # Effacer les rectangles existants
        for rect_id in self.text_block_rects:
            self.canvas.delete(rect_id)
        self.text_block_rects.clear()

        # Afficher les nouveaux blocs
        for block in text_blocks:
            if "lines" in block:
                bbox = block["bbox"]
                canvas_coords = [
                    self.content_tab.coordinate_converter.pdf_to_canvas(
                        bbox[0], bbox[1]
                    ),
                    self.content_tab.coordinate_converter.pdf_to_canvas(
                        bbox[2], bbox[3]
                    ),
                ]

                rect_id = self.canvas.create_rectangle(
                    canvas_coords[0][0],
                    canvas_coords[0][1],
                    canvas_coords[1][0],
                    canvas_coords[1][1],
                    outline="blue",
                    width=1,
                    fill="",
                )
                self.text_block_rects.append(rect_id)

    def set_cursor(self, cursor):
        """Change le curseur du canvas"""
        self.canvas.config(cursor=cursor)

    def clear_selections(self):
        """Efface toutes les sélections"""
        if self.current_selection_rect:
            self.canvas.delete(self.current_selection_rect)
            self.current_selection_rect = None

        # Effacer la sélection persistante
        self.clear_persistent_selection()

        # Effacer aussi les rectangles de zones de texte si affichés
        for rect_id in self.text_block_rects:
            self.canvas.delete(rect_id)
        self.text_block_rects.clear()

        # Réinitialiser les variables de sélection
        self.selection_start = None
        self.selection_start_pdf = None

    def clear(self):
        """Efface tout le contenu du canvas"""
        self.canvas.delete("all")
        self.text_block_rects.clear()
        self.current_selection_rect = None

    def display_image(self, image):
        """Affiche une image dans le canvas"""
        # Sauvegarder la sélection actuelle
        current_selection = self.content_tab.current_selection
        current_selection_rect = self.content_tab.current_selection_rect

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=image)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Restaurer la sélection si elle existait
        if current_selection and current_selection_rect:
            self.create_persistent_selection(current_selection_rect)
