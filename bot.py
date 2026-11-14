"""Bot iscrizioni per gilde di World of Warcraft su Discord.

Flusso:
  #iscrizione  -> bottone _("Accetto il regolamento e mi iscrivo") -> form (nome PG, classe, ...)
  #richieste   -> scheda con Approva / Rifiuta (approvano il GM e gli officer)
  Approva      -> ruolo "iscritto" (configurabile) + scheda in #da-gildare
  #da-gildare  -> bottone "Gildato" (solo GM e officer in game) -> la scheda sparisce
  #log-iscrizioni -> ogni passaggio, classificato
"""
import datetime
import logging
import os
import sqlite3

import discord
from discord import app_commands

from lingua import EN
from regolamento import SEZIONI_EN, SEZIONI_IT

LANGUAGE = os.environ.get("LANGUAGE", "it").strip().lower()  # "it" (default) oppure "en"
SEZIONI = SEZIONI_EN if LANGUAGE == "en" else SEZIONI_IT


def _(testo):
    """Restituisce il testo nella lingua scelta (i testi in italiano sono la chiave)."""
    return EN.get(testo, testo) if LANGUAGE == "en" else testo


def _D(it, en):
    """Valore predefinito diverso per lingua (nomi di canali, ruoli, liste)."""
    return en if LANGUAGE == "en" else it


