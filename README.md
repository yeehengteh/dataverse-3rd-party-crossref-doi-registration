# Dataverse 3rd-Party Crossref DOI Registration Plugin

## Dependencies
Install required packages.
```
pip install jinja2 crossrefapi python-dotenv
```

## Prerequisite
### Clone this repository
```
git clone https://github.com/yeehengteh/dataverse-3rd-party-crossref-doi-registration.git doi
```
### Create and edit .env
```
cd doi
cp .env.example .env
vi .env
```
### Create systemd file
```
cp doi.service /etc/systemd/system
```
### Make sure service user exists
If the user, dataverse do not exists, you can either choose to create or change the service user to an existing user in the doi.service
### Reload systemd
```
systemctl daemon-reload
```

## Running the script
```
systemctl enable --now doi
```
