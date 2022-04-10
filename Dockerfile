FROM python:latest
ADD core.py /
ADD requirements.txt /
RUN python3 -m pip install -r requirements.txt
CMD [ "python", "/core.py" ]