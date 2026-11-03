import os
import time
from collections import defaultdict, deque

import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

RED = discord.Color.red()

anti_raid = defaultdict(lambda: False)
join_times = defaultdict(deque)


def is_admin():
    return app_commands.checks.has_permissions(
        administrator=True
    )


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"EQUIPE CAOS online: {bot.user}")


# ENVIAR MENSAGENS
@bot.tree.command(
    name="enviar",
    description="Envia uma mensagem pelo EQUIPE CAOS"
)
@app_commands.describe(
    canal="Canal onde enviar",
    mensagem="Texto da mensagem"
)
@is_admin()
async def enviar(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    mensagem: str
):
    embed = discord.Embed(
        description=mensagem,
        color=RED
    )
    embed.set_author(name="EQUIPE CAOS")

    await canal.send(embed=embed)

    await interaction.response.send_message(
        f"Mensagem enviada em {canal.mention}.",
        ephemeral=True
    )


# BANIR MEMBROS
@bot.tree.command(
    name="ban",
    description="Bane um membro do servidor"
)
@app_commands.describe(
    membro="Membro que será banido",
    motivo="Motivo do banimento"
)
@is_admin()
async def ban(
    interaction: discord.Interaction,
    membro: discord.Member,
    motivo: str = "Não informado"
):
    if membro.id == interaction.user.id:
        await interaction.response.send_message(
            "Você não pode banir a si mesmo.",
            ephemeral=True
        )
        return

    if membro.top_role >= interaction.user.top_role:
        await interaction.response.send_message(
            "O cargo desse membro é igual ou superior ao seu.",
            ephemeral=True
        )
        return

    if membro.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "Meu cargo precisa estar acima do cargo desse membro.",
            ephemeral=True
        )
        return

    try:
        await membro.ban(reason=motivo)

        await interaction.response.send_message(
            f"🔨 {membro} foi banido.\nMotivo: {motivo}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "Não tenho permissão para banir esse membro.",
            ephemeral=True
        )


# ATIVAR OU DESATIVAR ANTI-RAID
@bot.tree.command(
    name="antiraid",
    description="Ativa ou desativa a proteção contra raids"
)
@app_commands.describe(
    ativar="True para ativar ou False para desativar"
)
@is_admin()
async def antiraid(
    interaction: discord.Interaction,
    ativar: bool
):
    anti_raid[interaction.guild_id] = ativar

    status = "ativado" if ativar else "desativado"

    await interaction.response.send_message(
        f"🛡️ Anti-raid {status}."
    )


# DETECTAR ENTRADAS EM MASSA
@bot.event
async def on_member_join(member: discord.Member):
    guild_id = member.guild.id

    if not anti_raid[guild_id]:
        return

    now = time.time()
    joins = join_times[guild_id]
    joins.append(now)

    while joins and now - joins[0] > 10:
        joins.popleft()

    if len(joins) >= 8:
        try:
            await member.guild.edit(
                verification_level=discord.VerificationLevel.high
            )
        except discord.Forbidden:
            pass

        channel = member.guild.system_channel

        if channel:
            await channel.send(
                "🚨 **EQUIPE CAOS — ALERTA ANTI-RAID**\n"
                "Entradas em massa detectadas! "
                "O nível de verificação foi aumentado."
            )

        joins.clear()


if not TOKEN:
    raise RuntimeError(
        "Configure a variável de ambiente DISCORD_TOKEN."
    )

bot.run(TOKEN)
