# OPSE - GHunt Plugin

✅ Not yet certified plugin for [OPSE-Framework](https://github.com/OPSE-Developers/OPSE-Framework)

OPSE Framework is a plugin oriented tool that allow a user to perform an open-source research to gather intelligence on a target.

This plugin perform a [GHunt](https://github.com/mxrch/GHunt) research to retrieve data on the target from a google email address.

# Installation

You'll need to follow the instruction for installing ghunt as described on the [official page](https://github.com/mxrch/GHunt). Here a quick recap :

```bash
$ pip3 install pipx
$ pipx ensurepath
$ pipx install ghunt
```

You will need to authentificate ghunt before using the module : use GHunt Companion to complete the login.

The extension is available on the following stores :\
\
[![Firefox](https://files.catbox.moe/5g2ld5.png)](https://addons.mozilla.org/en-US/firefox/addon/ghunt-companion/)&nbsp;&nbsp;&nbsp;[![Chrome](https://storage.googleapis.com/web-dev-uploads/image/WlD8wC6g8khYWPJUsQceQkhXSlv1/UV4C4ybeBTsZt43U4xis.png)](https://chrome.google.com/webstore/detail/ghunt-companion/dpdcofblfbmmnikcbmmiakkclocadjab)

Then run 
```bash
$ ghunt login
```
and authentificate using the token retrieved via the browser add-on.

Enjoy.