# Bot iscrizioni per gilde di World of Warcraft / WoW guild sign-up bot

In italiano qui sotto. **[English version → README_EN.md](README_EN.md)**. La lingua del bot si sceglie con la variabile `LANGUAGE` (`it` oppure `en`).

Un bot per Discord che gestisce l'iscrizione dei nuovi giocatori. Si installa sul tuo server
con il tuo bot e il tuo hosting: nessuno ospita niente al posto tuo.

## Come funziona
1. Il nuovo arrivato legge il regolamento nel canale `iscrizione` e preme il bottone verde.
2. Compila un modulo: nome del PG, classe, come vi ha conosciuto, un aneddoto divertente, note.
3. La richiesta arriva nel canale `richieste`: il GM o un officer la approva o la rifiuta.
4. Se approvata: il giocatore riceve il ruolo e la scheda passa in `da-gildare` (con avviso agli officer).
5. Un officer lo invita in gilda in gioco e preme "Gildato": la scheda sparisce e il giocatore riceve un messaggio.
6. Il canale `log-iscrizioni` conserva ogni passaggio, con la candidatura completa.

## Cosa serve
- Un server Discord dove sei amministratore.
- Un account GitHub e un servizio per tenere il bot sempre acceso (per esempio Railway, circa 5 dollari al mese).
- Un volume permanente montato su `/data`, altrimenti le richieste si perdono a ogni riavvio.

## Installazione
1. **Crea il bot.** Su https://discord.com/developers/applications clicca New Application, poi Bot. Copia il **token** (resta segreto: non incollarlo in chat, post o file condivisi). Lascia spenti i "Privileged Gateway Intents".
2. **Invita il bot.** In OAuth2 -> URL Generator scegli gli scope `bot` e `applications.commands`. Permessi: View Channels, Send Messages, Embed Links, Read Message History, Manage Roles. Apri il link generato e scegli il tuo server.
3. **Crea canali e ruoli.** Canali: `iscrizione` (visibile a tutti, nessuno scrive), `richieste` e `da-gildare` (solo officer), `log-iscrizioni` (solo officer). Ruolo per gli approvati (di default `iscritto`) e ruolo officer (di default `officer`). Il ruolo del bot deve stare **sopra** il ruolo degli approvati. Nei canali con permessi limitati dai al bot permessi espliciti (vedere, scrivere, incorporare link, leggere la cronologia, e per l'avviso "menziona tutti i ruoli" in `da-gildare`).
4. **Metti il codice online.** Carica questi file su un tuo repository GitHub **privato** e collegalo all'hosting. Comando di avvio: `python bot.py` (o usa il `Procfile`).
5. **Imposta le variabili** (vedi `.env.example`): `DISCORD_TOKEN` e `ADMIN_ID` sono obbligatorie; `LANGUAGE` sceglie la lingua (`it` o `en`). `ADMIN_ID` e' il tuo ID utente (Discord -> Impostazioni -> Avanzate -> Modalita' sviluppatore, poi tasto destro sul tuo nome -> Copia ID utente).
6. **Pubblica il messaggio.** Nel canale `iscrizione` scrivi `/setup_iscrizione`: compaiono introduzione, regolamento e bottone.

## Personalizzare
- Il regolamento si modifica in `regolamento.py`.
- Nomi di canali e ruoli, classi e fonti si cambiano con le variabili d'ambiente (vedi `.env.example`).
- I nomi dei canali e dei ruoli si cercano anche in modo parziale (`richieste` trova `📩・richieste`).

## Comandi (solo per l'amministratore indicato in ADMIN_ID)
- `/setup_iscrizione`: pubblica introduzione, regolamento e bottone nel canale corrente.
- `/pubblica_regolamento`: pubblica una copia del regolamento in un altro canale.
- `/azzera_richieste utente`: chiude le richieste aperte di un utente (utile per le prove).

## Dati e privacy
Il bot salva in un database sul tuo hosting nome del PG, ID Discord e i testi inseriti dagli utenti.
Sei tu il responsabile di questi dati: informa i tuoi giocatori e cancellali a richiesta.

## Licenza e garanzie
Usalo e modificalo liberamente. Nessuna garanzia: sei tu a installarlo e a gestirlo.
