"""
Service pour l'édition de texte dans les PDFs avec préservation du formatage
"""

import fitz
from typing import Dict, List, Tuple


class TextEditingService:
    def __init__(self, pdf_manager):
        self.pdf_manager = pdf_manager
        self.hidden_text_areas = {}  # {page_num: [rect1, rect2, ...]}
        self.replaced_text_areas = (
            {}
        )  # {page_num: [(original_rect, new_text, new_rect), ...]}

    def analyze_text_formatting(self, page_num: int, rect: fitz.Rect) -> Dict:
        """Analyse le formatage du texte dans une zone donnée"""
        page = self.pdf_manager.pdf_document[page_num]
        text_dict = page.get_text("dict")

        formatting_info = {
            "font_name": "helv",
            "font_size": 12,
            "font_flags": 0,
            "color": [0, 0, 0],
            "line_height": 14,
            "char_spacing": 0,
            "word_spacing": 0,
            "alignment": "left",
        }

        # Parcourir les blocs pour trouver le texte dans la zone
        for block in text_dict["blocks"]:
            if "lines" in block:
                block_rect = fitz.Rect(block["bbox"])
                if block_rect.intersects(rect):
                    for line in block["lines"]:
                        line_rect = fitz.Rect(line["bbox"])
                        if line_rect.intersects(rect):
                            for span in line["spans"]:
                                span_rect = fitz.Rect(span["bbox"])
                                if span_rect.intersects(rect):
                                    # Extraire les informations de formatage
                                    formatting_info.update(
                                        {
                                            "font_name": span.get("font", "helv"),
                                            "font_size": span.get("size", 12),
                                            "font_flags": span.get("flags", 0),
                                            "color": span.get("color", 0),
                                            "line_height": line_rect.height,
                                        }
                                    )

                                    # Calculer l'espacement des caractères
                                    if len(span.get("chars", [])) > 1:
                                        chars = span["chars"]
                                        total_width = span_rect.width
                                        text_width = sum(
                                            char.get("width", 0) for char in chars
                                        )
                                        if text_width > 0:
                                            formatting_info["char_spacing"] = (
                                                total_width - text_width
                                            ) / len(chars)

                                    return formatting_info

        return formatting_info

    def calculate_text_dimensions(
        self, text: str, formatting: Dict
    ) -> Tuple[float, float]:
        """Calcule les dimensions approximatives du texte avec le formatage donné"""
        font_size = formatting["font_size"]

        # Estimation approximative basée sur la taille de police
        # Ces valeurs peuvent être ajustées selon les besoins
        char_width_ratio = (
            0.6  # Ratio largeur/hauteur moyen pour la plupart des polices
        )
        avg_char_width = font_size * char_width_ratio

        # Calculer la largeur totale
        text_width = len(text) * avg_char_width + (len(text) - 1) * formatting.get(
            "char_spacing", 0
        )
        text_height = formatting.get("line_height", font_size * 1.2)

        return text_width, text_height

    def adjust_rect_for_text(
        self, original_rect: fitz.Rect, new_text: str, formatting: Dict
    ) -> fitz.Rect:
        """Ajuste le rectangle pour s'adapter au nouveau texte"""
        new_width, new_height = self.calculate_text_dimensions(new_text, formatting)

        # Créer un nouveau rectangle ajusté
        adjusted_rect = fitz.Rect(
            original_rect.x0,
            original_rect.y0,
            original_rect.x0 + new_width + 4,  # Petit padding
            original_rect.y0 + new_height + 2,  # Petit padding
        )

        # S'assurer que le rectangle ne dépasse pas les limites de la page
        page = self.pdf_manager.pdf_document[self.pdf_manager.current_page]
        page_rect = page.rect

        if adjusted_rect.x1 > page_rect.x1:
            # Ajuster en réduisant la largeur ou en déplaçant vers la gauche
            overflow = adjusted_rect.x1 - page_rect.x1
            adjusted_rect.x0 = max(0, adjusted_rect.x0 - overflow)
            adjusted_rect.x1 = min(page_rect.x1, original_rect.x0 + new_width + 4)

        if adjusted_rect.y1 > page_rect.y1:
            adjusted_rect.y1 = min(page_rect.y1, adjusted_rect.y0 + new_height + 2)

        return adjusted_rect

    def hide_text_area(self, page_num: int, rect: fitz.Rect):
        """Masque une zone de texte"""
        if page_num not in self.hidden_text_areas:
            self.hidden_text_areas[page_num] = []

        self.hidden_text_areas[page_num].append(rect)

        # Ajouter un rectangle blanc pour masquer le texte
        page = self.pdf_manager.pdf_document[page_num]

        # Créer une annotation rectangle blanche
        white_rect = page.add_rect_annot(rect)
        white_rect.set_colors(stroke=[1, 1, 1], fill=[1, 1, 1])  # Blanc
        white_rect.set_border(width=0)  # Pas de bordure
        white_rect.update()

    def replace_text_area(self, page_num: int, original_rect: fitz.Rect, new_text: str):
        """Remplace le texte dans une zone en préservant le formatage"""
        # Analyser le formatage du texte original
        formatting = self.analyze_text_formatting(page_num, original_rect)

        # Ajuster le rectangle pour le nouveau texte
        adjusted_rect = self.adjust_rect_for_text(original_rect, new_text, formatting)

        # D'abord masquer l'ancien texte (avec un rectangle légèrement plus grand)
        mask_rect = fitz.Rect(
            original_rect.x0 - 1,
            original_rect.y0 - 1,
            max(original_rect.x1, adjusted_rect.x1) + 1,
            max(original_rect.y1, adjusted_rect.y1) + 1,
        )
        self.hide_text_area(page_num, mask_rect)

        # Ajouter le nouveau texte avec le formatage préservé
        page = self.pdf_manager.pdf_document[page_num]

        # Convertir la couleur si nécessaire
        text_color = self.convert_color(formatting["color"])

        # Déterminer le type d'annotation selon la longueur du texte
        if len(new_text.split("\n")) > 1 or len(new_text) > 50:
            # Texte long : utiliser FreeText
            text_annot = page.add_freetext_annot(
                adjusted_rect,
                new_text,
                fontsize=formatting["font_size"],
                fontname=self.normalize_font_name(formatting["font_name"]),
                text_color=text_color,
                fill_color=[1, 1, 1],  # Fond blanc
                border_color=[1, 1, 1],  # Bordure blanche
            )
            text_annot.set_border(width=0)
        else:
            # Texte court : utiliser Text (plus précis)
            text_point = fitz.Point(
                adjusted_rect.x0 + 2, adjusted_rect.y0 + formatting["font_size"]
            )
            text_annot = page.add_text_annot(text_point, new_text)

            # Ajouter un rectangle de fond blanc
            bg_rect = page.add_rect_annot(adjusted_rect)
            bg_rect.set_colors(stroke=[1, 1, 1], fill=[1, 1, 1])
            bg_rect.set_border(width=0)
            bg_rect.update()

            # Puis ajouter le texte par-dessus
            text_insertion_point = fitz.Point(
                adjusted_rect.x0 + 2, adjusted_rect.y0 + formatting["font_size"] * 0.8
            )
            page.insert_text(
                text_insertion_point,
                new_text,
                fontsize=formatting["font_size"],
                fontname=self.normalize_font_name(formatting["font_name"]),
                color=text_color,
            )

        if "text_annot" in locals():
            text_annot.update()

        # Enregistrer le remplacement
        if page_num not in self.replaced_text_areas:
            self.replaced_text_areas[page_num] = []

        self.replaced_text_areas[page_num].append(
            (original_rect, new_text, adjusted_rect, formatting)
        )

    def convert_color(self, color_value) -> List[float]:
        """Convertit une valeur de couleur en format RGB normalisé"""
        if isinstance(color_value, (int, float)):
            # Couleur en niveaux de gris ou valeur unique
            if color_value == 0:
                return [0, 0, 0]  # Noir
            elif color_value == 1 or color_value >= 16777215:  # Blanc ou valeur max
                return [1, 1, 1]
            else:
                # Convertir depuis une valeur entière RGB
                if color_value > 1:
                    r = ((color_value >> 16) & 255) / 255.0
                    g = ((color_value >> 8) & 255) / 255.0
                    b = (color_value & 255) / 255.0
                    return [r, g, b]
                else:
                    # Niveau de gris
                    return [color_value, color_value, color_value]
        elif isinstance(color_value, (list, tuple)) and len(color_value) >= 3:
            # Déjà en format RGB
            return list(color_value[:3])
        else:
            # Valeur par défaut : noir
            return [0, 0, 0]

    def normalize_font_name(self, font_name: str) -> str:
        """Normalise le nom de police pour PyMuPDF"""
        font_mapping = {
            "Times-Roman": "times-roman",
            "Times-Bold": "times-bold",
            "Times-Italic": "times-italic",
            "Times-BoldItalic": "times-bolditalic",
            "Helvetica": "helv",
            "Helvetica-Bold": "hebo",
            "Helvetica-Oblique": "heit",
            "Helvetica-BoldOblique": "hebi",
            "Courier": "cour",
            "Courier-Bold": "cobo",
            "Courier-Oblique": "coit",
            "Courier-BoldOblique": "cobi",
        }

        return font_mapping.get(font_name, "helv")

    def get_text_formatting_info(self, page_num: int, rect: fitz.Rect) -> str:
        """Retourne une description du formatage du texte"""
        formatting = self.analyze_text_formatting(page_num, rect)

        font_style = "Normal"
        if formatting["font_flags"] & 2**4:  # Bold
            font_style = "Gras"
        if formatting["font_flags"] & 2**6:  # Italic
            font_style += " Italique" if font_style == "Normal" else " + Italique"

        return f"Police: {formatting['font_name']}, Taille: {formatting['font_size']:.1f}, Style: {font_style}"

    # ... (autres méthodes restent identiques)
    def is_text_hidden(self, page_num: int, point_or_rect) -> bool:
        """Vérifie si un point ou rectangle est dans une zone de texte masquée"""
        if page_num not in self.hidden_text_areas:
            return False

        if isinstance(point_or_rect, fitz.Point):
            point = point_or_rect
            for hidden_rect in self.hidden_text_areas[page_num]:
                if hidden_rect.contains(point):
                    return True
        else:  # fitz.Rect
            rect = point_or_rect
            for hidden_rect in self.hidden_text_areas[page_num]:
                if hidden_rect.intersects(rect):
                    return True

        return False

    def get_filtered_text_blocks(self, page_num: int) -> List:
        """Retourne les blocs de texte en filtrant les zones masquées"""
        page = self.pdf_manager.pdf_document[page_num]
        text_dict = page.get_text("dict")

        filtered_blocks = []

        for block in text_dict["blocks"]:
            if "lines" in block:  # Bloc de texte
                block_rect = fitz.Rect(block["bbox"])

                # Vérifier si le bloc entier est masqué
                if not self.is_text_hidden(page_num, block_rect):
                    # Filtrer les lignes individuelles
                    filtered_lines = []

                    for line in block["lines"]:
                        line_rect = fitz.Rect(line["bbox"])
                        if not self.is_text_hidden(page_num, line_rect):
                            # Filtrer les spans individuels
                            filtered_spans = []

                            for span in line["spans"]:
                                span_rect = fitz.Rect(span["bbox"])
                                if not self.is_text_hidden(page_num, span_rect):
                                    filtered_spans.append(span)

                            if filtered_spans:
                                line["spans"] = filtered_spans
                                filtered_lines.append(line)

                    if filtered_lines:
                        block["lines"] = filtered_lines
                        filtered_blocks.append(block)
            else:
                # Bloc d'image, garder tel quel
                filtered_blocks.append(block)

        return filtered_blocks

    def get_filtered_words(self, page_num: int) -> List:
        """Retourne les mots en filtrant les zones masquées"""
        page = self.pdf_manager.pdf_document[page_num]
        words = page.get_text("words")

        filtered_words = []

        for word in words:
            word_rect = fitz.Rect(word[:4])
            if not self.is_text_hidden(page_num, word_rect):
                filtered_words.append(word)

        return filtered_words

    def clear_page_edits(self, page_num: int):
        """Efface toutes les modifications d'une page"""
        if page_num in self.hidden_text_areas:
            del self.hidden_text_areas[page_num]
        if page_num in self.replaced_text_areas:
            del self.replaced_text_areas[page_num]

    def clear_all_edits(self):
        """Efface toutes les modifications"""
        self.hidden_text_areas.clear()
        self.replaced_text_areas.clear()