TOKEN = os.environ["DISCORD_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])  # il tuo ID utente Discord (obbligatorio)
DB_PATH = os.environ.get("DB_PATH", "/data/iscrizioni.db")

# Nomi (parziali, senza distinzione maiuscole/minuscole) di canali e ruoli.
CH_RICHIESTE = os.environ.get("CH_RICHIESTE", _D("richieste", "requests"))
CH_DA_GILDARE = os.environ.get("CH_DA_GILDARE", _D("da-gildare", "to-invite"))
CH_LOG = os.environ.get("CH_LOG", _D("log-iscrizioni", "signup-log"))
ROLE_APPROVED = os.environ.get("ROLE_APPROVED", _D("iscritto", "member"))
def _lista(nome, default):
    return [x.strip() for x in os.environ.get(nome, default).split(",") if x.strip()]


# Ruoli degli officer: possono approvare, rifiutare e segnare "gildato".
ROLES_GUILDERS = [r.lower() for r in _lista("ROLES_GUILDERS", "officer")]
# Ruoli avvisati in #da-gildare quando arriva un PG da gildare (facoltativo).
ROLES_NOTIFY = _lista("ROLES_NOTIFY", "")

COLOR_PENDING = 0xF1C40F
COLOR_OK = 0x2ECC71
COLOR_NO = 0xE74C3C
COLOR_GUILD = 0x9B59B6
COLOR_INFO = 0x3498DB

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot-iscrizioni")


# ---------------------------------------------------------------- database
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with db() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_tag TEXT,
                pg TEXT, classe TEXT, livello TEXT, fonte TEXT, note TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at INTEGER,
                review_msg_id INTEGER,
                guild_msg_id INTEGER,
                handled_by INTEGER,
                reject_reason TEXT
            )"""
        )
        try:
            c.execute("ALTER TABLE requests ADD COLUMN cazzata TEXT")
        except sqlite3.OperationalError:
            pass


def get_by_review_msg(msg_id):
    with db() as c:
        return c.execute("SELECT * FROM requests WHERE review_msg_id=?", (msg_id,)).fetchone()


def get_by_guild_msg(msg_id):
    with db() as c:
        return c.execute("SELECT * FROM requests WHERE guild_msg_id=?", (msg_id,)).fetchone()


def get_by_id(req_id):
    with db() as c:
        return c.execute("SELECT * FROM requests WHERE id=?", (req_id,)).fetchone()


def has_open_request(user_id):
    with db() as c:
        return c.execute(
            "SELECT 1 FROM requests WHERE user_id=? AND status IN ('pending','approved')",
            (user_id,),
        ).fetchone()


# ---------------------------------------------------------------- helpers
def norm(text):
    return text.lower().replace("’", "'").replace("‘", "'")


def split_text(text, limit=3900):
    """Divide un testo lungo in parti sotto il limite di Discord, andando a capo."""
    parts, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > limit and current:
            parts.append(current.rstrip("\n"))
            current = ""
        current += line + "\n"
    if current.strip():
        parts.append(current.rstrip("\n"))
    return parts


def esito_testo(parola, officer, motivo=None):
    ora = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    icona = "✅" if parola == "Approvata" else "❌"
    testo = icona + " " + _("{parola} da {officer}").format(parola=_(parola), officer=officer.mention) + f" · <t:{ora}:f>"
    if motivo:
        testo += "\n" + _("Motivo: {motivo}").format(motivo=motivo)
    return testo


def find_channel(guild, key):
    key = key.lower()
    for ch in guild.text_channels:
        if key in ch.name.lower():
            return ch
    return None


def find_role(guild, key):
    key = norm(key)
    for r in guild.roles:
        if key in norm(r.name):
            return r
    return None


def is_guilder(member):
    names = [norm(r.name) for r in member.roles]
    return any(any(key in n for n in names) for key in ROLES_GUILDERS)


def request_embed(row, title, color, esito=None):
    e = discord.Embed(title=title, color=color)
    e.add_field(name=_("Personaggio"), value=row["pg"], inline=True)
    e.add_field(name=_("Classe"), value=row["classe"] or "-", inline=True)
    if row["livello"]:
        e.add_field(name=_("Livello"), value=row["livello"], inline=True)
    e.add_field(name=_("Utente Discord"), value=f"<@{row['user_id']}> ({row['user_tag']})", inline=False)
    e.add_field(name=_("Come ci ha conosciuto"), value=row["fonte"] or "-", inline=False)
    if row["cazzata"]:
        e.add_field(name=_("Il suo aneddoto in WoW 🤡"), value=row["cazzata"], inline=False)
    if row["note"]:
        e.add_field(name=_("Alt, note e orari"), value=row["note"], inline=False)
    e.add_field(
        name=_("Regolamento"),
        value=_("Accettato il <t:{ts}:f>").format(ts=row["created_at"]),
        inline=False,
    )
    if esito:
        e.add_field(name=_("Esito"), value=esito, inline=False)
    e.set_footer(text=_("Richiesta n. {id}").format(id=row["id"]))
    return e


async def write_log(guild, category, color, row, detail=None, full=False):
    ch = find_channel(guild, CH_LOG)
    if not ch:
        log.warning("Canale log non trovato")
        return
    e = discord.Embed(title=category, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
    e.add_field(name="PG", value=row["pg"], inline=True)
    e.add_field(name=_("Utente"), value=f"<@{row['user_id']}>", inline=True)
    e.add_field(name=_("Richiesta"), value=_("n. {id}").format(id=row["id"]), inline=True)
    if full:
        e.add_field(name=_("Classe"), value=row["classe"] or "-", inline=True)
        e.add_field(name=_("Come ci ha conosciuto"), value=row["fonte"] or "-", inline=True)
        if row["cazzata"]:
            e.add_field(name=_("Il suo aneddoto in WoW 🤡"), value=row["cazzata"], inline=False)
        if row["note"]:
            e.add_field(name=_("Alt, note e orari"), value=row["note"], inline=False)
    if detail:
        e.add_field(name=_("Dettaglio"), value=detail, inline=False)
    await ch.send(embed=e)


# ---------------------------------------------------------------- iscrizione
# Liste dei menu a tendina (massimo 25 voci ciascuna). Si cambiano con le variabili CLASSI e FONTI.
FONTI = _lista("FONTI", _D(
    "Facebook,Instagram,Telegram,Internet,Intelligenza artificiale,Google,Passaparola (un amico),Altro",
    "Facebook,Instagram,Telegram,Internet,Artificial intelligence,Google,Word of mouth (a friend),Other",
))
CLASSI = _lista("CLASSI", "Warrior,Paladin,Hunter,Rogue,Priest,Shaman,Mage,Warlock,Druid")


class RegisterModal(discord.ui.Modal, title=_("Iscrizione in Gilda")):
    pg = discord.ui.Label(
        text=_("Nome del tuo PG (in game)"),
        component=discord.ui.TextInput(max_length=40, required=True),
    )
    classe = discord.ui.Label(
        text=_("Classe che vuoi giocare"),
        component=discord.ui.Select(
            placeholder=_("Scegli la classe"),
            options=[discord.SelectOption(label=c, value=c) for c in CLASSI],
        ),
    )
    fonte = discord.ui.Label(
        text=_("Come ci hai conosciuto?"),
        component=discord.ui.Select(
            placeholder=_("Scegli una risposta"),
            options=[discord.SelectOption(label=f, value=f) for f in FONTI],
        ),
    )
    cazzata = discord.ui.Label(
        text=_("Il tuo aneddoto più buffo in WoW 🤡"),
        description=_("Facoltativo: una figuraccia o un momento epico del tuo passato in WoW."),
        component=discord.ui.TextInput(style=discord.TextStyle.paragraph, max_length=400, required=False),
    )
    note = discord.ui.Label(
        text=_("Alt, note e orari"),
        description=_("Facoltativo: nomi degli alt che porti in gilda, orari, altro."),
        component=discord.ui.TextInput(style=discord.TextStyle.paragraph, max_length=500, required=False),
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        ch = find_channel(guild, CH_RICHIESTE)
        if not ch:
            await interaction.response.send_message(
                _("Errore: canale richieste non trovato. Avvisa un officer."), ephemeral=True
            )
            return
        now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        classe = self.classe.component.values[0] if self.classe.component.values else ""
        fonte = self.fonte.component.values[0] if self.fonte.component.values else ""
        with db() as c:
            cur = c.execute(
                """INSERT INTO requests (user_id, user_tag, pg, classe, livello, fonte, note, cazzata, status, created_at)
                   VALUES (?,?,?,?,?,?,?,?, 'pending', ?)""",
                (
                    interaction.user.id,
                    str(interaction.user),
                    self.pg.component.value.strip(),
                    classe,
                    "",
                    fonte,
                    (self.note.component.value or "").strip(),
                    (self.cazzata.component.value or "").strip(),
                    now,
                ),
            )
            req_id = cur.lastrowid
        row = get_by_id(req_id)
        msg = await ch.send(
            embed=request_embed(row, _("Nuova richiesta di iscrizione"), COLOR_PENDING),
            view=ReviewView(),
        )
        with db() as c:
            c.execute("UPDATE requests SET review_msg_id=? WHERE id=?", (msg.id, req_id))
        await write_log(guild, _("📝 Richiesta ricevuta"), COLOR_INFO, row, _("Regolamento accettato"), full=True)
        await interaction.response.send_message(
            _("Richiesta inviata! Un officer la valuterà a breve. Riceverai un messaggio con l'esito."),
            ephemeral=True,
        )


class RegisterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label=_("Accetto il regolamento e mi iscrivo"),
        style=discord.ButtonStyle.success,
        custom_id="iscrizione:register",
    )
    async def register(self, interaction: discord.Interaction, button: discord.ui.Button):
        log.info("Click su Iscriviti da %s", interaction.user)
        role = find_role(interaction.guild, ROLE_APPROVED)
        if role and role in interaction.user.roles:
            await interaction.response.send_message(_("Sei già dentro, benvenuto!"), ephemeral=True)
            return
        if has_open_request(interaction.user.id):
            await interaction.response.send_message(
                _("Hai già una richiesta in corso. Attendi la risposta di un officer."), ephemeral=True
            )
            return
        try:
            await interaction.response.send_modal(RegisterModal())
        except Exception:
            log.exception("Errore nell'aprire il modulo")
            raise


# ---------------------------------------------------------------- approvazione
class RejectModal(discord.ui.Modal, title=_("Rifiuta richiesta")):
    motivo = discord.ui.TextInput(
        label=_("Motivo (facoltativo)"), style=discord.TextStyle.paragraph, required=False, max_length=300
    )

    def __init__(self, message):
        super().__init__()
        self.message = message

    async def on_submit(self, interaction: discord.Interaction):
        row = get_by_review_msg(self.message.id)
        if not row or row["status"] != "pending":
            await interaction.response.send_message(_("Richiesta già gestita."), ephemeral=True)
            return
        reason = self.motivo.value.strip()
        with db() as c:
            c.execute(
                "UPDATE requests SET status='rejected', handled_by=?, reject_reason=? WHERE id=?",
                (interaction.user.id, reason, row["id"]),
            )
        row = get_by_id(row["id"])
        await write_log(interaction.guild, _("❌ Richiesta rifiutata"), COLOR_NO, row, _("Rifiutata da {officer}").format(officer=interaction.user.mention) + (_(". Motivo: {motivo}").format(motivo=reason) if reason else ""))
        try:
            await self.message.delete()
        except discord.HTTPException:
            await self.message.edit(embed=request_embed(row, _("Richiesta RIFIUTATA"), COLOR_NO, esito=esito_testo("Rifiutata", interaction.user, reason)), view=None)
        try:
            member = await interaction.guild.fetch_member(row["user_id"])
            text = _("La tua richiesta di iscrizione in gilda non è stata accettata.")
            if reason:
                text += "\n" + _("Motivo: {motivo}").format(motivo=reason)
            await member.send(text)
        except discord.HTTPException:
            pass
        await interaction.response.send_message(_("Richiesta rifiutata."), ephemeral=True)


class ReviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _admin_only(self, interaction):
        if interaction.user.id != ADMIN_ID and not is_guilder(interaction.user):
            await interaction.response.send_message(_("Solo gli officer possono usare questo bottone."), ephemeral=True)
            return False
        return True

    @discord.ui.button(label=_("Approva"), style=discord.ButtonStyle.success, custom_id="iscrizione:approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._admin_only(interaction):
            return
        row = get_by_review_msg(interaction.message.id)
        if not row or row["status"] != "pending":
            await interaction.response.send_message(_("Richiesta già gestita."), ephemeral=True)
            return
        guild = interaction.guild
        role = find_role(guild, ROLE_APPROVED)
        if not role:
            await interaction.response.send_message(_("Ruolo '{ruolo}' non trovato.").format(ruolo=ROLE_APPROVED), ephemeral=True)
            return
        try:
            member = await guild.fetch_member(row["user_id"])
        except discord.NotFound:
            await interaction.response.send_message(
                _("L'utente non è più nel server. Rifiuta la richiesta."), ephemeral=True
            )
            return
        try:
            await member.add_roles(role, reason=_("Iscrizione approvata (richiesta {id})").format(id=row["id"]))
        except discord.Forbidden:
            await interaction.response.send_message(
                _("Non riesco ad assegnare il ruolo: sposta il ruolo del bot sopra '{ruolo}'.").format(ruolo=ROLE_APPROVED),
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True)
        with db() as c:
            c.execute("UPDATE requests SET status='approved', handled_by=? WHERE id=?", (interaction.user.id, row["id"]))
        row = get_by_id(row["id"])
        await write_log(guild, _("✅ Richiesta approvata"), COLOR_OK, row, _("Approvata da {officer}. Ruolo {ruolo} assegnato").format(officer=interaction.user.mention, ruolo=ROLE_APPROVED))
        ch = find_channel(guild, CH_DA_GILDARE)
        if ch:
            menzioni = [r.mention for r in (find_role(guild, k) for k in ROLES_NOTIFY) if r]
            testo = (" ".join(menzioni) + " ") if menzioni else ""
            testo += _("🔔 Nuovo PG da gildare: **{pg}**").format(pg=row["pg"])
            msg = await ch.send(
                content=testo,
                embed=request_embed(row, _("Da gildare in game"), COLOR_GUILD),
                view=GuildView(),
                allowed_mentions=discord.AllowedMentions(roles=True, users=False, everyone=False),
            )
            with db() as c:
                c.execute("UPDATE requests SET guild_msg_id=? WHERE id=?", (msg.id, row["id"]))
        try:
            await member.send(
                _("La tua richiesta è stata approvata! Ora vedi tutto il Discord. Un officer ti inviterà in gilda in game sul PG **{pg}**.").format(pg=row["pg"])
            )
        except discord.HTTPException:
            pass
        try:
            await interaction.message.delete()
        except discord.HTTPException:
            await interaction.message.edit(embed=request_embed(row, _("Richiesta APPROVATA"), COLOR_OK, esito=esito_testo("Approvata", interaction.user)), view=None)
        await interaction.followup.send(_("Approvata e aggiunta a 'da gildare'."), ephemeral=True)

    @discord.ui.button(label=_("Rifiuta"), style=discord.ButtonStyle.danger, custom_id="iscrizione:reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._admin_only(interaction):
            return
        await interaction.response.send_modal(RejectModal(interaction.message))


# ---------------------------------------------------------------- da gildare
class GuildView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=_("Gildato ✓"), style=discord.ButtonStyle.primary, custom_id="iscrizione:guilded")
    async def guilded(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != ADMIN_ID and not is_guilder(interaction.user):
            await interaction.response.send_message(_("Solo GM e officer di gilda possono usarlo."), ephemeral=True)
            return
        row = get_by_guild_msg(interaction.message.id)
        if not row:
            await interaction.response.send_message(_("Richiesta non trovata."), ephemeral=True)
            return
        with db() as c:
            c.execute("UPDATE requests SET status='guilded', handled_by=? WHERE id=?", (interaction.user.id, row["id"]))
        row = get_by_id(row["id"])
        await write_log(
            interaction.guild, _("⚔️ Gildato in game"), COLOR_GUILD, row, _("Gildato da {officer}").format(officer=interaction.user.mention)
        )
        await interaction.message.delete()
        await interaction.response.send_message(_("{pg} segnato come gildato.").format(pg=row["pg"]), ephemeral=True)
        try:
            member = await interaction.guild.fetch_member(row["user_id"])
            await member.send(
                _("Sei stato invitato in gilda con il PG **{pg}**. Controlla l'invito in gioco e accettalo. Benvenuto in gilda!").format(pg=row["pg"])
            )
        except discord.HTTPException:
            pass


# ---------------------------------------------------------------- bot
class IscrizioniBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        init_db()
        self.add_view(RegisterView())
        self.add_view(ReviewView())
        self.add_view(GuildView())

    async def on_ready(self):
        for g in self.guilds:
            self.tree.copy_global_to(guild=g)
            await self.tree.sync(guild=g)
        log.info("Bot pronto come %s", self.user)


bot = IscrizioniBot()


async def post_rules(ch, pulsante):
    """Pubblica i due regolamenti in un canale. 'pulsante' dice dove si trova il bottone."""
    for titolo, testo in SEZIONI:
        testo = testo.replace("{PULSANTE}", pulsante)
        for i, parte in enumerate(split_text(testo)):
            await ch.send(
                embed=discord.Embed(title=titolo if i == 0 else None, description=parte, color=COLOR_INFO)
            )


@bot.tree.command(name=_("setup_iscrizione"), description=_("Pubblica il messaggio di iscrizione in questo canale"))
async def setup_iscrizione(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message(_("Solo il GM può usare questo comando."), ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    ch = interaction.channel
    intro = discord.Embed(
        title=_("Vuoi iscriverti in Gilda?"),
        description=_(
            "Compila l'iscrizione in un solo passaggio: Discord e personaggio insieme.\n\n"
            "**Come funziona**\n"
            "1. Leggi il regolamento qui sotto.\n"
            "2. Premi il bottone in fondo e compila il modulo con il nome del tuo PG.\n"
            "3. Un officer valuta la richiesta. Se approvata, ottieni accesso a tutto il Discord "
            "e ti invitiamo in gilda in game."
        ),
        color=COLOR_INFO,
    )
    await ch.send(embed=intro)
    await post_rules(ch, _("qui sotto"))
    fine = discord.Embed(
        description=_("Premendo il bottone dichiari di aver letto e accettato il regolamento."),
        color=COLOR_OK,
    )
    await ch.send(embed=fine, view=RegisterView())
    await interaction.followup.send(_("Messaggio pubblicato."), ephemeral=True)



@bot.tree.command(name=_("azzera_richieste"), description=_("Chiude le richieste aperte di un utente (utile per i test)"))
@app_commands.describe(utente=_("L'utente di cui azzerare le richieste aperte"))
@app_commands.rename(utente=_("utente"))
async def azzera_richieste(interaction: discord.Interaction, utente: discord.Member):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message(_("Solo il GM può usare questo comando."), ephemeral=True)
        return
    with db() as c:
        cur = c.execute(
            "UPDATE requests SET status='rejected', reject_reason=? "
            "WHERE user_id=? AND status IN ('pending','approved')",
            (_("Azzerata dal GM"), utente.id),
        )
        n = cur.rowcount
    await interaction.response.send_message(
        _("Richieste azzerate per {utente}: {n}.").format(utente=utente.mention, n=n), ephemeral=True
    )


@bot.tree.command(name=_("pubblica_regolamento"), description=_("Pubblica il regolamento in questo canale (copia da consultare)"))
async def pubblica_regolamento(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message(_("Solo il GM può usare questo comando."), ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await post_rules(interaction.channel, _("nel canale di iscrizione"))
    await interaction.followup.send(_("Regolamento pubblicato."), ephemeral=True)


if __name__ == "__main__":
    bot.run(TOKEN)
