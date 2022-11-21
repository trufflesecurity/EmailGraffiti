#! /usr/bin/env python3
# ~*~ utf-8 ~*~

import mailbox
import json
import bs4
from urllib.parse import urlparse
from threading import Thread
from queue import Queue
import sys
import http.client as httplib
import requests
import aiohttp
import time
import asyncio
from aiohttp import ClientSession

image_urls = []
url_set = set()

def get_html_text(html, from_address, subject, date):
    html = "\n".join(html.splitlines())
    html = html.replace("=\n", "")
    html = html.replace("=\n", "")
    html = html.replace("%3D\n", "")
    html = html.replace("3D\n", "")
    html = html.replace("=20\n", "\n")
    try:
        parsed = bs4.BeautifulSoup(html, 'lxml')
        img_tags = parsed.find_all('img')
        for img in img_tags:
            try:
                if "http" in img['src']:
                    image_url = img['src']
                    if image_url.startswith("3D\""):
                        image_url = image_url[3:]
                    if image_url.endswith("\""):
                        image_url = image_url[:-1]
                    if image_url not in url_set:
                        url_set.add(image_url)
                        image_urls.append({"url": image_url, "from": str(from_address), "subject": str(subject), "date": str(date)})
            except KeyError:
                pass
        return parsed.body.get_text(' ', strip=True)
    except AttributeError: # message contents empty
        return None

class GmailMboxMessage():
    def __init__(self, email_data):
        if not isinstance(email_data, mailbox.mboxMessage):
            raise TypeError('Variable must be type mailbox.mboxMessage')
        self.email_data = email_data

    def parse_email(self):
        email_labels = self.email_data['X-Gmail-Labels']
        email_date = self.email_data['Date']
        email_from = self.email_data['From']
        email_to = self.email_data['To']
        email_subject = self.email_data['Subject']
        email_text = self.read_email_payload()
        return email_text

    def read_email_payload(self):
        email_payload = self.email_data.get_payload()
        if self.email_data.is_multipart():
            email_messages = list(self._get_email_messages(email_payload))
        else:
            email_messages = [email_payload]
        return [self._read_email_text(msg) for msg in email_messages]

    def _get_email_messages(self, email_payload):
        for msg in email_payload:
            if isinstance(msg, (list,tuple)):
                for submsg in self._get_email_messages(msg):
                    yield submsg
            elif msg.is_multipart():
                for submsg in self._get_email_messages(msg.get_payload()):
                    yield submsg
            else:
                yield msg

    def _read_email_text(self, msg):
        content_type = 'NA' if isinstance(msg, str) else msg.get_content_type()
        encoding = 'NA' if isinstance(msg, str) else msg.get('Content-Transfer-Encoding', 'NA')
        if 'text/plain' in content_type and 'base64' not in encoding:
            msg_text = msg.get_payload()
        elif 'text/html' in content_type and 'base64' not in encoding:
            msg_text = get_html_text(msg.get_payload(), self.email_data['From'], self.email_data['Subject'], self.email_data['Date'])
        elif content_type == 'NA':
            msg_text = get_html_text(msg, self.email_data['From'], self.email_data['Subject'], self.email_data['Date'])

        else:
            msg_text = None
        return (content_type, encoding, msg_text)

######################### End of library, example of use below

print("loading your emails")
try:
    mbox_obj = mailbox.mbox('mail.mbox')
except:
    print("Error loading your emails, make sure mail.mbox is in the working directory")
    sys.exit()
print("loaded your emails")
print("number of records: {}".format("???"))

for idx, email_obj in enumerate(mbox_obj):
    email_data = GmailMboxMessage(email_obj)
    result = email_data.parse_email()
    print('Parsing images from email {0}'.format(idx))
with open("all_urls", "w+") as f:
    f.write(json.dumps(image_urls, indent=4))

print("Writing all image URLS to all_urls file")

with open("all_urls", "r") as f:
    urls = json.loads(f.read())

abandonded = []
print("{} images found, checking them now...".format(len(urls)))
count = 0
for image in urls:
    url = image["url"]
    count += 1
    if url.startswith("3D\""):
        url = url[3:]
    if url.startswith("3D"):
        url = url[2:]
    if url.endswith("\""):
        url = url[:-1]
    image["url"] = url

