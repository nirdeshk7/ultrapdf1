from flask import Flask, request, send_file, jsonify, render_template
from PyPDF2 import PdfMerger
import os
import uuid
import subprocess
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__, template_folder='templates')

UPLOAD_FOLDER = 'uploads/'
CONVERTED_FOLDER = 'converted_pdfs/'
MERGED_FOLDER = 'temp_outputs/'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)
os.makedirs(MERGED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge', methods=['POST'])
def merge_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No files part in the request'}), 400

    files = request.files.getlist('files')

    if len(files) == 0:
        return jsonify({'error': 'No files selected for uploading'}), 400

    if len(files) > 500:
        return jsonify({'error': 'Maximum 500 files allowed'}), 400

    merger = PdfMerger()
    saved_files = []

    try:
        for file in files:
            filename = secure_filename(file.filename)
            file_ext = filename.lower().split('.')[-1]
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            if file_ext in ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']:
                subprocess.run([
                    'libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', CONVERTED_FOLDER, filepath
                ], check=True)
                output_pdf = os.path.join(CONVERTED_FOLDER, filename.rsplit('.', 1)[0] + '.pdf')
                merger.append(output_pdf)
                saved_files.append(filepath)
                saved_files.append(output_pdf)
            elif file_ext in ['jpg', 'jpeg', 'png']:
                output_pdf = os.path.join(CONVERTED_FOLDER, filename.rsplit('.', 1)[0] + '.pdf')
                image = Image.open(filepath)
                image.convert('RGB').save(output_pdf)
                merger.append(output_pdf)
                saved_files.append(filepath)
                saved_files.append(output_pdf)
            elif file_ext == 'pdf':
                merger.append(filepath)
                saved_files.append(filepath)
            else:
                return jsonify({'error': f'Unsupported file type: {filename}'}), 400

        unique_filename = f'merged_{uuid.uuid4().hex}.pdf'
        output_pdf_path = os.path.join(MERGED_FOLDER, unique_filename)
        merger.write(output_pdf_path)
        merger.close()

        compressed_output_path = os.path.join(MERGED_FOLDER, f'compressed_{unique_filename}')
        gs_command = [
            'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
            '-dPDFSETTINGS=/ebook', '-dNOPAUSE', '-dBATCH', '-dQUIET',
            f'-sOutputFile={compressed_output_path}', output_pdf_path
        ]
        subprocess.run(gs_command, check=True)

        for file_path in saved_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        if os.path.exists(output_pdf_path):
            os.remove(output_pdf_path)

        return send_file(compressed_output_path, as_attachment=True)

    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
