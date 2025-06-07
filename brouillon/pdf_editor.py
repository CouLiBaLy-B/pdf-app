import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import PyPDF2
import fitz  # PyMuPDF pour l'édition de contenu
import os
from datetime import datetime
import tempfile
from PIL import Image, ImageTk
import io


class PDFEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Éditeur PDF Avancé - Métadonnées et Contenu")
        self.root.geometry("1400x900")

        self.current_pdf_path = None
        self.pdf_reader = None
        self.pdf_document = None  # PyMuPDF document
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0
        self.pdf_metadata = {}

        # Variables pour l'interaction
        self.selection_mode = "none"  # "text", "highlight", "draw", "none"
        self.selected_text_blocks = []
        self.text_blocks = []  # Stocke les blocs de texte de la page courante
        self.selection_start = None
        self.selection_end = None
        self.current_selection_rect = None

        # Variables pour le dessin
        self.drawing = False
        self.draw_start_x = 0
        self.draw_start_y = 0

        self.setup_ui()

    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configuration du redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Section de sélection de fichier
        ttk.Label(main_frame, text="Fichier PDF:", font=("Arial", 12, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(0, weight=1)

        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, state="readonly").grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        ttk.Button(file_frame, text="Parcourir", command=self.select_pdf).grid(
            row=0, column=1
        )

        # Notebook pour les onglets
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10
        )
        main_frame.rowconfigure(2, weight=1)

        # Onglets
        self.create_content_editor_tab()
        self.create_metadata_tab()
        self.create_manipulation_tab()
        self.create_info_tab()

        # Boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(
            button_frame,
            text="Sauvegarder toutes les modifications",
            command=self.save_all_modifications,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            button_frame,
            text="Sauvegarder sous...",
            command=self.save_as,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Réinitialiser", command=self.reset_form).pack(
            side=tk.LEFT, padx=5
        )

    def create_content_editor_tab(self):
        content_frame = ttk.Frame(self.notebook)
        self.notebook.add(content_frame, text="Éditeur de Contenu")

        # Frame pour les contrôles de navigation et modes
        nav_frame = ttk.Frame(content_frame)
        nav_frame.pack(fill="x", padx=5, pady=5)

        # Navigation des pages
        ttk.Button(nav_frame, text="◀◀", command=self.first_page).pack(
            side="left", padx=2
        )
        ttk.Button(nav_frame, text="◀", command=self.prev_page).pack(
            side="left", padx=2
        )

        self.page_var = tk.StringVar(value="0")
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
        self.zoom_var = tk.StringVar(value="100%")
        ttk.Label(nav_frame, textvariable=self.zoom_var).pack(side="left", padx=5)
        ttk.Button(nav_frame, text="+", command=self.zoom_in).pack(side="left", padx=2)

        # Modes d'interaction
        ttk.Separator(nav_frame, orient="vertical").pack(side="left", padx=10, fill="y")
        ttk.Label(nav_frame, text="Mode:").pack(side="left", padx=5)

        mode_frame = ttk.Frame(nav_frame)
        mode_frame.pack(side="left", padx=5)

        self.mode_var = tk.StringVar(value="select")
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

        # Bouton pour afficher les zones de texte
        ttk.Button(
            nav_frame, text="Afficher zones texte", command=self.toggle_text_blocks
        ).pack(side="left", padx=10)

        # Frame principal avec deux panneaux
        main_content_frame = ttk.Frame(content_frame)
        main_content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Panneau gauche - Visualisation PDF
        left_frame = ttk.LabelFrame(main_content_frame, text="Aperçu PDF Interactif")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Canvas avec scrollbars pour l'affichage PDF
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.pdf_canvas = tk.Canvas(canvas_frame, bg="white", cursor="crosshair")
        v_scrollbar = ttk.Scrollbar(
            canvas_frame, orient="vertical", command=self.pdf_canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            canvas_frame, orient="horizontal", command=self.pdf_canvas.xview
        )

        self.pdf_canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Événements de souris pour l'interaction
        self.pdf_canvas.bind("<Button-1>", self.on_canvas_click)
        self.pdf_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.pdf_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.pdf_canvas.bind("<Motion>", self.on_canvas_motion)
        self.pdf_canvas.bind("<Double-Button-1>", self.on_canvas_double_click)

        self.pdf_canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Panneau droit - Outils d'édition
        right_frame = ttk.LabelFrame(
            main_content_frame, text="Outils d'édition", width=350
        )
        right_frame.pack(side="right", fill="y")
        right_frame.pack_propagate(False)

        # Onglets pour les outils d'édition
        tools_notebook = ttk.Notebook(right_frame)
        tools_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Onglets
        self.create_text_tools_tab(tools_notebook)
        self.create_selection_tools_tab(tools_notebook)
        self.create_annotation_tools_tab(tools_notebook)
        self.create_text_extraction_tab(tools_notebook)

    def create_selection_tools_tab(self, parent):
        selection_frame = ttk.Frame(parent)
        parent.add(selection_frame, text="Sélection")

        # Informations sur la sélection courante
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

        # Formatage du texte sélectionné
        ttk.Separator(selection_frame, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(selection_frame, text="Formatage:", font=("Arial", 10, "bold")).pack(
            anchor="w"
        )

        format_frame = ttk.Frame(selection_frame)
        format_frame.pack(fill="x", pady=5)

        ttk.Label(format_frame, text="Taille:").pack(side="left")
        self.selected_font_size = tk.StringVar(value="12")
        ttk.Entry(format_frame, textvariable=self.selected_font_size, width=8).pack(
            side="left", padx=2
        )

        ttk.Label(format_frame, text="Couleur:").pack(side="left", padx=(10, 0))
        self.selected_text_color = tk.StringVar(value="black")
        color_combo = ttk.Combobox(
            format_frame,
            textvariable=self.selected_text_color,
            values=["black", "red", "blue", "green", "orange"],
            width=10,
        )
        color_combo.pack(side="left", padx=2)

        ttk.Button(
            selection_frame, text="Appliquer formatage", command=self.apply_formatting
        ).pack(pady=10)

    def create_text_tools_tab(self, parent):
        text_frame = ttk.Frame(parent)
        parent.add(text_frame, text="Ajout Texte")

        # Ajout de texte
        ttk.Label(
            text_frame, text="Ajouter du texte:", font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=5)

        ttk.Label(text_frame, text="Texte à ajouter:").pack(anchor="w")
        self.new_text_var = tk.StringVar()
        text_entry = ttk.Entry(text_frame, textvariable=self.new_text_var, width=30)
        text_entry.pack(fill="x", pady=2)

        # Position (sera remplie automatiquement lors du clic)
        pos_frame = ttk.Frame(text_frame)
        pos_frame.pack(fill="x", pady=5)

        ttk.Label(pos_frame, text="Position - X:").pack(side="left")
        self.text_x_var = tk.StringVar(value="100")
        ttk.Entry(pos_frame, textvariable=self.text_x_var, width=8).pack(
            side="left", padx=2
        )

        ttk.Label(pos_frame, text="Y:").pack(side="left", padx=(10, 0))
        self.text_y_var = tk.StringVar(value="100")
        ttk.Entry(pos_frame, textvariable=self.text_y_var, width=8).pack(
            side="left", padx=2
        )

        # Taille de police
        font_frame = ttk.Frame(text_frame)
        font_frame.pack(fill="x", pady=5)

        ttk.Label(font_frame, text="Taille:").pack(side="left")
        self.font_size_var = tk.StringVar(value="12")
        ttk.Entry(font_frame, textvariable=self.font_size_var, width=8).pack(
            side="left", padx=2
        )

        # Couleur
        ttk.Label(font_frame, text="Couleur:").pack(side="left", padx=(10, 0))
        self.text_color_var = tk.StringVar(value="black")
        color_combo = ttk.Combobox(
            font_frame,
            textvariable=self.text_color_var,
            values=["black", "red", "blue", "green", "orange"],
            width=10,
        )
        color_combo.pack(side="left", padx=2)

        ttk.Button(text_frame, text="Ajouter Texte", command=self.add_text_to_pdf).pack(
            pady=10
        )

        # Instructions
        ttk.Separator(text_frame, orient="horizontal").pack(fill="x", pady=10)
        instructions = tk.Text(text_frame, height=6, width=40, wrap=tk.WORD)
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

    def create_annotation_tools_tab(self, parent):
        annotation_frame = ttk.Frame(parent)
        parent.add(annotation_frame, text="Annotations")

        # Surlignage
        ttk.Label(
            annotation_frame, text="Surlignage:", font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=5)

        highlight_frame = ttk.Frame(annotation_frame)
        highlight_frame.pack(fill="x", pady=5)

        ttk.Label(highlight_frame, text="Couleur:").pack(side="left")
        self.highlight_color_var = tk.StringVar(value="yellow")
        highlight_combo = ttk.Combobox(
            highlight_frame,
            textvariable=self.highlight_color_var,
            values=["yellow", "green", "blue", "pink", "orange"],
            width=10,
        )
        highlight_combo.pack(side="left", padx=5)

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

        # Formes
        ttk.Separator(annotation_frame, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(annotation_frame, text="Formes:", font=("Arial", 10, "bold")).pack(
            anchor="w"
        )

        shapes_frame = ttk.Frame(annotation_frame)
        shapes_frame.pack(fill="x", pady=5)

        ttk.Button(
            shapes_frame, text="Rectangle", command=lambda: self.set_draw_mode("rect")
        ).pack(fill="x", pady=1)
        ttk.Button(
            shapes_frame, text="Cercle", command=lambda: self.set_draw_mode("circle")
        ).pack(fill="x", pady=1)
        ttk.Button(
            shapes_frame, text="Ligne", command=lambda: self.set_draw_mode("line")
        ).pack(fill="x", pady=1)

    def create_text_extraction_tab(self, parent):
        extract_frame = ttk.Frame(parent)
        parent.add(extract_frame, text="Extraction")

        ttk.Label(
            extract_frame, text="Texte extrait:", font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=5)

        # Zone de texte pour afficher le texte extrait
        self.extracted_text = scrolledtext.ScrolledText(
            extract_frame, height=15, width=35
        )
        self.extracted_text.pack(fill="both", expand=True, pady=5)

        # Boutons d'extraction
        extract_buttons = ttk.Frame(extract_frame)
        extract_buttons.pack(fill="x", pady=5)

        ttk.Button(
            extract_buttons,
            text="Extraire Page",
            command=self.extract_current_page_text,
        ).pack(fill="x", pady=1)
        ttk.Button(
            extract_buttons, text="Tout Extraire", command=self.extract_all_text
        ).pack(fill="x", pady=1)
        ttk.Button(
            extract_buttons, text="Sauvegarder Texte", command=self.save_extracted_text
        ).pack(fill="x", pady=1)

    # Fonctions d'interaction avec le canvas
    def change_mode(self):
        """Change le mode d'interaction"""
        mode = self.mode_var.get()
        self.selection_mode = mode

        # Changer le curseur selon le mode
        if mode == "select":
            self.pdf_canvas.config(cursor="crosshair")
        elif mode == "text":
            self.pdf_canvas.config(cursor="xterm")
        elif mode == "highlight":
            self.pdf_canvas.config(cursor="hand2")

        # Effacer les sélections précédentes
        self.clear_selections()

    def on_canvas_click(self, event):
        """Gestion du clic sur le canvas"""
        if not self.pdf_document:
            return

        # Convertir les coordonnées canvas en coordonnées PDF
        canvas_x = self.pdf_canvas.canvasx(event.x)
        canvas_y = self.pdf_canvas.canvasy(event.y)

        pdf_x, pdf_y = self.canvas_to_pdf_coords(canvas_x, canvas_y)

        mode = self.mode_var.get()

        if mode == "text":
            # Mode ajout de texte - mettre à jour les coordonnées
            self.text_x_var.set(str(int(pdf_x)))
            self.text_y_var.set(str(int(pdf_y)))

        elif mode == "select":
            # Mode sélection - commencer la sélection
            self.selection_start = (canvas_x, canvas_y)
            self.selection_start_pdf = (pdf_x, pdf_y)

        elif mode == "highlight":
            # Mode surlignage - commencer la zone de surlignage
            self.selection_start = (canvas_x, canvas_y)
            self.selection_start_pdf = (pdf_x, pdf_y)

    def on_canvas_drag(self, event):
        """Gestion du glissement sur le canvas"""
        if not self.pdf_document or not self.selection_start:
            return

        canvas_x = self.pdf_canvas.canvasx(event.x)
        canvas_y = self.pdf_canvas.canvasy(event.y)

        # Effacer le rectangle de sélection précédent
        if self.current_selection_rect:
            self.pdf_canvas.delete(self.current_selection_rect)

        # Dessiner le nouveau rectangle de sélection
        self.current_selection_rect = self.pdf_canvas.create_rectangle(
            self.selection_start[0],
            self.selection_start[1],
            canvas_x,
            canvas_y,
            outline="red",
            width=2,
            fill="",
            stipple="gray25",
        )

    def on_canvas_release(self, event):
        """Gestion du relâchement de la souris"""
        if not self.pdf_document or not self.selection_start:
            return

        canvas_x = self.pdf_canvas.canvasx(event.x)
        canvas_y = self.pdf_canvas.canvasy(event.y)

        pdf_x, pdf_y = self.canvas_to_pdf_coords(canvas_x, canvas_y)

        mode = self.mode_var.get()

        if mode == "select":
            # Sélectionner le texte dans la zone
            self.select_text_in_area(
                self.selection_start_pdf[0], self.selection_start_pdf[1], pdf_x, pdf_y
            )
        elif mode == "highlight":
            # Appliquer le surlignage dans la zone
            self.highlight_area(
                self.selection_start_pdf[0], self.selection_start_pdf[1], pdf_x, pdf_y
            )

        self.selection_start = None

    def on_canvas_motion(self, event):
        """Gestion du mouvement de la souris"""
        if not self.pdf_document:
            return

        # Changer le curseur selon la zone
        canvas_x = self.pdf_canvas.canvasx(event.x)
        canvas_y = self.pdf_canvas.canvasy(event.y)

        # Vérifier si on survole du texte
        if self.is_over_text(canvas_x, canvas_y):
            if self.mode_var.get() == "select":
                self.pdf_canvas.config(cursor="xterm")
        else:
            self.change_mode()  # Restaurer le curseur par défaut

    def on_canvas_double_click(self, event):
        """Gestion du double-clic pour sélectionner un mot"""
        if not self.pdf_document:
            return

        canvas_x = self.pdf_canvas.canvasx(event.x)
        canvas_y = self.pdf_canvas.canvasy(event.y)
        pdf_x, pdf_y = self.canvas_to_pdf_coords(canvas_x, canvas_y)

        # Sélectionner le mot sous le curseur
        self.select_word_at_position(pdf_x, pdf_y)

    # Fonctions utilitaires de conversion de coordonnées
    def canvas_to_pdf_coords(self, canvas_x, canvas_y):
        """Convertit les coordonnées canvas en coordonnées PDF"""
        if not self.pdf_document:
            return 0, 0

        page = self.pdf_document[self.current_page]
        page_rect = page.rect

        # Prendre en compte le zoom
        pdf_x = canvas_x / self.zoom_level
        pdf_y = canvas_y / self.zoom_level

        return pdf_x, pdf_y

    def pdf_to_canvas_coords(self, pdf_x, pdf_y):
        """Convertit les coordonnées PDF en coordonnées canvas"""
        canvas_x = pdf_x * self.zoom_level
        canvas_y = pdf_y * self.zoom_level
        return canvas_x, canvas_y

    # Fonctions de sélection et manipulation de texte
    def load_text_blocks(self):
        """Charge les blocs de texte de la page courante"""
        if not self.pdf_document:
            return

        page = self.pdf_document[self.current_page]
        self.text_blocks = page.get_text("dict")["blocks"]

    def toggle_text_blocks(self):
        """Affiche/masque les zones de texte détectées"""
        if not self.pdf_document:
            return

        # Effacer les rectangles existants
        self.pdf_canvas.delete("text_block")

        # Charger et afficher les blocs de texte
        self.load_text_blocks()

        for block in self.text_blocks:
            if "lines" in block:  # C'est un bloc de texte
                bbox = block["bbox"]
                canvas_coords = [
                    self.pdf_to_canvas_coords(bbox[0], bbox[1]),
                    self.pdf_to_canvas_coords(bbox[2], bbox[3]),
                ]

                self.pdf_canvas.create_rectangle(
                    canvas_coords[0][0],
                    canvas_coords[0][1],
                    canvas_coords[1][0],
                    canvas_coords[1][1],
                    outline="blue",
                    width=1,
                    fill="",
                    tags="text_block",
                )

    def is_over_text(self, canvas_x, canvas_y):
        """Vérifie si les coordonnées sont au-dessus d'un texte"""
        pdf_x, pdf_y = self.canvas_to_pdf_coords(canvas_x, canvas_y)

        for block in self.text_blocks:
            if "lines" in block:
                bbox = block["bbox"]
                if bbox[0] <= pdf_x <= bbox[2] and bbox[1] <= pdf_y <= bbox[3]:
                    return True
        return False

    def select_text_in_area(self, x1, y1, x2, y2):
        """Sélectionne le texte dans une zone rectangulaire"""
        if not self.pdf_document:
            return

        page = self.pdf_document[self.current_page]

        # Créer un rectangle de sélection
        rect = fitz.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

        # Extraire le texte dans cette zone
        selected_text = page.get_textbox(rect)

        if selected_text.strip():
            # Mettre à jour l'interface avec le texte sélectionné
            self.selection_info.config(state="normal")
            self.selection_info.delete("1.0", tk.END)
            self.selection_info.insert("1.0", f"Texte sélectionné:\n{selected_text}")
            self.selection_info.config(state="disabled")

            # Stocker la sélection pour les opérations futures
            self.current_selection = {
                "text": selected_text,
                "rect": rect,
                "page": self.current_page,
            }
        else:
            self.clear_selection_info()

    def select_word_at_position(self, x, y):
        """Sélectionne le mot à la position donnée"""
        if not self.pdf_document:
            return

        page = self.pdf_document[self.current_page]

        # Créer un petit rectangle autour du point cliqué
        point_rect = fitz.Rect(x - 5, y - 5, x + 5, y + 5)

        # Obtenir tous les mots de la page
        words = page.get_text("words")

        # Trouver le mot qui contient le point
        for word in words:
            word_rect = fitz.Rect(
                word[:4]
            )  # Les 4 premiers éléments sont les coordonnées
            if word_rect.intersects(point_rect):
                # Sélectionner ce mot
                self.selection_info.config(state="normal")
                self.selection_info.delete("1.0", tk.END)
                self.selection_info.insert(
                    "1.0", f"Mot sélectionné:\n{word[4]}"
                )  # Le 5ème élément est le texte
                self.selection_info.config(state="disabled")

                # Stocker la sélection
                self.current_selection = {
                    "text": word[4],
                    "rect": word_rect,
                    "page": self.current_page,
                }

                # Dessiner un rectangle autour du mot
                canvas_coords = [
                    self.pdf_to_canvas_coords(word_rect.x0, word_rect.y0),
                    self.pdf_to_canvas_coords(word_rect.x1, word_rect.y1),
                ]

                if self.current_selection_rect:
                    self.pdf_canvas.delete(self.current_selection_rect)

                self.current_selection_rect = self.pdf_canvas.create_rectangle(
                    canvas_coords[0][0],
                    canvas_coords[0][1],
                    canvas_coords[1][0],
                    canvas_coords[1][1],
                    outline="red",
                    width=2,
                    fill="",
                    stipple="gray25",
                )
                break

    def clear_selections(self):
        """Efface toutes les sélections"""
        if self.current_selection_rect:
            self.pdf_canvas.delete(self.current_selection_rect)
            self.current_selection_rect = None

        self.clear_selection_info()
        self.current_selection = None

    def clear_selection_info(self):
        """Efface les informations de sélection"""
        self.selection_info.config(state="normal")
        self.selection_info.delete("1.0", tk.END)
        self.selection_info.insert("1.0", "Aucune sélection")
        self.selection_info.config(state="disabled")

    # Fonctions d'édition de texte
    def delete_selected_text(self):
        """Supprime le texte sélectionné"""
        if not hasattr(self, "current_selection") or not self.current_selection:
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        try:
            page = self.pdf_document[self.current_selection["page"]]
            rect = self.current_selection["rect"]

            # Dessiner un rectangle blanc pour "effacer" le texte
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

            self.display_current_page()
            self.clear_selections()
            messagebox.showinfo("Succès", "Texte supprimé")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression: {str(e)}")

    def copy_selected_text(self):
        """Copie le texte sélectionné dans le presse-papiers"""
        if not hasattr(self, "current_selection") or not self.current_selection:
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_selection["text"])
        messagebox.showinfo("Succès", "Texte copié dans le presse-papiers")

    def replace_selected_text(self):
        """Remplace le texte sélectionné"""
        if not hasattr(self, "current_selection") or not self.current_selection:
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        replacement = self.replacement_text.get("1.0", tk.END).strip()
        if not replacement:
            messagebox.showwarning(
                "Attention", "Veuillez entrer le texte de remplacement"
            )
            return

        try:
            page = self.pdf_document[self.current_selection["page"]]
            rect = self.current_selection["rect"]

            # Effacer l'ancien texte
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

            # Ajouter le nouveau texte
            page.insert_text(
                (rect.x0, rect.y1 - 2),
                replacement,
                fontsize=float(self.selected_font_size.get()),
                color=self.get_color_rgb(self.selected_text_color.get()),
            )

            self.display_current_page()
            self.clear_selections()
            self.replacement_text.delete("1.0", tk.END)
            messagebox.showinfo("Succès", "Texte remplacé")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du remplacement: {str(e)}")

    def apply_formatting(self):
        """Applique le formatage au texte sélectionné"""
        if not hasattr(self, "current_selection") or not self.current_selection:
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        try:
            page = self.pdf_document[self.current_selection["page"]]
            rect = self.current_selection["rect"]
            text = self.current_selection["text"]

            # Effacer l'ancien texte
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

            # Ajouter le texte avec le nouveau formatage
            page.insert_text(
                (rect.x0, rect.y1 - 2),
                text,
                fontsize=float(self.selected_font_size.get()),
                color=self.get_color_rgb(self.selected_text_color.get()),
            )

            self.display_current_page()
            messagebox.showinfo("Succès", "Formatage appliqué")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du formatage: {str(e)}")

    def highlight_area(self, x1, y1, x2, y2):
        """Applique un surlignage dans une zone"""
        if not self.pdf_document:
            return

        try:
            page = self.pdf_document[self.current_page]
            rect = fitz.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

            # Ajouter une annotation de surlignage
            highlight = page.add_highlight_annot(rect)
            highlight.set_colors(
                stroke=self.get_color_rgb(self.highlight_color_var.get())
            )
            highlight.update()

            self.display_current_page()
            messagebox.showinfo("Succès", "Surlignage appliqué")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du surlignage: {str(e)}")

    def apply_highlight(self):
        """Applique le surlignage à la sélection courante"""
        if not hasattr(self, "current_selection") or not self.current_selection:
            messagebox.showwarning("Attention", "Aucun texte sélectionné")
            return

        try:
            page = self.pdf_document[self.current_selection["page"]]
            rect = self.current_selection["rect"]

            highlight = page.add_highlight_annot(rect)
            highlight.set_colors(
                stroke=self.get_color_rgb(self.highlight_color_var.get())
            )
            highlight.update()

            self.display_current_page()
            self.clear_selections()
            messagebox.showinfo("Succès", "Surlignage appliqué")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du surlignage: {str(e)}")

    def get_color_rgb(self, color_name):
        """Convertit un nom de couleur en tuple RGB"""
        color_map = {
            "black": (0, 0, 0),
            "red": (1, 0, 0),
            "blue": (0, 0, 1),
            "green": (0, 1, 0),
            "orange": (1, 0.5, 0),
            "yellow": (1, 1, 0),
            "pink": (1, 0.75, 0.8),
        }
        return color_map.get(color_name, (0, 0, 0))

    # Fonctions d'ajout de contenu
    def add_text_to_pdf(self):
        """Ajoute du texte à la position spécifiée"""
        if not self.pdf_document:
            messagebox.showwarning("Attention", "Aucun PDF chargé")
            return

        text = self.new_text_var.get().strip()
        if not text:
            messagebox.showwarning("Attention", "Veuillez entrer du texte")
            return

        try:
            x = float(self.text_x_var.get())
            y = float(self.text_y_var.get())
            font_size = float(self.font_size_var.get())
            color = self.get_color_rgb(self.text_color_var.get())

            page = self.pdf_document[self.current_page]

            # Ajouter le texte
            page.insert_text((x, y), text, fontsize=font_size, color=color)

            # Rafraîchir l'affichage
            self.display_current_page()

            messagebox.showinfo("Succès", "Texte ajouté avec succès")
            self.new_text_var.set("")

        except ValueError:
            messagebox.showerror("Erreur", "Valeurs numériques invalides")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout de texte: {str(e)}")

    def add_note(self):
        """Ajoute une annotation note"""
        if not self.pdf_document:
            messagebox.showwarning("Attention", "Aucun PDF chargé")
            return

        note_content = self.note_text.get("1.0", tk.END).strip()
        if not note_content:
            messagebox.showwarning("Attention", "Veuillez entrer le contenu de la note")
            return

        try:
            page = self.pdf_document[self.current_page]

            # Ajouter une annotation note au centre de la page
            rect = fitz.Rect(100, 100, 150, 150)
            annot = page.add_text_annot(rect.tl, note_content)
            annot.set_info(content=note_content)
            annot.update()

            self.display_current_page()
            messagebox.showinfo("Succès", "Note ajoutée avec succès")
            self.note_text.delete("1.0", tk.END)

        except Exception as e:
            messagebox.showerror(
                "Erreur", f"Erreur lors de l'ajout de la note: {str(e)}"
            )

    def set_draw_mode(self, mode):
        """Définit le mode de dessin"""
        self.draw_mode = mode
        messagebox.showinfo(
            "Info",
            f"Mode de dessin '{mode}' activé. Cliquez et glissez sur le PDF pour dessiner.",
        )

    # Fonctions de navigation et affichage
    def select_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier PDF",
            filetypes=[("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*")],
        )

        if file_path:
            self.current_pdf_path = file_path
            self.file_path_var.set(file_path)
            self.load_pdf_info()
            self.load_pdf_for_editing()

    def load_pdf_for_editing(self):
        """Charge le PDF avec PyMuPDF pour l'édition"""
        try:
            if self.pdf_document:
                self.pdf_document.close()

            self.pdf_document = fitz.open(self.current_pdf_path)
            self.total_pages = len(self.pdf_document)
            self.current_page = 0

            self.page_var.set("1")
            self.total_pages_label.config(text=f"/ {self.total_pages}")

            self.display_current_page()
            self.load_text_blocks()

        except Exception as e:
            messagebox.showerror(
                "Erreur", f"Impossible de charger le PDF pour édition: {str(e)}"
            )

    def display_current_page(self):
        """Affiche la page courante dans le canvas"""
        if not self.pdf_document or self.current_page >= self.total_pages:
            return

        try:
            page = self.pdf_document[self.current_page]

            # Créer une matrice de transformation pour le zoom
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=mat)

            # Convertir en image PIL
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))

            # Convertir pour Tkinter
            self.current_image = ImageTk.PhotoImage(img)

            # Effacer le canvas et afficher l'image
            self.pdf_canvas.delete("all")
            self.pdf_canvas.create_image(0, 0, anchor="nw", image=self.current_image)

            # Mettre à jour la région de défilement
            self.pdf_canvas.configure(scrollregion=self.pdf_canvas.bbox("all"))

            # Mettre à jour le numéro de page
            self.page_var.set(str(self.current_page + 1))

            # Recharger les blocs de texte pour la nouvelle page
            self.load_text_blocks()

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage: {str(e)}")

    # Fonctions de navigation
    def first_page(self):
        """Va à la première page"""
        if self.pdf_document and self.current_page > 0:
            self.current_page = 0
            self.display_current_page()
            self.clear_selections()

    def prev_page(self):
        """Va à la page précédente"""
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.display_current_page()
            self.clear_selections()

    def next_page(self):
        """Va à la page suivante"""
        if self.pdf_document and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_current_page()
            self.clear_selections()

    def last_page(self):
        """Va à la dernière page"""
        if self.pdf_document and self.current_page < self.total_pages - 1:
            self.current_page = self.total_pages - 1
            self.display_current_page()
            self.clear_selections()

    def goto_page(self, event=None):
        """Va à une page spécifique"""
        try:
            page_num = int(self.page_var.get()) - 1
            if 0 <= page_num < self.total_pages:
                self.current_page = page_num
                self.display_current_page()
                self.clear_selections()
            else:
                self.page_var.set(str(self.current_page + 1))
                messagebox.showwarning(
                    "Attention", f"Page invalide. Utilisez 1-{self.total_pages}"
                )
        except ValueError:
            self.page_var.set(str(self.current_page + 1))
            messagebox.showerror("Erreur", "Numéro de page invalide")

    # Fonctions de zoom
    def zoom_in(self):
        """Augmente le zoom"""
        if self.zoom_level < 3.0:
            self.zoom_level += 0.25
            self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
            self.display_current_page()

    def zoom_out(self):
        """Diminue le zoom"""
        if self.zoom_level > 0.5:
            self.zoom_level -= 0.25
            self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
            self.display_current_page()

    # Fonctions d'extraction de texte
    def extract_current_page_text(self):
        """Extrait le texte de la page courante"""
        if not self.pdf_document:
            messagebox.showwarning("Attention", "Aucun PDF chargé")
            return

        try:
            page = self.pdf_document[self.current_page]
            text = page.get_text()

            self.extracted_text.delete("1.0", tk.END)
            self.extracted_text.insert("1.0", text)

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'extraction: {str(e)}")

    def extract_all_text(self):
        """Extrait le texte de tout le PDF"""
        if not self.pdf_document:
            messagebox.showwarning("Attention", "Aucun PDF chargé")
            return

        try:
            all_text = ""
            for page_num in range(len(self.pdf_document)):
                page = self.pdf_document[page_num]
                text = page.get_text()
                all_text += f"--- Page {page_num + 1} ---\n{text}\n\n"

            self.extracted_text.delete("1.0", tk.END)
            self.extracted_text.insert("1.0", all_text)

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'extraction: {str(e)}")

    def save_extracted_text(self):
        """Sauvegarde le texte extrait"""
        text_content = self.extracted_text.get("1.0", tk.END).strip()
        if not text_content:
            messagebox.showwarning("Attention", "Aucun texte à sauvegarder")
            return

        file_path = filedialog.asksaveasfilename(
            title="Sauvegarder le texte extrait",
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text_content)
                messagebox.showinfo("Succès", f"Texte sauvegardé dans: {file_path}")
            except Exception as e:
                messagebox.showerror(
                    "Erreur", f"Erreur lors de la sauvegarde: {str(e)}"
                )

    # Fonctions des onglets existants (métadonnées, manipulation, etc.)
    def create_metadata_tab(self):
        metadata_frame = ttk.Frame(self.notebook)
        self.notebook.add(metadata_frame, text="Métadonnées")

        # Créer un canvas avec scrollbar
        canvas = tk.Canvas(metadata_frame)
        scrollbar = ttk.Scrollbar(
            metadata_frame, orient="vertical", command=canvas.yview
        )
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Champs de métadonnées
        self.metadata_vars = {}
        metadata_fields = [
            ("Titre", "title"),
            ("Auteur", "author"),
            ("Sujet", "subject"),
            ("Créateur", "creator"),
            ("Producteur", "producer"),
            ("Mots-clés", "keywords"),
            ("Date de création", "creation_date"),
            ("Date de modification", "modification_date"),
        ]

        for i, (label, key) in enumerate(metadata_fields):
            ttk.Label(scrollable_frame, text=f"{label}:").grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            var = tk.StringVar()
            self.metadata_vars[key] = var
            ttk.Entry(scrollable_frame, textvariable=var, width=50).grid(
                row=i, column=1, sticky=(tk.W, tk.E), padx=5, pady=2
            )

        scrollable_frame.columnconfigure(1, weight=1)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_manipulation_tab(self):
        manip_frame = ttk.Frame(self.notebook)
        self.notebook.add(manip_frame, text="Manipulation PDF")

        # Section extraction de pages
        extract_frame = ttk.LabelFrame(
            manip_frame, text="Extraction de pages", padding="10"
        )
        extract_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(extract_frame, text="Pages à extraire (ex: 1,3,5-7):").pack(
            anchor="w"
        )
        self.extract_pages_var = tk.StringVar()
        ttk.Entry(extract_frame, textvariable=self.extract_pages_var, width=30).pack(
            anchor="w", pady=2
        )
        ttk.Button(
            extract_frame, text="Extraire pages", command=self.extract_pages
        ).pack(anchor="w", pady=5)

        # Section fusion de PDF
        merge_frame = ttk.LabelFrame(manip_frame, text="Fusion de PDF", padding="10")
        merge_frame.pack(fill="x", padx=10, pady=5)

        self.merge_files = []
        ttk.Button(
            merge_frame, text="Ajouter des fichiers PDF", command=self.add_merge_files
        ).pack(anchor="w", pady=2)

        self.merge_listbox = tk.Listbox(merge_frame, height=4)
        self.merge_listbox.pack(fill="x", pady=2)

        merge_buttons = ttk.Frame(merge_frame)
        merge_buttons.pack(fill="x", pady=2)
        ttk.Button(merge_buttons, text="Fusionner", command=self.merge_pdfs).pack(
            side="left", padx=2
        )
        ttk.Button(
            merge_buttons, text="Supprimer sélectionné", command=self.remove_merge_file
        ).pack(side="left", padx=2)

        # Section rotation de pages
        rotate_frame = ttk.LabelFrame(
            manip_frame, text="Rotation de pages", padding="10"
        )
        rotate_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(rotate_frame, text="Pages à faire tourner (ex: 1,3,5-7):").pack(
            anchor="w"
        )
        self.rotate_pages_var = tk.StringVar()
        ttk.Entry(rotate_frame, textvariable=self.rotate_pages_var, width=30).pack(
            anchor="w", pady=2
        )

        rotate_options = ttk.Frame(rotate_frame)
        rotate_options.pack(anchor="w", pady=2)
        ttk.Label(rotate_options, text="Angle:").pack(side="left")
        self.rotate_angle_var = tk.StringVar(value="90")
        ttk.Combobox(
            rotate_options,
            textvariable=self.rotate_angle_var,
            values=["90", "180", "270"],
            width=10,
        ).pack(side="left", padx=5)
        ttk.Button(
            rotate_options, text="Appliquer rotation", command=self.rotate_pages
        ).pack(side="left", padx=5)

    def create_info_tab(self):
        info_frame = ttk.Frame(self.notebook)
        self.notebook.add(info_frame, text="Informations")

        self.info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, height=20)
        self.info_text.pack(fill="both", expand=True, padx=10, pady=10)

    def load_pdf_info(self):
        try:
            with open(self.current_pdf_path, "rb") as file:
                self.pdf_reader = PyPDF2.PdfReader(file)

                # Charger les métadonnées
                metadata = self.pdf_reader.metadata
                if metadata:
                    self.metadata_vars["title"].set(metadata.get("/Title", "") or "")
                    self.metadata_vars["author"].set(metadata.get("/Author", "") or "")
                    self.metadata_vars["subject"].set(
                        metadata.get("/Subject", "") or ""
                    )
                    self.metadata_vars["creator"].set(
                        metadata.get("/Creator", "") or ""
                    )
                    self.metadata_vars["producer"].set(
                        metadata.get("/Producer", "") or ""
                    )
                    self.metadata_vars["keywords"].set(
                        metadata.get("/Keywords", "") or ""
                    )

                    # Dates
                    creation_date = metadata.get("/CreationDate", "")
                    if creation_date:
                        self.metadata_vars["creation_date"].set(str(creation_date))

                    mod_date = metadata.get("/ModDate", "")
                    if mod_date:
                        self.metadata_vars["modification_date"].set(str(mod_date))

                # Afficher les informations du PDF
                self.display_pdf_info()

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le PDF: {str(e)}")

    def display_pdf_info(self):
        if not self.pdf_reader:
            return

        info_text = f"Informations du PDF: {os.path.basename(self.current_pdf_path)}\n"
        info_text += "=" * 50 + "\n\n"

        # Informations générales
        info_text += f"Nombre de pages: {len(self.pdf_reader.pages)}\n"
        info_text += (
            f"Taille du fichier: {os.path.getsize(self.current_pdf_path)} bytes\n"
        )

        # Métadonnées
        if self.pdf_reader.metadata:
            info_text += "\nMétadonnées:\n"
            info_text += "-" * 20 + "\n"
            for key, value in self.pdf_reader.metadata.items():
                if value:
                    info_text += f"{key}: {value}\n"

        # Informations sur les pages
        info_text += "\nInformations des pages:\n"
        info_text += "-" * 30 + "\n"
        for i, page in enumerate(
            self.pdf_reader.pages[:5]
        ):  # Limite aux 5 premières pages
            try:
                mediabox = page.mediabox
                info_text += f"Page {i+1}: {mediabox.width} x {mediabox.height} pts\n"
            except Exception as e:
                info_text += f"Page {i+1}: Impossible de lire les dimensions\n (Erreur: {str(e)})\n"

        if len(self.pdf_reader.pages) > 5:
            info_text += f"... et {len(self.pdf_reader.pages) - 5} autres pages\n"

        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", info_text)

    # Fonctions de sauvegarde et manipulation (conservées de l'original)
    def save_all_modifications(self):
        """Sauvegarde toutes les modifications dans le fichier original"""
        if not self.current_pdf_path or not self.pdf_document:
            messagebox.showwarning("Attention", "Aucun fichier PDF chargé")
            return

        try:
            # Sauvegarder les modifications de contenu
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.close()

            self.pdf_document.save(temp_file.name)

            # Maintenant traiter les métadonnées avec PyPDF2
            with open(temp_file.name, "rb") as input_file:
                pdf_reader = PyPDF2.PdfReader(input_file)
                pdf_writer = PyPDF2.PdfWriter()

                # Copier toutes les pages
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)

                # Mettre à jour les métadonnées
                metadata = {}
                if self.metadata_vars["title"].get():
                    metadata["/Title"] = self.metadata_vars["title"].get()
                if self.metadata_vars["author"].get():
                    metadata["/Author"] = self.metadata_vars["author"].get()
                if self.metadata_vars["subject"].get():
                    metadata["/Subject"] = self.metadata_vars["subject"].get()
                if self.metadata_vars["creator"].get():
                    metadata["/Creator"] = self.metadata_vars["creator"].get()
                if self.metadata_vars["producer"].get():
                    metadata["/Producer"] = self.metadata_vars["producer"].get()
                if self.metadata_vars["keywords"].get():
                    metadata["/Keywords"] = self.metadata_vars["keywords"].get()

                # Ajouter la date de modification
                metadata["/ModDate"] = f"D:{datetime.now().strftime('%Y%m%d%H%M%S')}"

                pdf_writer.add_metadata(metadata)

                # Écrire le fichier final
                with open(self.current_pdf_path, "wb") as output_file:
                    pdf_writer.write(output_file)

            # Nettoyer le fichier temporaire
            os.unlink(temp_file.name)

            # Recharger le PDF
            self.load_pdf_for_editing()
            self.load_pdf_info()

            messagebox.showinfo(
                "Succès", "Toutes les modifications ont été sauvegardées!"
            )

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

    def save_as(self):
        """Sauvegarde sous un nouveau nom"""
        if not self.current_pdf_path or not self.pdf_document:
            messagebox.showwarning("Attention", "Aucun fichier PDF chargé")
            return

        output_path = filedialog.asksaveasfilename(
            title="Sauvegarder sous...",
            defaultextension=".pdf",
            filetypes=[("Fichiers PDF", "*.pdf")],
        )

        if output_path:
            try:
                # Sauvegarder les modifications de contenu
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                temp_file.close()

                self.pdf_document.save(temp_file.name)

                # Traiter les métadonnées
                with open(temp_file.name, "rb") as input_file:
                    pdf_reader = PyPDF2.PdfReader(input_file)
                    pdf_writer = PyPDF2.PdfWriter()

                    for page in pdf_reader.pages:
                        pdf_writer.add_page(page)

                    # Métadonnées
                    metadata = {}
                    if self.metadata_vars["title"].get():
                        metadata["/Title"] = self.metadata_vars["title"].get()
                    if self.metadata_vars["author"].get():
                        metadata["/Author"] = self.metadata_vars["author"].get()
                    if self.metadata_vars["subject"].get():
                        metadata["/Subject"] = self.metadata_vars["subject"].get()
                    if self.metadata_vars["creator"].get():
                        metadata["/Creator"] = self.metadata_vars["creator"].get()
                    if self.metadata_vars["producer"].get():
                        metadata["/Producer"] = self.metadata_vars["producer"].get()
                    if self.metadata_vars["keywords"].get():
                        metadata["/Keywords"] = self.metadata_vars["keywords"].get()

                    metadata["/ModDate"] = (
                        f"D:{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    )
                    pdf_writer.add_metadata(metadata)

                    with open(output_path, "wb") as output_file:
                        pdf_writer.write(output_file)

                # Nettoyer
                os.unlink(temp_file.name)

                messagebox.showinfo("Succès", f"PDF sauvegardé dans: {output_path}")

            except Exception as e:
                messagebox.showerror(
                    "Erreur", f"Erreur lors de la sauvegarde: {str(e)}"
                )

    # Fonctions de manipulation (conservées de l'original)
    def parse_page_ranges(self, page_input):
        """Parse une chaîne comme '1,3,5-7' en liste de numéros de pages"""
        pages = []
        parts = page_input.split(",")

        for part in parts:
            part = part.strip()
            if "-" in part:
                start, end = map(int, part.split("-"))
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))

        return sorted(set(pages))

    def extract_pages(self):
        if not self.current_pdf_path:
            messagebox.showwarning("Attention", "Aucun fichier PDF sélectionné")
            return

        pages_input = self.extract_pages_var.get().strip()
        if not pages_input:
            messagebox.showwarning(
                "Attention", "Veuillez spécifier les pages à extraire"
            )
            return

        try:
            pages_to_extract = self.parse_page_ranges(pages_input)

            # Vérifier que les pages existent
            max_pages = len(self.pdf_reader.pages)
            invalid_pages = [p for p in pages_to_extract if p < 1 or p > max_pages]
            if invalid_pages:
                messagebox.showerror(
                    "Erreur",
                    f"Pages invalides: {invalid_pages}. Le PDF a {max_pages} pages.",
                )
                return

            output_path = filedialog.asksaveasfilename(
                title="Sauvegarder les pages extraites",
                defaultextension=".pdf",
                filetypes=[("Fichiers PDF", "*.pdf")],
            )

            if output_path:
                with open(self.current_pdf_path, "rb") as input_file:
                    pdf_reader = PyPDF2.PdfReader(input_file)
                    pdf_writer = PyPDF2.PdfWriter()

                    for page_num in pages_to_extract:
                        pdf_writer.add_page(pdf_reader.pages[page_num - 1])

                    with open(output_path, "wb") as output_file:
                        pdf_writer.write(output_file)

                messagebox.showinfo(
                    "Succès", f"Pages extraites sauvegardées dans: {output_path}"
                )

        except ValueError:
            messagebox.showerror(
                "Erreur", "Format de pages invalide. Utilisez le format: 1,3,5-7"
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'extraction: {str(e)}")

    def add_merge_files(self):
        files = filedialog.askopenfilenames(
            title="Sélectionner des fichiers PDF à fusionner",
            filetypes=[("Fichiers PDF", "*.pdf")],
        )

        for file_path in files:
            if file_path not in self.merge_files:
                self.merge_files.append(file_path)
                self.merge_listbox.insert(tk.END, os.path.basename(file_path))

    def remove_merge_file(self):
        selection = self.merge_listbox.curselection()
        if selection:
            index = selection[0]
            self.merge_listbox.delete(index)
            del self.merge_files[index]

    def merge_pdfs(self):
        if len(self.merge_files) < 2:
            messagebox.showwarning(
                "Attention", "Sélectionnez au moins 2 fichiers PDF à fusionner"
            )
            return

        output_path = filedialog.asksaveasfilename(
            title="Sauvegarder le PDF fusionné",
            defaultextension=".pdf",
            filetypes=[("Fichiers PDF", "*.pdf")],
        )

        if output_path:
            try:
                pdf_writer = PyPDF2.PdfWriter()

                for file_path in self.merge_files:
                    with open(file_path, "rb") as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page in pdf_reader.pages:
                            pdf_writer.add_page(page)

                with open(output_path, "wb") as output_file:
                    pdf_writer.write(output_file)

                messagebox.showinfo(
                    "Succès", f"PDF fusionné sauvegardé dans: {output_path}"
                )

            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la fusion: {str(e)}")

    def rotate_pages(self):
        if not self.current_pdf_path:
            messagebox.showwarning("Attention", "Aucun fichier PDF sélectionné")
            return

        pages_input = self.rotate_pages_var.get().strip()
        if not pages_input:
            messagebox.showwarning(
                "Attention", "Veuillez spécifier les pages à faire tourner"
            )
            return

        try:
            pages_to_rotate = self.parse_page_ranges(pages_input)
            angle = int(self.rotate_angle_var.get())

            max_pages = len(self.pdf_reader.pages)
            invalid_pages = [p for p in pages_to_rotate if p < 1 or p > max_pages]
            if invalid_pages:
                messagebox.showerror(
                    "Erreur",
                    f"Pages invalides: {invalid_pages}. Le PDF a {max_pages} pages.",
                )
                return

            output_path = filedialog.asksaveasfilename(
                title="Sauvegarder le PDF avec rotation",
                defaultextension=".pdf",
                filetypes=[("Fichiers PDF", "*.pdf")],
            )

            if output_path:
                with open(self.current_pdf_path, "rb") as input_file:
                    pdf_reader = PyPDF2.PdfReader(input_file)
                    pdf_writer = PyPDF2.PdfWriter()

                    for i, page in enumerate(pdf_reader.pages):
                        if (i + 1) in pages_to_rotate:
                            page = page.rotate(angle)
                        pdf_writer.add_page(page)

                    with open(output_path, "wb") as output_file:
                        pdf_writer.write(output_file)

                messagebox.showinfo(
                    "Succès", f"PDF avec rotation sauvegardé dans: {output_path}"
                )

        except ValueError:
            messagebox.showerror("Erreur", "Format de pages invalide ou angle invalide")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la rotation: {str(e)}")

    def reset_form(self):
        """Réinitialise tous les champs du formulaire"""
        # Réinitialiser les métadonnées
        for var in self.metadata_vars.values():
            var.set("")

        # Réinitialiser les champs de manipulation
        self.extract_pages_var.set("")
        self.rotate_pages_var.set("")
        self.rotate_angle_var.set("90")

        # Réinitialiser la fusion
        self.merge_files.clear()
        self.merge_listbox.delete(0, tk.END)

        # Réinitialiser les champs d'édition de contenu
        if hasattr(self, "new_text_var"):
            self.new_text_var.set("")
            self.text_x_var.set("100")
            self.text_y_var.set("100")
            self.font_size_var.set("12")
            self.text_color_var.set("black")
            self.highlight_color_var.set("yellow")
            self.selected_font_size.set("12")
            self.selected_text_color.set("black")

        # Vider les zones de texte
        if hasattr(self, "note_text"):
            self.note_text.delete("1.0", tk.END)
        if hasattr(self, "extracted_text"):
            self.extracted_text.delete("1.0", tk.END)
        if hasattr(self, "replacement_text"):
            self.replacement_text.delete("1.0", tk.END)

        self.info_text.delete("1.0", tk.END)

        # Réinitialiser l'affichage PDF
        if hasattr(self, "pdf_canvas"):
            self.pdf_canvas.delete("all")

        # Fermer le document PDF
        if self.pdf_document:
            self.pdf_document.close()
            self.pdf_document = None

        self.current_pdf_path = None
        self.file_path_var.set("")
        self.current_page = 0
        self.total_pages = 0
        if hasattr(self, "page_var"):
            self.page_var.set("0")
            self.total_pages_label.config(text="/ 0")
        self.zoom_level = 1.0
        if hasattr(self, "zoom_var"):
            self.zoom_var.set("100%")

        # Réinitialiser les sélections
        self.clear_selections()

    def __del__(self):
        """Nettoyage lors de la destruction de l'objet"""
        if hasattr(self, "pdf_document") and self.pdf_document:
            self.pdf_document.close()


def main():
    root = tk.Tk()
    app = PDFEditor(root)

    # Gérer la fermeture propre de l'application
    def on_closing():
        if hasattr(app, "pdf_document") and app.pdf_document:
            app.pdf_document.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
