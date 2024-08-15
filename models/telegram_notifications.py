# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
from datetime import datetime, timedelta
from math import *

# Maestro de Motivos de alerta de Telegram
class TelegramNotificationIssue(models.Model):
    _name = "telegram.notification.issue"
    _description = 'Motivo de alerta de telegram'

    name = fields.Char(string="Description", required=True,unique=True)
    code = fields.Char(string='Code',required=True,unique=True)
    active = fields.Boolean(string='Active',default=True)
    save_message_in_log = fields.Boolean(string="Write log",default=False)

# Maestro de bots de Telegram
class TelegramNotificationBot(models.Model):
    _name = "telegram.notification.bot"

    name = fields.Char(string='Bot name',required=True)
    telegram_bot_id = fields.Char(string='Telegram Bot ID',required=True)
    issue_ids = fields.Many2many('telegram.notification.issue',required=True)
    active = fields.Boolean(string='Active',default=True)

# Mestro de usuarios de Telegram
class TelegramNotificationUser(models.Model):
    _name = "telegram.notification.user"
    _description = 'User master to send messages by telegram'
    
    name = fields.Char(string="Telegram ID", default=0 , required= True) #solo númerico
    stock = fields.Many2many("stock.warehouse", string="Warehouses" , required= True )
    active = fields.Boolean(default=True,string="Active")
    user_id = fields.Many2one('res.users',string='Odoo user',required=True)
    issue_ids = fields.Many2many('telegram.notification.issue',string='Alert reasons')
    
    @api.onchange('name')
    def _validate_name(self):
        if( not self.name.isnumeric()):
            raise UserError("Telegram ID does not contain letters")
        
# Log de mensajes enviados de Telegram
class TelegramNotificationLogSms(models.Model):
    _name = "telegram.notifications.log.sms"
    _description = 'Record of all messages sent by telegram'
    _order = 'date desc'

    issue_id = fields.Many2one('telegram.notification.issue',string="Reason",required=True)
    user_id = fields.Many2one('res.users',string='Odoo user',required=True)
    date = fields.Date(string="Date",required=True)
    reference = fields.Char(string="Ref.",required=True)
    message = fields.Text(string="Message")