services = {
    'AWS/S3': {'error': b'The specified bucket does not exist<'},
    'GCP/GCS': {'error': b'The specified bucket does not exist.'},
    'BitBucket': {'error': b'Repository not found'},
    'Github': {'error': b'There isn\\\'t a Github Pages site here\.'},
    'Shopify': {'error': b'Sorry\, this shop is currently unavailable\.'},
    'Fastly': {'error': b'Fastly error\: unknown domain\:'},

    'Ghost': {'error': b'The thing you were looking for is no longer here\, or never was'},
    'Heroku': {'error': b'no-such-app.html|<title>no such app</title>|herokucdn.com/error-pages/no-such-app.html'},
    'Pantheon': {'error': b'The gods are wise, but do not know of the site which you seek.'},
    'Tumbler': {'error': b'Whatever you were looking for doesn\\\'t currently exist at this address.'},
    'Wordpress': {'error': b'Do you want to register'},

    'TeamWork': {'error': b'Oops - We didn\'t find your site.'},
    'Helpjuice': {'error': b'We could not find what you\'re looking for.'},
    'Helpscout': {'error': b'No settings were found for this company:'},
    'Cargo': {'error': b'<title>404 &mdash; File not found</title>'},
    'Uservoice': {'error': b'This UserVoice subdomain is currently available!'},
    'Surge': {'error': b'project not found'},
    'Intercom': {'error': b'This page is reserved for artistic dogs\.|Uh oh\. That page doesn\'t exist</h1>'},

    'Webflow': {'error': b'<p class=\"description\">The page you are looking for doesn\'t exist or has been moved.</p>'},
    'Tave': {'error': b'<h1>Error 404: Page Not Found</h1>'},

    'Wishpond': {'error': b'<h1>https://www.wishpond.com/404?campaign=true'},
    'Aftership': {'error': b'Oops.</h2><p class=\"text-muted text-tight\">The page you\'re looking for doesn\'t exist.'},
    'Aha': {'error': b'There is no portal here \.\.\. sending you back to Aha!'},
    'Tictail': {'error': b'to target URL: <a href=\"https://tictail.com|Start selling on Tictail.'},
    'Brightcove': {'error': b'<p class=\"bc-gallery-error-code\">Error Code: 404</p>'},
    'Bigcartel': {'error': b'<h1>Oops! We couldn&#8217;t find that page.</h1>'},
    'ActiveCampaign': {'error': b'alt=\"LIGHTTPD - fly light.\"'},

    'Campaignmonitor': {'error': b'Double check the URL or <a href=\"mailto:help@createsend.com'},
    'Acquia': {'error': b'The site you are looking for could not be found.|If you are an Acquia Cloud customer and expect to see your site at this address'},
    'Proposify': {'error': b'If you need immediate assistance, please contact <a href=\"mailto:support@proposify.biz'},
    'Simplebooklet': {'error': b'We can\'t find this <a href=\"https://simplebooklet.com'},
    'GetResponse': {'error': b'With GetResponse Landing Pages, lead generation has never been easier'},
    'Vend': {'error': b'Looks like you\'ve traveled too far into cyberspace.'},
    'Jetbrains': {'error': b'is not a registered InCloud YouTrack.'},

    'Smartling': {'error': b'Domain is not configured'},
    'Pingdom': {'error': b'pingdom'},
    'Tilda': {'error': b'Domain has been assigned'},
    'Surveygizmo': {'error': b'data-html-name'},
    'Mashery': {'error': b'Unrecognized domain <strong>'},
    'Divio': {'error': b'Application not responding'},
    'feedpress': {'error': b'The feed has not been found.'},
    'readme': {'error': b'Project doesnt exist... yet!'},
    'statuspage': {'error': b'You are being <a href=\'https>'},
    'zendesk': {'error': b'Help Center Closed'},
    'worksites.net': {'error': b'Hello! Sorry, but the webs>'}
}


def doSomethingWithRes(res, image):
#    if res == "error":
#        return None
#    if res.status_code == 404:
    body = res
    for service in services:
        if services[service]["error"] in body:
            print("~~~~~\nFound an image you can takeover! \nFrom: {}\nSubject {}\nDate: {}Image URL: {}\nService: {}\n~~~~~".format(image["from"], image["subject"], image["date"], image["url"], service))


#!/usr/local/bin/python3.5
async def fetch(image, session):
    try:
        async with session.get(image["url"]) as response:
            if response.status == 404:
                doSomethingWithRes(await response.read(), image)

    except (aiohttp.client_exceptions.ClientOSError, aiohttp.client_exceptions.ServerDisconnectedError, ValueError, aiohttp.client_exceptions.ClientResponseError, aiohttp.client_exceptions.TooManyRedirects, UnicodeDecodeError, asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.InvalidURL, aiohttp.client_exceptions.ClientConnectorError, TimeoutError):
        pass
async def run():
    tasks = []

    # Fetch all responses within one Client session,
    # keep connection alive for all requests.
    async with ClientSession() as session:
        count = 0
        for image in urls:
            count += 1
            task = asyncio.ensure_future(fetch(image, session))
            tasks.append(task)

        await asyncio.gather(*tasks)
        # you now have all response bodies in this variable

loop = asyncio.get_event_loop()
future = asyncio.ensure_future(run())
loop.run_until_complete(future)
print("Finished checking!")
