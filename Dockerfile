FROM python:3-alpine
RUN apk add --update --no-cache g++ gcc libxslt-dev 
COPY requirements.txt .
RUN pip install -r requirements.txt
WORKDIR /mailbox
COPY checkMyOldEmails.py .
ENTRYPOINT ["python", "checkMyOldEmails.py"]
