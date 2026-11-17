## Run a Claude PR lane in an isolated VM

ADDED (config keys): To opt in on an Apple silicon Mac, configure
`parallel.isolated_image_url` and `parallel.isolated_image_sha512` with a trusted
Linux arm64 image and its digest.

ADDED (engine CLI surface): Install Lima and configure the operator-only GitHub
update and deletion rules described in the headless lane workflow. From the trusted
cockpit, use `dev_session.sh isolated` with the prompt and the lane App signing key.
