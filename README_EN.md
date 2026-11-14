# WoW guild sign-up bot for Discord

**[Versione italiana → README.md](README.md)**

A Discord bot that handles new player sign-ups for a World of Warcraft guild. You install it on
your own server, with your own bot and your own hosting: nobody hosts anything for you.
Italian is the default language: set the variable `LANGUAGE=en` for English.

## How it works
1. A newcomer reads the rules in the sign-up channel and presses the green button.
2. They fill in a form: character name, class, how they found you, a funny WoW story, notes.
3. The request arrives in the `requests` channel: the GM or any officer approves or rejects it.
4. If approved: the player gets the member role and the card moves to `to-invite` (officers are pinged).
5. An officer invites them in game and presses "Invited": the card disappears and the player gets a message.
6. The `signup-log` channel keeps every step, including the full application.

## What you need
- A Discord server where you are an administrator.
- A GitHub account and a service that keeps the bot running 24/7 (for example Railway, about 5 dollars a month).
- A persistent volume mounted on `/data`, otherwise requests are lost at every restart.

## Setup
1. **Create the bot.** At https://discord.com/developers/applications click New Application, then Bot. Copy the **token** (keep it secret: never paste it in chats, posts or shared files). Leave the "Privileged Gateway Intents" off.
2. **Invite the bot.** In OAuth2 -> URL Generator choose the scopes `bot` and `applications.commands`. Permissions: View Channels, Send Messages, Embed Links, Read Message History, Manage Roles. Open the generated link and pick your server.
3. **Create channels and roles.** Channels: `sign-up` (visible to everyone, nobody can write), `requests` and `to-invite` (officers only), `signup-log` (officers only). A role for approved members (default `member`) and an officer role (default `officer`). The bot's role must be **above** the approved-members role. In restricted channels give the bot explicit permissions (view, send, embed links, read history, and "Mention everyone, here and all roles" in `to-invite` for the officer ping).
4. **Put the code online.** Upload these files to a **private** GitHub repository of yours and connect it to your hosting. Start command: `python bot.py` (or use the `Procfile`).
5. **Set the variables** (see `.env.example`): `DISCORD_TOKEN` and `ADMIN_ID` are required, `LANGUAGE=en` selects English. `ADMIN_ID` is your user ID (Discord -> Settings -> Advanced -> Developer Mode, then right-click your name -> Copy User ID).
6. **Post the message.** In the sign-up channel type `/setup_signup`: intro, rules and button appear.

## Customize
- Edit the rules in `regolamento.py` (English text: `SEZIONI_EN`).
- Channel and role names, classes and sources are set with environment variables (see `.env.example`). Names are matched partially, so `requests` also finds `📩・requests`.
- Another language? Copy the dictionary in `lingua.py` and translate the values.

## Commands (only for the administrator set in ADMIN_ID)
In English mode: `/setup_signup`, `/publish_rules`, `/reset_requests user`. In Italian mode: `/setup_iscrizione`, `/pubblica_regolamento`, `/azzera_richieste utente`.

## Data and privacy
The bot stores the character name, Discord ID and the texts typed by users in a database on your hosting.
You are responsible for this data: tell your players and delete it on request.

## License and warranty
Use and modify it freely. No warranty: you install and run it yourself.
