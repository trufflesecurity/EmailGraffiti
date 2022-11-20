from python:alpine
copy requirements.txt .
run pip install -r requirements.txt
workdir /mailbox
copy checkMyOldEmails.py .
cmd ["python", "checkMyOldEmails.py"]
