# Docker Debug Notes

Build image
`docker build -t listener:listener .`

Run container

`docker run --env-file=.env -v /home/kjnether/rfc_proj/cmc_cansip/data:/data  -p 8080:8080 listener:listener`


