FROM python:3.10
COPY updater.py /updater.py
COPY utils /utils
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
RUN chmod +x /updater.py
CMD ["python", "-u", "updater.py"]