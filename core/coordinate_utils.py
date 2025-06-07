"""
Utilitaires pour la conversion de coordonnées
"""


class CoordinateConverter:
    def __init__(self, zoom_level=1.0):
        self.zoom_level = zoom_level

    def set_zoom(self, zoom_level):
        """Met à jour le niveau de zoom"""
        self.zoom_level = zoom_level

    def canvas_to_pdf(self, canvas_x, canvas_y):
        """Convertit les coordonnées canvas en coordonnées PDF"""
        pdf_x = canvas_x / self.zoom_level
        pdf_y = canvas_y / self.zoom_level
        return pdf_x, pdf_y

    def pdf_to_canvas(self, pdf_x, pdf_y):
        """Convertit les coordonnées PDF en coordonnées canvas"""
        canvas_x = pdf_x * self.zoom_level
        canvas_y = pdf_y * self.zoom_level
        return canvas_x, canvas_y
