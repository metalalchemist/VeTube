# Reading TikTok from your browser: the local signer extension

This guide explains an alternative way to read a TikTok live chat in VeTube, meant for when the usual method fails. It's meant to be read top to bottom: first what it's for, then why it exists, how to install and use it, and finally the security notes.

## What it's for

To read a live chat, TikTok requires the request to the chat's *websocket* to be **signed**. VeTube normally asks an external service (EulerStream) to compute that signature. When that service goes down — which happens often — VeTube can't read the chat of **any** TikTok live through the usual route.

The extension solves exactly that: instead of depending on that external service, it lets **your own browser** — which already has the live open and is already receiving the chat over a signed, working connection — pass those messages to VeTube. The extension doesn't compute any new signature: it just copies the messages your browser is already receiving.

In one sentence: *VeTube reads over your browser's shoulder, since your browser is the one actually connected to TikTok.*

## Why it was created

There's no official API to read a TikTok live chat, so VeTube (and any similar program) depends on an external service to compute the signature TikTok requires. That service, EulerStream:

- goes down often (and while it's down, nobody can read any TikTok live that way),
- splits a limited quota among all its users,
- is a third party outside of VeTube.

Since the signature can't be skipped, the extension was built to solve this without depending on that third party: if your browser is already watching the live with a signed, working connection, there's no need to ask anyone else for a signature. It's an alternative, not a permanent replacement — it's meant to be used when the usual service fails.

## How to install it

The extension is **not on the Chrome Web Store**: it ships with VeTube, in the `interceptor_extension` folder. To install it, just once:

1. Open Chrome (or a Chromium-based browser, such as Edge or Brave) and go to `chrome://extensions`.
2. Turn on **"Developer mode"** (the toggle in the top right).
3. Click **"Load unpacked"** and select the `interceptor_extension` folder (it ships alongside VeTube).
4. Done: **"VeTube – TikTok Live chat bridge"** appears in the extensions list.

## How to use it

On VeTube's home screen, in the **"Capture chat from:"** dropdown, there are two options for TikTok: **"TikTok"** (the usual service) and **"TikTok (browser, experimental)"** (this extension). To use the extension directly:

1. Open the live in your browser (with the extension already installed). Chrome will show a bar saying *"… is debugging this browser"*: this is normal and means the extension is reading the chat. Don't close it.
2. In VeTube, type the **same username** as the live (the `@username`, exactly as it appears).
3. Choose **"TikTok (browser, experimental)"** in "Capture chat from:" and click **Connect**.

You can also let VeTube offer it to you automatically: if you pick the normal "TikTok" option and the usual connection fails, VeTube will ask whether you want to switch to reading from the browser (with the live already open there). If you accept, it keeps reading without restarting anything.

Requirements: the extension has to be loaded **before** you open the live (if it was already open, reload that tab), and don't have the developer tools (F12) open on that tab, since they use the same channel as the extension.

## Security notes

- **The extension only reads what your browser is already receiving.** It doesn't bypass any TikTok protection: the signature is still computed by TikTok, on your own session, as usual.
- **It never sends your session cookie** (`sessionid`) or any account credential. A public live's chat works the same without being logged in.
- **Everything stays on your computer.** The extension only talks to `127.0.0.1:8790` (VeTube, on your own machine); nothing is sent to any external server or third party.
- **It doesn't modify the TikTok page** or interfere with its security: it only observes the chat traffic, the same way the browser's developer tools would see it.

More technical detail (how the extension is built, the protocol it uses to talk to VeTube, and troubleshooting) is in `FIRMADOR_LOCAL.md` and `interceptor_extension/LEEME.md`, in VeTube's source code.
