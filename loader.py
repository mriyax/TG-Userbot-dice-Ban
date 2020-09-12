from userbot import client
from userbot import client, LOGGER
from userbot.utils.events import NewMessage


pmanager = client.pluginManager


@client.onMessage(
    command=('load'), outgoing=True, regex='load$'
)
async def pluginloader(event: NewMessage.Event) -> None:
    reply = await event.get_reply_message()
    if not reply or not (
        reply.document and (reply.document.mime_type == 'text/x-python') and
        getattr(reply.document.attributes[0], 'file_name', '').endswith('.py')
    ):
        await event.answer('`Reply to a python plugin document to load.`')
        return

    tmp = await reply.download_media(file=bytes)
    name = reply.document.attributes[0].file_name.split('.')[-2]
    try:
        pmanager._import_plugin(name, 'githubusercontent.com/TG/media', tmp)
        for plugin in pmanager.active_plugins:
            if plugin.name == name:
                for callback in plugin.callbacks:
                    client.add_event_handler(callback.callback)
                    LOGGER.debug(
                        "Added event handler for %s.", callback.callback.__name__
                    )
                    break
        await event.answer(f'`Successfully loaded {name}.`')
    except:
        await event.answer(f'`Failed to load {name}.`')
