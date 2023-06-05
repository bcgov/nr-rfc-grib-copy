# Deploying - Current Status - Manual

To deploy the listener atm requires manually running the helm chart, to deploy
the image that is getting built in the github action.

## Steps:

1. create a PR to build the image

2. grab the image tag from ghcr and update the values.yaml parameter for image_tag and promote

3. deploy the helm chart:





# Docker Debug Notes

Build image
`docker build -t listener:listener .`

Run container

`docker run --env-file=.env -v /home/kjnether/rfc_proj/cmc_cansip/data:/data  -p 8080:8080 listener:listener`


