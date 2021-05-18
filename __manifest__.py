# -*- coding: utf-8 -*-
{
    'name': 'Purchase Request Order',
    'version': '1.0',
    'sequence': 1,
    'summary': 'Odoo 14 Purchase Request',
    'description': """""",
    'category': 'Tutorials',
    'author': 'Hung Pham',
    'maintainer': '',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'purchase',
    ],
    'data': [
        'views/purchase_order_line.xml',
        'views/import_xls.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [],
    'qweb': [],
    'images': [''],
    'installable': True,
    'auto_install': False,
    'application': True,

}
