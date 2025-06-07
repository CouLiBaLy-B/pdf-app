"""
Service pour les annotations PDF
"""

import fitz
from config.settings import COLORS


class AnnotationService:
    def __init__(self, pdf_manager):
        self.pdf_manager = pdf_manager

    def add_highlight(self, rect, color):
        """Ajoute un surlignage"""
        if not self.pdf_manager.pdf_document:
            raise Exception("Aucun PDF chargé")

        page = self.pdf_manager.get_page()
        if not page:
            raise Exception("Page invalide")

        highlight = page.add_highlight_annot(rect)
        color_rgb = COLORS.get(color, (1, 1, 0))
        highlight.set_colors(stroke=color_rgb)
        highlight.update()

    def add_note(self, content, x=100, y=100):
        """Ajoute une annotation note"""
        if not self.pdf_manager.pdf_document:
            raise Exception("Aucun PDF chargé")

        page = self.pdf_manager.get_page()
        if not page:
            raise Exception("Page invalide")

        rect = fitz.Rect(x, y, x + 50, y + 50)
        annot = page.add_text_annot(rect.tl, content)
        annot.set_info(content=content)
        annot.update()
