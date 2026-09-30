# Three Shadows — Discord + OpenAI Multiplayer Game

Three Shadows is a three-player chat-based social-deduction game for a class project.

Two players are human Discord users and the third player is an AI-controlled Discord bot.
The game demonstrates:
- a real-time chat interface
- persistent game state
- hidden/private information
- AI decision making
- turn/game-rule enforcement
- an OpenAI API integration
- a complete win condition

## Game rules

There are exactly three players:
1. Human Player 1
2. Human Player 2
3. The AI player

One player is secretly the **Shadow**. The other two are **Investigators**.

### Goal
- Investigators win if they identify and vote out the Shadow.
- The Shadow wins if the vote eliminates an Investigator.

### Round flow
1. Two humans join.
2. `/start` assigns the three roles randomly.
3. Roles are privately revealed to the humans by Discord DM. The AI receives its role through the program.
4. Players discuss publicly with `/say`.
5. The AI responds after human discussion messages.
6. `/vote @player` records a vote.
7. Once all three players have voted, the bot counts the votes.
8. If one player receives at least two votes, that player is eliminated and the game ends.
9. A tie results in another discussion round, followed by another vote.

The Python program—not the AI—decides whether votes are legal and who wins. The AI only chooses its own conversational actions and vote.

## Project structure

```text
three_shadows/
├── bot.py
├── game.py
├── ai_player.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 1. Create a Discord application

Go to the Discord Developer Portal:
https://discord.com/developers/applications

Create an application, then create a Bot for it.

Enable the **Message Content Intent** under the bot's Privileged Gateway Intents.

Invite the bot to a server with permissions to:
- View Channels
- Send Messages
- Read Message History
- Use Slash Commands

Keep the bot token secret.

## 2. Create an OpenAI API key

Create an API key from the OpenAI platform and place it in your `.env` file.

The project uses the official Python OpenAI SDK and the Responses API.

## 3. Install dependencies

Windows:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Configure environment variables

Copy `.env.example` to `.env`.

Example:

```env
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.6
AI_PLAYER_NAME=ShadowBot
```

If the API account you are using exposes a different model, change `OPENAI_MODEL` without changing the rest of the project.

## 5. Run

```bash
python bot.py
```

The terminal should show that the bot has connected.

## Discord commands

```text
/start
```
Starts a game after exactly two humans have joined.

```text
/join
```
Adds the user to the player list.

```text
/say <message>
```
Adds a public discussion message. The AI gets to respond.

```text
/vote @player
```
Casts or changes your vote.

```text
/status
```
Displays public game information.

```text
/reset
```
Resets the current game. Useful for testing.

## Suggested demonstration

For a class presentation:

1. Invite the bot to a Discord server.
2. Have two students join.
3. Run `/start`.
4. Show that the humans receive private roles.
5. Have the humans discuss using `/say`.
6. Show that the AI responds with its own reasoning/claims.
7. Vote using `/vote`.
8. Show the automatic result.
9. Run `/reset` and play a second round with different roles.

## Why the AI is a real player

The AI receives:
- its private role
- the public discussion history
- the current public game state
- legal actions

It does NOT receive the private roles of the human players.

The AI must independently choose:
- what to say
- whom to accuse
- whom to vote for

The game engine validates all actions and determines the actual result.

This separation prevents the language model from changing game rules or declaring itself the winner.

## Architecture

```text
Human 1 ─┐
         │
Human 2 ─┼──> Discord ──> bot.py ──> game.py
         │                    │
AI Bot ──┘                    └──> ai_player.py ──> OpenAI Responses API
```

## Academic discussion points

The project demonstrates:
- API integration
- event-driven programming
- object-oriented game-state management
- asynchronous programming
- natural-language interaction
- prompt engineering
- separation of AI behavior from deterministic application logic
- privacy boundaries for hidden game information
- validation of AI-generated decisions

## Security

Never commit `.env` to GitHub.

The `.gitignore` file included in this project excludes it.
