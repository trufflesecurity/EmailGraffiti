# EmailGraffiti
Vandalize old emails by taking over images that point to unclaimed resources, kind of like an NFT that's easy to prove ownership of

## How to get started
Start by downloading the email you want to check in mbox format. In Gmail you can do that [here](https://takeout.google.com/?pli=1)

*Note: It's super sketchy to run someone's random skript on all your old email, so maybe review the code first ;)*

Place your export in your current working directory.

### Build the docker container:
```bash
docker build -t emailgraffiti .
```

### Run the docker container to find email images you can Graffiti over

```
docker run --rm -it -v $PWD/:/mailbox emailgraffiti
```

That's it! You should start seeing some images you can take over in your email :)
