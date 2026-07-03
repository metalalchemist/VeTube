# VeTube and Discord: step-by-step guide

VeTube can read the messages of a text channel on a Discord server in real time. To do this the official way, Discord requires a "bot": a special account you create yourself for free, once, in about 10 minutes. This guide walks you through the whole process and is written for screen reader users (no screenshots, exact names for every button).

Note: the Discord developer portal is only available in English. The Discord chat application itself is translated.

## What you need
- A Discord account.
- Permission to invite bots to the server you want to read (the "Manage Server" permission). If you don't have it, at the end of step 4 you can send the invite link to an administrator so they open it for you.

## Step 1: create the application
1. Open https://discord.com/developers/applications and sign in.
2. Press the "New Application" button.
3. Type a name (for example "VeTube"), accept the terms and press "Create".

## Step 2: get the bot token
1. On your application's page, go to the "Bot" section in the left menu.
2. Press the "Reset Token" button and confirm with "Yes, do it!". If you have two-factor authentication, you will be asked for the code.
3. The new token appears with a "Copy" button to copy it to the clipboard. Paste it temporarily somewhere safe, for example Notepad.

Important: the token is like your bot's password. Do not share it or publish it anywhere. If it leaks, come back to this page and press "Reset Token" to generate a new one; the old one stops working.

## Step 3: enable "Message Content Intent"
Without this option, Discord does not let the bot read the content of messages.
1. Still in the "Bot" section, scroll down to "Privileged Gateway Intents".
2. Turn on the "Message Content Intent" switch.
3. Press "Save Changes" in the bar that appears.

## Step 4: invite the bot to your server
1. Go to the "OAuth2" section in the left menu and find "URL Generator".
2. In the "Scopes" list, check the "bot" checkbox.
3. In "Bot Permissions", which appears below, check "View Channels" and "Read Message History".
4. At the bottom of the page, in "Generated URL", press "Copy".
5. Open that URL in your browser, pick the server in the combo box and press "Continue" then "Authorize". (If you are not allowed to invite bots, send that URL to a server administrator.)

## Step 5: copy the channel link
1. In Discord, find the text channel you want to read.
2. Open its context menu: right click, or the Applications key or Shift+F10 with a screen reader.
3. Choose "Copy Link". The link looks like this: https://discord.com/channels/1234567890/0987654321

## Step 6: paste into VeTube
1. Open VeTube, paste the channel link into the main text box and press "Access" or Enter.
2. The first time, VeTube will ask for the bot token: paste it and press "OK". It will be saved and you won't be asked again.
3. Done! Channel messages start arriving. Messages from the server owner and from people who can moderate appear in the "Moderators" category; everything else goes to "General".

## Troubleshooting
- "The token is not valid": copy the full token from the portal (step 2). When in doubt, generate a new one with "Reset Token".
- "The bot is missing the Message Content Intent option": go over step 3 again and save the changes.
- "Discord channel not found": check that the bot was invited to that exact server (step 4) and that you copied the link of the right channel (step 5).
- The chat connects but no messages arrive: make sure the bot can see that channel. For private channels you must grant it access or a role that has it.
