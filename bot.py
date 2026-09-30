import os
import json
import discord #this is how i integrate the bot to use Discord's API
from discord import app_commands
from dotenv import load_dotenv

from game import GameState
from ai_player import AIPlayer

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")     #ai_player and bot has to detect Discord token and OpenAI key
AI_NAME = os.getenv("AI_PLAYER_NAME", "ShadowBot")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from .env")

AI_KEY = None

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

game = GameState()
ai = AIPlayer(model=OPENAI_MODEL, name=AI_NAME)


def mention_for(player_key: str) -> str:
    player = game.players[player_key]
    if player.is_ai:
        return f"**{player.name}**"
    return f"<@{player.key}>"


def find_human_by_discord_user(user: discord.User | discord.Member):
    return game.players.get(str(user.id))


@client.event
async def on_ready():
    global AI_KEY
    AI_KEY = str(client.user.id)
    await tree.sync()
    print(f"Logged in as {client.user}.")


@tree.command(name="join", description="Join the next Three Shadows game.")
async def join(interaction: discord.Interaction):
    if game.started:
        await interaction.response.send_message(
            "A game is already running. Use `/reset` after the game ends.",
            ephemeral=True
        )
        return

    ok = game.add_human(str(interaction.user.id), interaction.user.display_name)
    if not ok:
        await interaction.response.send_message(
            "You cannot join right now. The game already has two human players "
            "or you already joined.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"**{interaction.user.display_name}** joined. "
        f"Human players: {len([p for p in game.players.values() if not p.is_ai])}/2"
    )


@tree.command(name="start", description="Start the game when two humans have joined.")
async def start(interaction: discord.Interaction):
    humans = [p for p in game.players.values() if not p.is_ai]
    if game.started:
        await interaction.response.send_message("A game is already running.")
        return

    if len(humans) != 2:
        await interaction.response.send_message(
            "Exactly two human players must use `/join` before `/start`."
        )
        return

    if AI_KEY is None:
        await interaction.response.send_message("The bot is still initializing. Try again in a moment.")
        return

    game.start(AI_KEY, AI_NAME)

    # Send human roles privately.
    for player in humans:
        try:
            user = await client.fetch_user(int(player.key))
            await user.send(
                f"🔐 **Three Shadows — Private Role**\n\n"
                f"Your secret role is **{player.role}**.\n"
                f"Do not reveal this message to the other players unless you choose to."
            )
        except discord.Forbidden:
            pass

    await interaction.response.send_message(
        "🎭 **The game has started!**\n"
        "There are 3 players: two humans and the AI.\n\n"
        "Roles are private. Discuss using `/say <message>`.\n" #how the discord bot would usually react
        "When ready, vote using `/vote @player`."
    )


@tree.command(name="say", description="Send a public discussion message.") #makes you say a public discussion message
@app_commands.describe(message="What you want to say to the other players.")
async def say(interaction: discord.Interaction, message: str):
    player = find_human_by_discord_user(interaction.user)

    if not game.started or player is None or player.is_ai:
        await interaction.response.send_message(
            "You are not an active human player in the current game.",
            ephemeral=True
        )
        return

    game.add_discussion(player.name, message)

    await interaction.response.send_message(
        f"💬 **{player.name}:** {message}"
    )

    # AI sees only public discussion plus its own secret role.
    ai_response = ai.respond_to_discussion(
        game.ai_private_context(),
        player.name,
        message
    )
    game.add_discussion(AI_NAME, ai_response)

    await interaction.followup.send(
        f"🤖 **{AI_NAME}:** {ai_response}"
    )


@tree.command(name="vote", description="Vote for another player.")
@app_commands.describe(player="The player you want to vote for.")
async def vote(interaction: discord.Interaction, player: discord.Member):
    voter = find_human_by_discord_user(interaction.user)

    if not game.started or voter is None or voter.is_ai:
        await interaction.response.send_message(
            "You are not an active human player.",
            ephemeral=True
        )
        return

    target_key = str(player.id)
    if target_key not in game.players:
        await interaction.response.send_message(
            "That person is not one of the three players.",
            ephemeral=True
        )
        return

    try:
        game.cast_vote(voter.key, target_key)
    except ValueError as exc:
        await interaction.response.send_message(str(exc), ephemeral=True)
        return

    await interaction.response.send_message(
        f"🗳️ **{voter.name}** has voted. "
        f"({len(game.votes)}/{len(game.players)} votes received.)"
    )

    # The AI votes after the humans have both voted.
    human_keys = [p.key for p in game.players.values() if not p.is_ai]
    if all(key in game.votes for key in human_keys) and AI_KEY not in game.votes:
        raw = ai.choose_vote(game.ai_private_context())

        try:
            data = json.loads(raw)
            target_name = data.get("target", "")
            statement = data.get("statement", "")
        except json.JSONDecodeError:
            target_name = ""
            statement = raw

        target = game.player_by_name(target_name)

        if target is None or target.key == AI_KEY:
            # Safe deterministic fallback.
            target = next(p for p in game.players.values() if p.key != AI_KEY)

        game.cast_vote(AI_KEY, target.key)
        game.add_discussion(AI_NAME, statement or f"I vote for {target.name}.")

        await interaction.followup.send(
            f"🤖 **{AI_NAME}:** {statement or f'I vote for {target.name}.'}\n"
            f"🗳️ **{AI_NAME} voted for {target.name}.**"
        )

    if game.all_voted():
        result = game.resolve_vote()

        if result["type"] == "tie":
            tally_text = "\n".join(
                f"- {game.players[key].name}: {count}"
                for key, count in result["tally"].items()
            )
            await interaction.followup.send(
                "⚖️ **Tie vote!** Nobody is eliminated.\n\n"
                f"Vote tally:\n{tally_text}\n\n"
                f"Round {game.round_number} begins. Discuss again."
            )
        else:
            eliminated = game.players[result["eliminated"]]
            role = result["role"]

            await interaction.followup.send(
                "💀 **Vote complete!**\n\n"
                f"Eliminated: **{eliminated.name}**\n"
                f"Their role was: **{role}**\n\n"
                f"🏆 **{result['winner']} win!**\n\n"
                "Use `/reset` to start another game."
            )


@tree.command(name="status", description="Show the public game status.")
async def status(interaction: discord.Interaction):
    if not game.players:
        await interaction.response.send_message(
            "No players have joined. Use `/join`."
        )
        return

    names = "\n".join(
        f"- {p.name}{' (AI)' if p.is_ai else ''}"
        for p in game.players.values()
    )

    votes = len(game.votes)
    state = "running" if game.started else "waiting for players"

    await interaction.response.send_message(
        f"**Three Shadows status: {state}**\n"
        f"Round: {game.round_number}\n"
        f"Players:\n{names}\n"
        f"Votes received: {votes}/{len(game.players)}"
    )


@tree.command(name="reset", description="Reset the current game.")
async def reset(interaction: discord.Interaction):
    game.reset()
    await interaction.response.send_message(
        "🔄 Game reset. Two humans can use `/join` to begin a new game."
    )


client.run(DISCORD_TOKEN)
