# Dataverse 3rd-Party Crossref DOI Registration Plugin

## Dependencies
Install required packages.
```
pip install jinja2 crossrefapi python-dotenv
```

## Prerequisite
1. Fill in the .env file
2. Modify the `doi.service` accordingly and copy to `/etc/systemd/system`
3. Run `systemctl daemon-reload`

## Running the script
```
systemctl enable --now doi
```
