FROM python:3.11-slim

WORKDIR /app/webui

COPY requirements.txt /app/webui/

RUN pip install --upgrade pip && pip install -r /app/webui/requirements.txt

COPY . /app/webui/

EXPOSE 8501

CMD ["streamlit", "run", "webui.py", "--server.port=8501", "--server.address=0.0.0.0"]
