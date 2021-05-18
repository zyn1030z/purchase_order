import base64

import xlrd

from odoo import api
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError


class purchase_order_line(models.Model):
    _inherit = "purchase.order"

    def import_xls(self):
        return {
            'name': 'Import file',
            'type': 'ir.actions.act_window',
            'res_model': 'import.xls.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new'
        }

    # def _get_template(self):
    #     self.contract_template = base64.b64encode(open("pur_request/static/xls/imp_donmuahang.xls", "rb").read())
    #
    # contract_template = fields.Binary('Template', compute="_get_template")

    def get_contract_template(self):
        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': 'pur_request/static/xls/imp_donmuahang.xls'

        }