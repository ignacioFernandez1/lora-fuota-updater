FROM python:3.10
COPY updater.py /updater.py
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
RUN chmod +x /updater.py
ENTRYPOINT ["/updater.py"]