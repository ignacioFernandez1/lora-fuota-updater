FROM python:3.10
COPY updater.py /updater.py
COPY entrypoint.sh /entrypoint.sh
COPY utils /utils
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
RUN chmod +x /updater.py
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]