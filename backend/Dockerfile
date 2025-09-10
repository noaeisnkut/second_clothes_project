FROM python:3.11
WORKDIR /app
COPY requirements.txt .
COPY app_test.py .
COPY ../infra/wait-for-mysql.sh /app/infra/wait-for-mysql.sh
RUN chmod +x /app/infra/wait-for-mysql.sh
RUN pip install --upgrade pip
RUN pip install --upgrade Flask Flask-SQLAlchemy Werkzeug
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
