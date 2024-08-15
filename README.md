# Odoo:odoo_telegram_notifications

####    This module allow you to send telegram notifications from models actions

This module adds a section to configure the notifications that will be sent by Telegram. In the module, system users can register with their Telegram user (ID) to whom the notifications will be sent, the different bots previously created in Telegram that can be used to send the notifications, finally, a master of reasons or motives. of notifications, these are codes to indicate which users can receive a certain alert.

After registering users, bots and reasons, it is necessary to extend those methods that you want to send a notification when they are executed. In this version of the module we extend the function that validates and confirms the `stock pickings` so that a notification is sent for each internal transfer that is made


####    Telegram Considerations

The Telegram API allows you to send messages from a bot configured in the messaging application, for the bot to communicate with a user, the user must have started a conversation with it, otherwise the messages will not be sent. For more information consult the documentation of the [API](https://core.telegram.org/api)