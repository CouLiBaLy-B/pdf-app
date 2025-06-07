"""
Service pour les opérations sur le texte
"""

from config.settings import COLORS


class TextService:
    def __init__(self, pdf_manager):
        self.pdf_manager = pdf_manager

    def add_text(self, text, x, y, font_size, color):
        """Ajoute du texte à la position spécifiée"""
        if not self.pdf_manager.pdf_document:
            raise Exception("Aucun PDF chargé")

        page = self.pdf_manager.get_page()
        if not page:
            raise Exception("Page invalide")

        color_rgb = COLORS.get(color, (0, 0, 0))
        page.insert_text((x, y), text, fontsize=font_size, color=color_rgb)

    def delete_text(self, selection):
        """Supprime le texte sélectionné"""
        if not self.pdf_manager.pdf_document:
            raise Exception("Aucun PDF chargé")

        page = self.pdf_manager.pdf_document[selection["page"]]
        rect = selection["rect"]

        # Dessiner un rectangle blanc pour "effacer" le texte
        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

    def replace_text(self, selection, new_text, font_size, color):
        """Remplace le texte sélectionné"""
        if not self.pdf_manager.pdf_document:
            raise Exception("Aucun PDF chargé")

        page = self.pdf_manager.pdf_document[selection["page"]]
        rect = selection["rect"]

        # Effacer l'ancien texte
        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

        # Ajouter le nouveau texte
        color_rgb = COLORS.get(color, (0, 0, 0))
        page.insert_text(
            (rect.x0, rect.y1 - 2), new_text, fontsize=font_size, color=color_rgb
        )

    def format_text(self, selection, font_size, color):
        """Applique un formatage au texte sélectionné"""
        if not self.pdf_manager.pdf_document:
            raise Exception("Aucun PDF chargé")

        page = self.pdf_manager.pdf_document[selection["page"]]
        rect = selection["rect"]
        text = selection["text"]

        # Effacer l'ancien texte
        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

        # Ajouter le texte avec le nouveau formatage
        color_rgb = COLORS.get(color, (0, 0, 0))
        page.insert_text(
            (rect.x0, rect.y1 - 2), text, fontsize=font_size, color=color_rgb
        )

    def extract_page_text(self, page_num):
        """Extrait le texte d'une page"""
        if not self.pdf_manager.pdf_document:
            raise Exception("Aucun PDF chargé")

        page = self.pdf_manager.pdf_document[page_num]
        return page.get_text()

    def extract_all_text(self):
        """Extrait le texte de tout le PDF"""
        if not self.pdf_manager.pdf_document:
            raise Exception("Aucun PDF chargé")

        all_text = ""
        for page_num in range(len(self.pdf_manager.pdf_document)):
            page = self.pdf_manager.pdf_document[page_num]
            text = page.get_text()
            all_text += f"--- Page {page_num + 1} ---\n{text}\n\n"

        return all_text
