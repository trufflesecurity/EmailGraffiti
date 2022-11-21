# EmailGraffiti
Vandalize old emails by taking over images that point to unclaimed resources, kind of like an NFT that's easy to prove ownership of.

![emailgraffiti](https://user-images.githubusercontent.com/3084554/203109995-e1cec5bb-82b3-46c0-99c7-d37b78cd7557.gif)

Checkout this full blog post to understand what's happening: [https://trufflesecurity.com/blog/email-graffiti](https://trufflesecurity.com/blog/email-graffiti)

## How to get started
Start by downloading the email you want to check in mbox format. In Gmail you can do that [here](https://takeout.google.com/?pli=1)

*Note: It's super sketchy to run someone's random skript on all your old email, so maybe review the code first ;)*

Place your export in your current working directory.

### Run the docker container to find email images you can Graffiti over

```
docker run --rm -it -v $PWD/:/pwd trufflesecurity/email-graffiti pwd/mail.mbox
```

You should start seeing some images you can take over in your email :)
<img width="849" alt="image" src="https://user-images.githubusercontent.com/3084554/202891858-066b01b2-41b2-4e0f-9894-cc2fa5c9615c.png">

## Now what?
Now that you've got the image and the service, you can go to that service and register the image as your own! 

For example, for S3 buckets, here's the name of the bucket:

https://s3-us-west-2.amazonaws.com/**bucketname**/imagename.jpg

Head on over to the [AWS console](https://s3.console.aws.amazon.com/s3/buckets?region=us-east-1), and register that bucket name:
<img width="1324" alt="image" src="https://user-images.githubusercontent.com/3084554/202891924-0f6b4f26-b5a4-4d81-bcd8-ebade1486c28.png">

Then just upload an image into the bucket that has the same name as the image found in your email. That's it!

## Animated images
Did you know if Chrome recieves a GIF from the server, it doesn't matter if the extension is `.jpeg` ? You can name any animated GIF after the png, jpeg or jpg of your choosing. Try it out! 
