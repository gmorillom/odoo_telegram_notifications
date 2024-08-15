# -*- coding: utf-8 -*-
{
    'name': "telegram_notifications",

    'summary':"Notifications with the Telegram messaging application",

    'description': """
        Long description of module's purpose
    """,

    'author': "gmorillom",
    "maintainer": ['gmorillom'],
    'website': "https://github.com/gmorillom",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Technical Settings',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'mail'
    ],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/sms_log.xml',
        'views/views.xml',
        'views/bots.xml',
        'views/issues.xml'
    ],
    
}