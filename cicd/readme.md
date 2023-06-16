# Deploying - Current Status - Manual

To deploy the listener atm requires manually running the helm chart, to deploy
the image that is getting built in the github action.

## Steps:

1. create a PR to build the image

2. grab the image tag from ghcr and update the values.yaml parameter for `image_tag` and `promote`

3. populate the environment variables:
    `set -o allexport; source .env; set +o allexport`

3. deploy the helm chart:

```bash
cd cicd
helm upgrade --install \
--set github_secrets.access_token=$GH_TOKEN \
message-queue \
message-queue
```

# Docker Debug Notes

Build image
`docker build -t listener:listener .`

Run container

`docker run --env-file=.env -v /home/kjnether/rfc_proj/cmc_cansip/data:/data  -p 8080:8080 listener:listener`


# Debugging Openshift

In the debugging folder `./cicd/debugging` there is a pod definition that can be
used to setup a simple pod that has mounted the PVC.  Once logged into that pod
you can pull the data down with the following commands:

``` bash
# deploy the pod
oc create -f ./debug_pod.yaml

# login to pod
oc rsh volume-debugger

# get the database
oc rsync volume-debugger:/data/event_database.db $PWD/
```

# Debugging Remote Call to downstream Job (gha - webhook)

The following is an example that makes a webhook call to the github action
test_remote_action_dispatch.yaml

```
curl -H "Accept: application/vnd.github.everest-preview+json" \
    -H "Authorization: token $GH_TOKEN" \
    --request POST \
    --data '{"event_type": "do-something", "client_payload": {"message": "bar", "idem_key": "20210601"}}' \
    https://api.github.com/repos/$GH_ORG/$GH_REPO/dispatches
```
