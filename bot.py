import os
import sqlite3
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    MessageHandler,
    ContextTypes,
    filters
)


TOKEN = os.getenv("TOKEN")

GROUP_ID = -1003992021211

GROUP_LINK = "https://t.me/rodadasebonuslink"

REF_VALUE = 1.50

MIN_WITHDRAW = 10.00

ADMIN_ID = 0


# =====================
# BANCO
# =====================

conn = sqlite3.connect(
    "bot.db",
    check_same_thread=False
)

cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id TEXT PRIMARY KEY,
username TEXT,
ref TEXT,
balance REAL DEFAULT 0,
invites INTEGER DEFAULT 0,
joined INTEGER DEFAULT 0,
pix TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS referrals(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id TEXT,
indicator TEXT,
username TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawals(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id TEXT,
value REAL,
pix TEXT,
status TEXT
)
""")


conn.commit()



# =====================
# FUNÇÕES
# =====================

def create_user(uid, username):

    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (id,username)
        VALUES (?,?)
        """,
        (
            uid,
            username
        )
    )

    conn.commit()



def get_user(uid):

    cursor.execute(
        "SELECT * FROM users WHERE id=?",
        (uid,)
    )

    return cursor.fetchone()



def set_ref(uid, ref):

    cursor.execute(
        """
        UPDATE users
        SET ref=?
        WHERE id=?
        """,
        (
            ref,
            uid
        )
    )

    conn.commit()



def add_balance(uid):

    cursor.execute(
        """
        UPDATE users
        SET balance = balance + ?
        WHERE id=?
        """,
        (
            REF_VALUE,
            uid
        )
    )

    conn.commit()



def add_invite(uid):

    cursor.execute(
        """
        UPDATE users
        SET invites = invites + 1
        WHERE id=?
        """,
        (uid,)
    )

    conn.commit()



def mark_join(uid):

    cursor.execute(
        """
        UPDATE users
        SET joined=1
        WHERE id=?
        """,
        (uid,)
    )

    conn.commit()



def save_referral(user, indicator, username):

    cursor.execute(
        """
        INSERT INTO referrals
        (user_id,indicator,username)
        VALUES (?,?,?)
        """,
        (
            user,
            indicator,
            username
        )
    )

    conn.commit()



def keyboard():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🔗 Meu link",
                callback_data="link"
            ),

            InlineKeyboardButton(
                "💰 Saldo",
                callback_data="saldo"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 Convites",
                callback_data="convites"
            ),

            InlineKeyboardButton(
                "💸 Sacar",
                callback_data="saque"
            )
        ],

        [
            InlineKeyboardButton(
                "🏆 Ranking",
                callback_data="ranking"
            ),

            InlineKeyboardButton(
                "📜 Histórico",
                callback_data="historico"
            )
        ]

    ])
# =====================
# START
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    uid = str(user.id)

    username = user.username or "usuario"


    create_user(
        uid,
        username
    )


    if context.args:

        ref = context.args[0]


        if ref != uid:

            data = get_user(uid)


            if data and not data[2]:

                set_ref(
                    uid,
                    ref
                )


    await update.message.reply_text(

        """
🎁 <b>INDICAÇÃO REGISTRADA!</b>


Entre no grupo para confirmar sua indicação e liberar sua recompensa.


💰 Valor por indicação:
<b>R$ 1,50</b>
""",

        reply_markup=InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🚀 Entrar no grupo",
                    url=GROUP_LINK
                )
            ]

        ]),

        parse_mode="HTML"

    )



# =====================
# CONFIRMAR ENTRADA
# =====================

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    member = update.chat_member


    if member.new_chat_member.status not in ["member", "administrator"]:

        return


    user = member.new_chat_member.user

    uid = str(user.id)

    username = user.username or "usuario"


    create_user(
        uid,
        username
    )


    data = get_user(uid)


    if data[5] == 1:

        return


    ref = data[2]


    mark_join(uid)



    if not ref:

        return



    if ref == uid:

        return



    add_balance(ref)

    add_invite(ref)


    save_referral(
        uid,
        ref,
        username
    )


    indicador = get_user(ref)



    try:

        await context.bot.send_message(

            chat_id=int(ref),

            text=f"""
🎉 <b>NOVA INDICAÇÃO CONFIRMADA!</b>


👤 Usuário:
@{username}


💰 Comissão:
<b>+R$ {REF_VALUE:.2f}</b>


💵 Seu saldo:
<b>R$ {indicador[3] + REF_VALUE:.2f}</b>


👥 Convites:
<b>{indicador[4] + 1}</b>
""",

            parse_mode="HTML"

        )


    except:

        pass




# =====================
# PAINEL NO GRUPO
# =====================

async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):


    await update.message.reply_text(

        """
🎁 <b>PAINEL DE INDICAÇÕES</b>


💰 Ganhe R$ 1,50 por cada pessoa indicada.


💸 Saque mínimo:
<b>R$ 10,00</b>


Clique abaixo:
""",

        reply_markup=keyboard(),

        parse_mode="HTML"

    )



