import dill
from typing import List

from telethon.events import ChatAction
from telethon.tl import types
from telethon.utils import get_display_name

from userbot import client
from userbot.utils.events import NewMessage


plugin_category = "bucci"
redis = client.database

dice_chats: List[int] = []

if redis:
    if redis.exists('dice:chats'):
        dice_chats = dill.loads(redis.get('dice:chats'))


@client.onMessage(
    command=("diceban", plugin_category),
    outgoing=True, regex="diceban(?: |$)(on|off)$"
)
async def dice_toggle(event: NewMessage.Event) -> None:
    """Toggle to add a chat in the list to ban anyone who sends the dice"""
    if not redis:
        await event.answer('`You need Redis to use this.`')
        return
    match = event.matches[0].group(1)
    text = None
    if match:
        match = match.lower()
        if match in ('on', 'enable') and event.chat_id not in dice_chats:
            dice_chats.append(event.chat_id)
            text = "`Will ban anyone who rolls a dice now!`"
        elif match in ('off', 'disable') and event.chat_id in dice_chats:
            dice_chats.remove(event.chat_id)
            text = "`Successfully disabled dice ban!`"
        if text:
            await update_db()
            await event.answer(text, self_destruct=2)
    else:
        if event.chat_id in dice_chats:
            text = "`Dice ban is enabled for this chat.`"
        else:
            text = "`Dice ban is not enabled for this chat.`"
        await event.answer(text, self_destruct=2)


@client.onMessage(incoming=True)
async def dice_listener(event: NewMessage.Event) -> None:
    """Check for new incoming dice messages and ban the sender if it matches"""
    if not (
        redis or event.is_group or
        (event.chat.creator or event.chat.admin_rights.ban_users)
    ):
        return
    if (
        event.chat_id in dice_chats and
        isinstance(event.media, types.MessageMediaDice)
    ):
        sender = await event.get_sender()
        try:
            await client.edit_permissions(
                entity=event.chat.id,
                user=sender.id,
                view_messages=False
            )
            href = f"[{get_display_name(sender)}](tg://user?id={sender.id})"
            await event.answer(f'{href} `was banned for rolling a dice!`')
        except Exception:
            pass
        if event.chat.creator or event.chat.admin_rights.delete_messages:
            await event.delete()


@client.on(ChatAction)
async def inc_handler(event):
    """Listen for new chat actions to see if you were added by in a new chat"""
    added = False
    if event.user_added:
        me = await client.get_me()
        users = await event.get_users()
        for user in users:
            if user.id == me.id:
                added = True
                break
        if added:
            chat = await event.get_chat()
            added_by = await event.get_added_by()
            if client.logger:
                entity = client.config['userbot'].getint(
                    'logger_group_id', False
                )
            else:
                entity = "self"
            adder = (
                f'[{get_display_name(added_by)}](tg://user?id={added_by.id})'
            )
            if chat.username:
                group = (
                    f'**[{chat.title}](tg://resolve?domain={chat.username})**'
                    f' `{chat.id}`'
                )
            else:
                group = f"**{chat.title}** `{chat.id}`"
            await client.send_message(
                entity, f'{adder} `has added you to` {group}'
            )


async def update_db() -> None:
    """Update the DB with the updated list of chats"""
    if redis:
        if dice_chats:
            redis.set('dice:chats', dill.dumps(dice_chats))
        else:
            redis.delete('dice:chats')
