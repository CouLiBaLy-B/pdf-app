"""
Onglet pour la manipulation de PDF (extraction, fusion, rotation)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import PyPDF2
import os
from utils.helpers import parse_page_ranges, validate_page_numbers


class ManipulationTab:
    def __init__(self, notebook, pdf_manager):
        self.notebook = notebook
        self.pdf_manager = pdf_manager

        # Variables
        self.extract_pages_var = tk.StringVar()
        self.rotate_pages_var = tk.StringVar()
        self.rotate_angle_var = tk.StringVar(value="90")
        self.merge_files = []

        self.create_tab()

    def create_tab(self):
        """Crée l'onglet manipulation"""
        self.manip_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.manip_frame, text="Manipulation PDF")

        self.create_extraction_section()
        self.create_merge_section()
        self.create_rotation_section()

    def create_extraction_section(self):
        """Section extraction de pages"""
        extract_frame = ttk.LabelFrame(
            self.manip_frame, text="Extraction de pages", padding="10"
        )
        extract_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(extract_frame, text="Pages à extraire (ex: 1,3,5-7):").pack(
            anchor="w"
        )
        ttk.Entry(extract_frame, textvariable=self.extract_pages_var, width=30).pack(
            anchor="w", pady=2
        )
        ttk.Button(
            extract_frame, text="Extraire pages", command=self.extract_pages
        ).pack(anchor="w", pady=5)

    def create_merge_section(self):
        """Section fusion de PDF"""
        merge_frame = ttk.LabelFrame(
            self.manip_frame, text="Fusion de PDF", padding="10"
        )
        merge_frame.pack(fill="x", padx=10, pady=5)

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

    def create_rotation_section(self):
        """Section rotation de pages"""
        rotate_frame = ttk.LabelFrame(
            self.manip_frame, text="Rotation de pages", padding="10"
        )
        rotate_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(rotate_frame, text="Pages à faire tourner (ex: 1,3,5-7):").pack(
            anchor="w"
        )
        ttk.Entry(rotate_frame, textvariable=self.rotate_pages_var, width=30).pack(
            anchor="w", pady=2
        )

        rotate_options = ttk.Frame(rotate_frame)
        rotate_options.pack(anchor="w", pady=2)
        ttk.Label(rotate_options, text="Angle:").pack(side="left")
        ttk.Combobox(
            rotate_options,
            textvariable=self.rotate_angle_var,
            values=["90", "180", "270"],
            width=10,
        ).pack(side="left", padx=5)
        ttk.Button(
            rotate_options, text="Appliquer rotation", command=self.rotate_pages
        ).pack(side="left", padx=5)

    def extract_pages(self):
        """Extrait les pages spécifiées"""
        if not self.pdf_manager.current_path:
            messagebox.showwarning("Attention", "Aucun fichier PDF sélectionné")
            return

        pages_input = self.extract_pages_var.get().strip()
        if not pages_input:
            messagebox.showwarning(
                "Attention", "Veuillez spécifier les pages à extraire"
            )
            return

        try:
            pages_to_extract = parse_page_ranges(pages_input)
            max_pages = self.pdf_manager.total_pages

            valid, invalid_pages = validate_page_numbers(pages_to_extract, max_pages)
            if not valid:
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
                with open(self.pdf_manager.current_path, "rb") as input_file:
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
        """Ajoute des fichiers à fusionner"""
        files = filedialog.askopenfilenames(
            title="Sélectionner des fichiers PDF à fusionner",
            filetypes=[("Fichiers PDF", "*.pdf")],
        )

        for file_path in files:
            if file_path not in self.merge_files:
                self.merge_files.append(file_path)
                self.merge_listbox.insert(tk.END, os.path.basename(file_path))

    def remove_merge_file(self):
        """Supprime un fichier de la liste de fusion"""
        selection = self.merge_listbox.curselection()
        if selection:
            index = selection[0]
            self.merge_listbox.delete(index)
            del self.merge_files[index]

    def merge_pdfs(self):
        """Fusionne les PDF sélectionnés"""
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
        """Applique une rotation aux pages spécifiées"""
        if not self.pdf_manager.current_path:
            messagebox.showwarning("Attention", "Aucun fichier PDF sélectionné")
            return

        pages_input = self.rotate_pages_var.get().strip()
        if not pages_input:
            messagebox.showwarning(
                "Attention", "Veuillez spécifier les pages à faire tourner"
            )
            return

        try:
            pages_to_rotate = parse_page_ranges(pages_input)
            angle = int(self.rotate_angle_var.get())
            max_pages = self.pdf_manager.total_pages

            valid, invalid_pages = validate_page_numbers(pages_to_rotate, max_pages)
            if not valid:
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
                with open(self.pdf_manager.current_path, "rb") as input_file:
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

    def on_pdf_loaded(self):
        """Appelé quand un nouveau PDF est chargé"""
        pass  # Rien de spécial à faire pour cet onglet

    def reset(self):
        """Réinitialise l'onglet"""
        self.extract_pages_var.set("")
        self.rotate_pages_var.set("")
        self.rotate_angle_var.set("90")
        self.merge_files.clear()
        self.merge_listbox.delete(0, tk.END)
