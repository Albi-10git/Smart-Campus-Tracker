FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_HOST=0.0.0.0
ENV PORT=5000
ENV ARDUINO_ENABLED=false

EXPOSE 5000

CMD ["python","app.py"] 
