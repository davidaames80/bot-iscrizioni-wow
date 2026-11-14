# WoW guild sign-up bot for Discord / Bot iscrizioni per gilde WoW

🇮🇹 [Italiano](#italiano) · 🇬🇧 [English](#english)

Free Discord bot for World of Warcraft guild sign-ups. You install it yourself, with your own bot and hosting. / Bot Discord gratuito per le iscrizioni nelle gilde di World of Warcraft. Lo installi tu, con il tuo bot e il tuo hosting.

## English

A Discord bot that handles new player sign-ups for a World of Warcraft guild. You install it on
your own server, with your own bot and your own hosting: nobody hosts anything for you.
Italian is the default language: set the variable `LANGUAGE=en` for English.

### How it works
1. A newcomer reads the rules in the sign-up channel and presses the green button.
2. They fill in a form: character name, class, how they found you, a funny WoW story, notes.
3. The request arrives in the `requests` channel: the GM or any officer approves or rejects it.
4. If approved: the player gets the member role and the card moves to `to-invite` (officers are pinged).
5. An officer invites them in game and presses "Invited": the card disappears and the player gets a message.
6. The `signup-log` channel keeps every step, including the full application.

### What you need
- A Discord server where you are an administrator.
- A GitHub account and a service that keeps the bot running 24/7 (for example Railway, about 5 dollars a month).
- A persistent volume mounted on `/data`, otherwise requests are lost at every restart.

### Setup
1. **Create the bot.** At https://discord.com/developers/applications click New Application, then Bot. Copy the **token** (keep it secret: never paste it in chats, posts or shared files). Leave the "Privileged Gateway Intents" off.
2. **Invite the bot.** In OAuth2 -> URL Generator choose the scopes `bot` and `applications.commands`. Permissions: View Channels, Send Messages, Embed Links, Read Message History, Manage Roles. Open the generated link and pick your server.
3. **Create channels and roles.** Channels: `sign-up` (visible to everyone, nobody can write), `requests` and `to-invite` (officers only), `signup-log` (officers only). A role for approved members (default `member`) and an officer role (default `officer`). The bot's role must be **above** the approved-members role. In restricted channels give the bot explicit permissions (view, send, embed links, read history, and "Mention everyone, here and all roles" in `to-invite` for the officer ping).
4. **Put the code online.** Upload these files to a **private** GitHub repository of yours and connect it to your hosting. Start command: `python bot.py` (or use the `Procfile`).
5. **Set the variables** (see `.env.example`): `DISCORD_TOKEN` and `ADMIN_ID` are required, `LANGUAGE=en` selects English. `ADMIN_ID` is your user ID (Discord -> Settings -> Advanced -> Developer Mode, then right-click your name -> Copy User ID).
6. **Post the message.** In the sign-up channel type `/setup_signup`: intro, rules and button appear.

### Customize
- Edit the rules in `regolamento.py` (English text: `SEZIONI_EN`).
- Channel and role names, classes and sources are set with environment variables (see `.env.example`). Names are matched partially, so `requests` also finds `📩・requests`.
- Another language? Copy the dictionary in `lingua.py` and translate the values.

### Commands (only for the administrator set in ADMIN_ID)
In English mode: `/setup_signup`, `/publish_rules`, `/reset_requests user`. In Italian mode: `/setup_iscrizione`, `/pubblica_regolamento`, `/azzera_richieste utente`.

### Data and privacy
The bot stores the character name, Discord ID and the texts typed by users in a database on your hosting.
You are responsible for this data: tell your players and delete it on request.

### License and warranty
Use and modify it freely. No warranty: you install and run it yourself.

---

## Italiano

Un bot per Discord che gestisce l'iscrizione dei nuovi giocatori. Si installa sul tuo server
con il tuo bot e il tuo hosting: nessuno ospita niente al posto tuo.

### Come funziona
1. Il nuovo arrivato legge il regolamento nel canale `iscrizione` e preme il bottone verde.
2. Compila un modulo: nome del PG, classe, come vi ha conosciuto, un aneddoto divertente, note.
3. La richiesta arriva nel canale `richieste`: il GM o un officer la approva o la rifiuta.
4. Se approvata: il giocatore riceve il ruolo e la scheda passa in `da-gildare` (con avviso agli officer).
5. Un officer lo invita in gilda in gioco e preme "Gildato": la scheda sparisce e il giocatore riceve un messaggio.
6. Il canale `log-iscrizioni` conserva ogni passaggio, con la candidatura completa.

### Cosa serve
- Un server Discord dove sei amministratore.
- Un account GitHub e un servizio per tenere il bot sempre acceso (per esempio Railway, circa 5 dollari al mese).
- Un volume permanente montato su `/data`, altrimenti le richieste si perdono a ogni riavvio.

### Installazione
1. **Crea il bot.** Su https://discord.com/developers/applications clicca New Application, poi Bot. Copia il **token** (resta segreto: non incollarlo in chat, post o file condivisi). Lascia spenti i "Privileged Gateway Intents".
2. **Invita il bot.** In OAuth2 -> URL Generator scegli gli scope `bot` e `applications.commands`. Permessi: View Channels, Send Messages, Embed Links, Read Message History, Manage Roles. Apri il link generato e scegli il tuo server.
3. **Crea canali e ruoli.** Canali: `iscrizione` (visibile a tutti, nessuno scrive), `richieste` e `da-gildare` (solo officer), `log-iscrizioni` (solo officer). Ruolo per gli approvati (di default `iscritto`) e ruolo officer (di default `officer`). Il ruolo del bot deve stare **sopra** il ruolo degli approvati. Nei canali con permessi limitati dai al bot permessi espliciti (vedere, scrivere, incorporare link, leggere la cronologia, e per l'avviso "menziona tutti i ruoli" in `da-gildare`).
4. **Metti il codice online.** Carica questi file su un tuo repository GitHub **privato** e collegalo all'hosting. Comando di avvio: `python bot.py` (o usa il `Procfile`).
5. **Imposta le variabili** (vedi `.env.example`): `DISCORD_TOKEN` e `ADMIN_ID` sono obbligatorie; `LANGUAGE` sceglie la lingua (`it` o `en`). `ADMIN_ID` e' il tuo ID utente (Discord -> Impostazioni -> Avanzate -> Modalita' sviluppatore, poi tasto destro sul tuo nome -> Copia ID utente).
6. **Pubblica il messaggio.** Nel canale `iscrizione` scrivi `/setup_iscrizione`: compaiono introduzione, regolamento e bottone.

### Personalizzare
- Il regolamento si modifica in `regolamento.py`.
- Nomi di canali e ruoli, classi e fonti si cambiano con le variabili d'ambiente (vedi `.env.example`).
- I nomi dei canali e dei ruoli si cercano anche in modo parziale (`richieste` trova `📩・richieste`).

### Comandi (solo per l'amministratore indicato in ADMIN_ID)
- `/setup_iscrizione`: pubblica introduzione, regolamento e bottone nel canale corrente.
- `/pubblica_regolamento`: pubblica una copia del regolamento in un altro canale.
- `/azzera_richieste utente`: chiude le richieste aperte di un utente (utile per le prove).

### Dati e privacy
Il bot salva in un database sul tuo hosting nome del PG, ID Discord e i testi inseriti dagli utenti.
Sei tu il responsabile di questi dati: informa i tuoi giocatori e cancellali a richiesta.

### Licenza e garanzie
Usalo e modificalo liberamente. Nessuna garanzia: sei tu a installarlo e a gestirlo.
