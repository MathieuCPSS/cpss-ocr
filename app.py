import os
import base64
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from paddleocr import PaddleOCR

app = Flask(__name__)
CORS(app)  # Autorise les requêtes depuis devis.html

# Initialiser PaddleOCR une seule fois au démarrage
# use_angle_cls=True : détecte les textes inclinés
# lang='en' : anglais pour les devis britanniques
ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'ok': True})

@app.route('/ocr', methods=['POST'])
def do_ocr():
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'Champ "image" manquant (base64)'}), 400

        # Décoder l'image base64
        image_data = base64.b64decode(data['image'])

        # Sauvegarder temporairement
        suffix = '.png'
        if data.get('type', '').endswith('jpeg') or data.get('type', '').endswith('jpg'):
            suffix = '.jpg'

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(image_data)
            tmp_path = tmp.name

        try:
            # Lancer OCR
            result = ocr.ocr(tmp_path, cls=True)

            # Reconstruire le texte en respectant la structure des lignes
            # PaddleOCR retourne : [[[box], (text, confidence)], ...]
            lines = []
            if result and result[0]:
                # Trier par position Y (haut → bas) puis X (gauche → droite)
                items = []
                for line in result[0]:
                    box = line[0]
                    text = line[1][0]
                    conf = line[1][1]
                    # Centre Y de la boîte
                    y_center = sum(p[1] for p in box) / 4
                    x_left = min(p[0] for p in box)
                    items.append({'text': text, 'y': y_center, 'x': x_left, 'conf': conf})

                # Grouper par lignes (même Y ± 8px)
                items.sort(key=lambda i: i['y'])
                grouped = []
                current_line = []
                current_y = None

                for item in items:
                    if current_y is None or abs(item['y'] - current_y) <= 8:
                        current_line.append(item)
                        current_y = item['y'] if current_y is None else (current_y + item['y']) / 2
                    else:
                        if current_line:
                            grouped.append(sorted(current_line, key=lambda i: i['x']))
                        current_line = [item]
                        current_y = item['y']

                if current_line:
                    grouped.append(sorted(current_line, key=lambda i: i['x']))

                # Construire le texte avec tabulations entre colonnes
                for line_items in grouped:
                    line_text = '\t'.join(item['text'] for item in line_items)
                    lines.append(line_text)

            texte = '\n'.join(lines)
            return jsonify({'texte': texte, 'lignes': len(lines)})

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
