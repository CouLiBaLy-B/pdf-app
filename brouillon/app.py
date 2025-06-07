import os
import uuid
from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ALLOWED_EXTENSIONS"] = {"pdf"}
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

# Créer les dossiers nécessaires
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return render_template("index.html", error="Aucun fichier sélectionné")

        file = request.files["file"]

        if file.filename == "":
            return render_template("index.html", error="Aucun fichier sélectionné")

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())
            temp_filename = f"{unique_id}_{filename}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], temp_filename)
            file.save(filepath)

            try:
                # Lire les métadonnées et le contenu
                doc = fitz.open(filepath)
                metadata = doc.metadata
                page_count = doc.page_count
                content = ""

                # Extraire le texte de la première page à titre d'exemple
                if page_count > 0:
                    page = doc.load_page(0)
                    content = page.get_text()

                doc.close()
                return render_template(
                    "index.html",
                    metadata=metadata,
                    content=content,
                    temp_file=temp_filename,
                    filename=filename,
                    page_count=page_count,
                )
            except Exception as e:
                return render_template(
                    "index.html", error=f"Erreur de lecture: {str(e)}"
                )
        else:
            return render_template("index.html", error="Format de fichier non supporté")

    return render_template("index.html")


@app.route("/update", methods=["POST"])
def update_pdf():
    temp_file = request.form["temp_file"]
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], temp_file)

    if not os.path.exists(filepath):
        return render_template("index.html", error="Fichier introuvable")

    try:
        # Traitement des métadonnées
        new_metadata = {
            "author": request.form.get("author", ""),
            "title": request.form.get("title", ""),
            "subject": request.form.get("subject", ""),
            "keywords": request.form.get("keywords", ""),
        }

        # Traitement des modifications de contenu
        content_modifications = {
            "text": request.form.get("new_text", ""),
            "page": int(request.form.get("page_number", 0)),
            "x": float(request.form.get("pos_x", 50)),
            "y": float(request.form.get("pos_y", 50)),
            "font_size": float(request.form.get("font_size", 12)),
        }

        # Ouvrir le PDF avec PyMuPDF pour les modifications de contenu
        doc = fitz.open(filepath)

        # Ajouter du texte si spécifié
        if content_modifications["text"]:
            page_num = min(content_modifications["page"], doc.page_count - 1)
            page = doc.load_page(page_num)

            # Calculer la position (coordonnées PDF: bas gauche = (0,0))
            height = page.rect.height
            y_position = height - content_modifications["y"]

            page.insert_text(
                (content_modifications["x"], y_position),
                content_modifications["text"],
                fontsize=content_modifications["font_size"],
                color=(0, 0, 0),  # Noir
            )

        # Appliquer les métadonnées
        doc.set_metadata(new_metadata)

        # Sauvegarder les modifications
        output_filename = f"modified_{temp_file}"
        output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_filename)
        doc.save(output_path)
        doc.close()

        # Envoyer le fichier modifié
        return send_file(
            output_path,
            as_attachment=True,
            download_name=request.form.get(
                "original_filename", "document_modified.pdf"
            ),
            mimetype="application/pdf",
        )

    except Exception as e:
        return render_template("index.html", error=f"Erreur de modification: {str(e)}")
    finally:
        # Nettoyage des fichiers temporaires
        if os.path.exists(filepath):
            os.remove(filepath)
        if "output_path" in locals() and os.path.exists(output_path):
            os.remove(output_path)


if __name__ == "__main__":
    app.run(debug=True)