# =====================
# BOTÕES
# =====================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()


    uid = str(query.from_user.id)


    create_user(
        uid,
        query.from_user.username or "usuario"
    )


    data = get_user(uid)



    # =====================
    # LINK
    # =====================

    if query.data == "link":

        me = await context.bot.get_me()


        await query.message.reply_text(

f"""
🔗 <b>SEU LINK DE INDICAÇÃO</b>


https://t.me/{me.username}?start={uid}
""",

parse_mode="HTML"

        )



    # =====================
    # SALDO
    # =====================

    elif query.data == "saldo":

        await query.message.reply_text(

f"""
💰 <b>SEU SALDO</b>


R$ {data[3]:.2f}
""",

parse_mode="HTML"

        )



    # =====================
    # CONVITES
    # =====================

    elif query.data == "convites":

        cursor.execute(
            """
            SELECT username
            FROM referrals
            WHERE indicator=?
            """,
            (uid,)
        )


        lista = cursor.fetchall()


        texto = "👥 <b>SEUS CONVITES</b>\n\n"


        if not lista:

            texto += "Nenhum convite confirmado."


        else:

            for i, x in enumerate(lista, 1):

                texto += f"{i}. @{x[0]}\n"



        await query.message.reply_text(
            texto,
            parse_mode="HTML"
        )



    # =====================
    # SAQUE
    # =====================

    elif query.data == "saque":


        if data[3] < MIN_WITHDRAW:


            await query.message.reply_text(

f"""
❌ <b>SALDO INSUFICIENTE</b>


💰 Seu saldo:
R$ {data[3]:.2f}


💸 Saque mínimo:
R$ {MIN_WITHDRAW:.2f}
""",

parse_mode="HTML"

            )

            return



        context.user_data["saque"] = True


        await query.message.reply_text(

"""
💸 <b>SOLICITAÇÃO DE SAQUE</b>


Digite sua chave Pix:
""",

parse_mode="HTML"

        )



    # =====================
    # RANKING
    # =====================

    elif query.data == "ranking":


        cursor.execute(
            """
            SELECT username, invites
            FROM users
            ORDER BY invites DESC
            LIMIT 10
            """
        )


        dados = cursor.fetchall()


        texto = "🏆 <b>RANKING DE INDICADORES</b>\n\n"


        if not dados:

            texto += "Nenhum registro."


        else:

            for i, x in enumerate(dados, 1):

                texto += f"{i}º @{x[0]} - {x[1]} convites\n"



        await query.message.reply_text(

            texto,

            parse_mode="HTML"

        )



    # =====================
    # HISTÓRICO DE SAQUES
    # =====================

    elif query.data == "historico":


        cursor.execute(
            """
            SELECT value,status
            FROM withdrawals
            WHERE user_id=?
            ORDER BY id DESC
            """,
            (uid,)
        )


        dados = cursor.fetchall()


        texto = "📜 <b>HISTÓRICO DE SAQUES</b>\n\n"


        if not dados:

            texto += "Nenhum saque realizado."


        else:

            for x in dados:

                texto += f"""
💸 Valor: R$ {x[0]:.2f}
⏳ Status: {x[1]}

"""



        await query.message.reply_text(

            texto,

            parse_mode="HTML"

        )
# =====================
# RECEBER PIX
# =====================

async def receber_pix(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("saque"):
        return


    uid = str(update.effective_user.id)

    pix = update.message.text


    data = get_user(uid)

    valor = data[3]


    cursor.execute(
        """
        INSERT INTO withdrawals
        (user_id,value,pix,status)
        VALUES (?,?,?,?)
        """,
        (
            uid,
            valor,
            pix,
            "PENDENTE"
        )
    )


    cursor.execute(
        """
        UPDATE users
        SET balance=0,
        pix=?
        WHERE id=?
        """,
        (
            pix,
            uid
        )
    )


    conn.commit()



    await update.message.reply_text(

f"""
💸 <b>SAQUE SOLICITADO!</b>


💰 Valor:
<b>R$ {valor:.2f}</b>


🔑 Pix:
{pix}


⏳ Status:
<b>PENDENTE</b>
""",

parse_mode="HTML"

    )


    context.user_data.clear()


# =====================
# INICIAR BOT
# =====================

async def main():

    bot = Application.builder().token(TOKEN).build()


    bot.add_handler(
        CommandHandler("start", start)
    )


    bot.add_handler(
        CommandHandler("painel", painel)
    )


    bot.add_handler(
        CallbackQueryHandler(buttons)
    )


    bot.add_handler(
        ChatMemberHandler(check_join)
    )


    bot.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receber_pix
        )
    )


    print("BOT ONLINE")


    await bot.initialize()
    await bot.start()
    await bot.updater.start_polling()


    await asyncio.Event().wait()



if __name__ == "__main__":

    import asyncio

    asyncio.run(main())
