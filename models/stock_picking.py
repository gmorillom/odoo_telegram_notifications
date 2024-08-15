# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
from datetime import datetime, timedelta
from math import *
import logging

_logger = logging.getLogger(__name__)

'''
    Class that extends the stock.picking model by modifying the button_validate and action_confirm methods
    Odoo natives to send the message by telegram. 2 methods are added: sendTelegramMessage and
    buildOrderObject
'''
STOCK_PICKING_ISSUE_CODE = 'stock_picking'

class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'
    
    def process(self):
        res = super(StockBackorderConfirmation,self).process()
        orden = self.pick_ids
        
        action = "send"
        orden.sendTelegramMessage(action)

        action = "receive"
        orden.sendTelegramMessage(action)

        return res
                
class TelegramNotification(models.Model):
    _inherit = "stock.picking"

    '''
        Method that processes the transfer as Done (received), changing its status and blocking
        the transfer, in this state it cannot be modified or deleted
    '''
    def button_validate(self):
        
        resp = super(TelegramNotification,self).button_validate()
        oper =self.picking_type_id.type
        
        if (oper == "internal"):
            if not self._check_backorder():
                action = "send"
                self.sendTelegramMessage(action)
                
                action = "receive"
                self.sendTelegramMessage(action)
        
        return resp

    '''
        Returns an object with the information of the transfer made in the inventory
        The states done, assigned and confirmed have information already confirmed so they are filled
        the object being in one of these states
    '''
    def buildOrderObject(self):

        if not( self.state == 'done' or self.state == 'assigned' or self.state == 'confirmed' ):
            return {}
        
        date = self.scheduled_date 
        date = date - timedelta(hours=4)
        date = date.strftime('%d/%m/%Y %H:%M')

        date2 = datetime.now()
        date2 = date2 - timedelta(hours=4)
        date2 = date2.strftime('%d/%m/%Y %H:%M')
        
        picked = {
            'name':self.name,
            'partner_id': self.partner_id.name,
            'location_id': self.location_id.display_name,
            'location_dest_id': self.location_dest_id.display_name,
            'picking_type_id': self.picking_type_id.name,
            'scheduled_date': date,
            'date_done': date2,
            'owner_id': self.owner_id.name,
            'company_id': self.company_id.name,
            'backorder': self._check_backorder() and self.state == 'done',
            'moves': []
        }

        if self.state == 'done':
            picked['date_done'] = (datetime.now()- timedelta(hours=4)).strftime('%d/%m/%Y %H:%M')
      
        for mv in self.move_ids_without_package:
            
            move = {
                'product_id': mv.product_id.name,
                'product_uom_qty': mv.product_uom_qty,
                'quantity_done': mv.quantity_done,
                'product_uom': mv.product_uom.name,
                'lots_from_products': mv.move_line_ids,
                
            }
            picked['moves'].append(move)
            
        return picked

    '''
        Send a message via HTTP request to consume the Telegram API and notify
        of a pending or completed transfer
    '''

    def sendTelegramMessage(self,action):
        issue_id = self.env['telegram.notification.issue'].search([('active','=',True),('code','=',STOCK_PICKING_ISSUE_CODE)])
        telegram_chat_ids = self.env['telegram.notification.user'].search([('active','=',True)])
        telegram_chat_ids = telegram_chat_ids.filtered( lambda t: len( t.issue_ids.filtered(lambda i: i.code == STOCK_PICKING_ISSUE_CODE) > 0 ) )
        
        # telegram_bot_id = "bot5158330231:AAGrX6GLjtIW5zLPUYvd4Yc86XOAU9-KIt4"
        telegram_bot_id = self.env['telegram.notification.bot'].search([('active','=',True)])
        telegram_bot_id = telegram_bot_id.filtered(lambda t: len( t.issue_ids.filtered(lambda i: i.code == STOCK_PICKING_ISSUE_CODE) ) > 0)
        
        info = self.buildOrderObject()
        
        if bool(info) and telegram_chat_ids and telegram_bot_id and issue_id:     
            if ( info["date_done"] ):
                info["date_done"] = datetime.now()
                info["date_done"] = info["date_done"] - timedelta(hours=4)
                info["date_done"] = info["date_done"].strftime('%d/%m/%Y %H:%M')

            try:
                textMessage = "Referencia: "+info["name"]+ " %0A" 
                # validation if the partner_id does not exist
                if(info["partner_id"]):
                    textMessage = textMessage + " %0A" + "Responsable: "+info["partner_id"]+" %0A"

                textMessage = textMessage + "Ubicación de origen: "+info["location_id"]+" %0A"
                textMessage = textMessage + "Ubicación de destino: "+info["location_dest_id"]+" %0A"
                textMessage = textMessage + "Tipo de operación: "+info["picking_type_id"]+" %0A"
                    
                if (action=="send"):
                    textMessage = textMessage + "Fecha de emisión: "+info["scheduled_date"]+" %0A"
                else:
                    textMessage = textMessage + "Fecha de recepción: "+info["date_done"]+" %0A"

                textMessage = textMessage + "Compañía: "+info["company_id"]+" %0A %0A %0A"

                if info["backorder"]:
                    textMessage = textMessage + "Es una entrega parcial: Si %0A"

                for move in info["moves"]:
                    moveInfo = "Producto: "+move["product_id"]+" "
                                        
                    if (action=="send"):
                        moveInfo = moveInfo + "fueron enviados en total " +str(move["product_uom_qty"])+"%0A"
                        moveInfo = moveInfo + move["product_uom"]+"%0A"

                        if move["product_uom_qty"] == move["quantity_done"]:
                            for record_line in move["lots_from_products"]: 
                                        
                                if(record_line.qty_done == 0):
                                    
                                    moveInfo = moveInfo + "Nro de lote - " + record_line.lot_id.name + "%0A"
                                    date = record_line.lot_id.life_date.strftime('%d/%m/%Y') 
                                    moveInfo = moveInfo + "Con fecha de vencimiento: - " + date + "%0A"
                                else:
                                    nombre = record_line.lot_id.name

                                    if(record_line.lot_id.name and record_line.qty_done and record_line.product_uom_id.name):
                                        moveInfo = moveInfo + "Nro de lote - " + record_line.lot_id.name + " - " + str(record_line.qty_done) + " " + record_line.product_uom_id.name + "%0A"
                                    if(record_line.lot_id.life_date):
                                        date = record_line.lot_id.life_date.strftime('%d/%m/%Y') 
                                        moveInfo = moveInfo + "Con fecha de vencimiento: - " + date + "%0A"
                          
                        moveInfo = moveInfo + "%0A"
                               
                    else:
                        moveInfo = moveInfo + "fueron recibidos en total: "+str(move["product_uom_qty"])+" "
                        moveInfo = moveInfo + move["product_uom"]+"%0A"
                   
                        if move["product_uom_qty"] == move["quantity_done"]:
                            for record_line in move["lots_from_products"]: 
                                        
                                if(record_line.qty_done == 0):
                                    
                                    moveInfo = moveInfo + "Nro de lote - " + record_line.lot_id.name + "%0A"
                                    date = record_line.lot_id.life_date.strftime('%d/%m/%Y') 
                                    moveInfo = moveInfo + "Con fecha de vencimiento: - " + date + "%0A"
                                else:
                                    
                                    if(record_line.lot_id.name and record_line.qty_done and record_line.product_uom_id.name):
                                     moveInfo = moveInfo + "Nro de lote - " + record_line.lot_id.name + " - " + str(record_line.qty_done) + " " + record_line.product_uom_id.name + "%0A"
                                    
                                    if(record_line.lot_id.life_date):
                                        date = record_line.lot_id.life_date.strftime('%d/%m/%Y') 
                                        moveInfo = moveInfo + "Con fecha de vencimiento: - " + date + "%0A"
                                    
                        moveInfo = moveInfo + "%0A"
                        
                    textMessage = textMessage + moveInfo
                    
                try:
                    date = info["scheduled_date"]
                    name= info["company_id"]
                                  
                    for chat_id in telegram_chat_ids:
                        id_t = str(chat_id.name)

                        if (action=="send"):
                            stock_two = info["location_dest_id"]
                            des = "Envio de mercancia desde " + info["location_id"] + " a " + stock_two
                        else:
                            stock_two = info["location_id"]
                            date = info["date_done"]
                            des = "Recepción de mercancia en " + info["location_dest_id"] + " desde " + stock_two
                        
                        # ------------------
                        for alm in chat_id.stock:
                            
                            stock = alm.code + "/"   
                            # --------------------------            
                            if (stock_two.find(stock) != -1 ):

                                # sent message log
                                sms = self.env['telegram.notifications.log.sms'].create({
                                    'issue_id': issue_id.id,
                                    'user_id': chat_id.user_id.id,
                                    'date': fields.Date.context_today(self),
                                    'reference': info["name"],
                                    'message': textMessage if issue_id.save_message_in_log else '',
                                })
                                                                                                        
                                uri = "https://api.telegram.org/"+telegram_bot_id.telegram_bot_id+"/sendMessage?chat_id="+id_t+"&text="+textMessage
                                request = requests.get(uri)                                                                    
                                
                except Exception as e:
                    _logger.error('[SEND TELEGRAM ALERT] %s' %(e))

            except NameError:
                print(NameError)