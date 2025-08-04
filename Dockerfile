FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y libreoffice ghostscript && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads converted_pdfs temp_outputs templates

CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
