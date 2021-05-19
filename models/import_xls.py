import base64

import xlrd

from odoo import models, fields, _
from odoo.exceptions import ValidationError


class ImportXLS(models.TransientModel):
    _name = 'import.xls.wizard'
    xls_file = fields.Binary(string='File Excel', required=True)

    def check_exist_product_in_database(self, values):
        arr_line_error_not_exist_database = []
        line_check_exist_data = 7
        for val in values[6:]:
            product_id_import = self.env['product.product'].search(
                [('default_code', '=', val[0])]).id  # product_id trong file import
            if product_id_import is False:
                arr_line_error_not_exist_database.append(line_check_exist_data)
            line_check_exist_data += 1
        return arr_line_error_not_exist_database

    def _check_product_qty_in_excel(self, values):
        arr_line_error_slsp = []
        line_check_slsp = 7
        for val in values[6:]:
            if not val[3]:
                arr_line_error_slsp.append(line_check_slsp)
            elif float(val[3]) < 0:
                arr_line_error_slsp.append(line_check_slsp)
            line_check_slsp += 1
        return arr_line_error_slsp

    def _check_uom_product_in_excel(self, values):
        arr_line_error_dvt = []
        line_check_dvt = 7
        for val in values[6:]:
            if not val[2]:
                # kiểm tra nếu k có đơn vị tính thì gán theo hệ thống
                product_id_import_standard = self.env['product.product'].search(
                    [('default_code', '=', val[0])]).product_tmpl_id.id
                uom = self.env['product.template'].search(
                    [('id', '=', product_id_import_standard)]
                ).uom_id
                val[2] = uom.name
                line_check_dvt += 1
            elif val[2]:
                arr_dvt = self.env['uom.uom'].search([('name', '=', val[2])])
                if len(arr_dvt) == 0:
                    arr_line_error_dvt.append(line_check_dvt)
                line_check_dvt += 1
        return arr_line_error_dvt

    def create_product(self, val, price_unit, amount, product_uom, ):
        product_id_import = self.env['product.product'].search(
            [('default_code', '=', val[0])]).id
        self.env['purchase.order.line'].create(
            {'price_unit': price_unit, 'product_qty': float(val[3]), 'order_id': amount,
             'product_id': product_id_import, 'product_uom': product_uom})
        self.env.cr.commit()

    def import_xls(self):
        amount = self.env.context.get('current_id')
        try:
            wb = xlrd.open_workbook(file_contents=base64.decodestring(self.xls_file))
        except:
            raise ValidationError(
                'File import phải là file excel')
        for sheet in wb.sheets():
            values = []
            for row in range(sheet.nrows):
                col_values = []
                for col in range(sheet.ncols):
                    value = sheet.cell(row, col).value
                    try:
                        value = str(value)
                    except:
                        pass
                    col_values.append(value)
                values.append(col_values)

            # kiểm tra số sp k tồn tại trong database
            arr_line_error_not_exist_database = self.check_exist_product_in_database(values)

            # kiểm tra số lượng sản phẩm lớn hơn 0
            arr_line_error_slsp = self._check_product_qty_in_excel(values)

            # kiểm tra đơn vị tính
            arr_line_error_dvt = self._check_uom_product_in_excel(values)

            listToStr_line_slsp = ' , '.join([str(elem) for elem in arr_line_error_slsp])
            listToStr_line_not_exist_database = ' , '.join([str(elem) for elem in arr_line_error_not_exist_database])
            listToStr_line_dvt = ' , '.join([str(elem) for elem in arr_line_error_dvt])
            if len(arr_line_error_not_exist_database) == 0 and len(arr_line_error_dvt) == 0 and len(
                    arr_line_error_slsp) == 0:
                exist_products_in_line = self.env['purchase.order.line'].search([('order_id', '=', amount)])

                # tạo mảng lưu mã sản phẩm trong bảng chi tiết ex : [code1, code1, code2]
                exist_products_in_line_arr = []
                for pr_in_line in exist_products_in_line:
                    exist_products_in_line_arr.append(pr_in_line.product_id.default_code)

                # tạo mảng lưu mã sản phẩm trong bảng chi tiết không lặp lại ex : [code1, code2]
                arr = []
                for r in exist_products_in_line_arr:
                    if r not in arr:
                        arr.append(r)
                for val in values[6:]:
                    # lấy mã id sản phẩm muốn import
                    product_id_import = self.env['product.product'].search(
                        [('default_code', '=', val[0])]).id
                    uom_unit = val[2]
                    print('uom_unit', uom_unit)
                    if len(arr) != 0:
                        # kiểm tra xem mã code trong file exel tồn tại trong bảng chi tiết không
                        if val[0] in arr:
                            id_product_exist = self.env['product.product'].search(
                                [('default_code', '=', val[0])]).id
                            rc_purchase_order_line_exist_list = self.env['purchase.order.line'].search(
                                [('product_id', '=', id_product_exist), ('order_id', '=', amount)])
                            product_id_import_standard = self.env['product.product'].search(
                                [('default_code', '=', val[0])]).product_tmpl_id.id
                            standard_price = self.env['product.template'].search(
                                [('id', '=', product_id_import_standard)]
                            ).standard_price
                            price_unit_arr_exist = []
                            for rc_purchase_order_line_exist in rc_purchase_order_line_exist_list:
                                price_unit_arr_exist.append(rc_purchase_order_line_exist.price_unit)
                            if not val[4]:
                                if standard_price in price_unit_arr_exist:
                                    # có tồn tại, tìm dòng đó và ghi đè
                                    for rc_purchase_order_line_exist in rc_purchase_order_line_exist_list:
                                        if rc_purchase_order_line_exist.price_unit == standard_price:
                                            product_quanty = rc_purchase_order_line_exist.product_qty + float(
                                                val[3])
                                            rc_purchase_order_line_exist.write({'product_qty': product_quanty})
                                else:
                                    self.create_product(val, standard_price, amount, 2)

                            elif float(val[4]) in price_unit_arr_exist:
                                for rc_purchase_order_line_exist in rc_purchase_order_line_exist_list:
                                    if rc_purchase_order_line_exist.price_unit == float(val[4]):
                                        product_quanty = rc_purchase_order_line_exist.product_qty + float(val[3])
                                        rc_purchase_order_line_exist.write({'product_qty': product_quanty})
                            else:
                                self.create_product(val, float(val[4]), amount, 2)

                        # nếu mã code không có trong file exel, tạo mới
                        else:
                            if not val[4]:
                                # lấy đơn giá rồi gán vào val[4]
                                product_id_import_standard = self.env['product.product'].search(
                                    [('default_code', '=', val[0])]).product_tmpl_id.id
                                standard_price = self.env['product.template'].search(
                                    [('id', '=', product_id_import_standard)]
                                ).standard_price
                                self.create_product(val, standard_price, amount, 2)

                            else:
                                print('test5')
                                self.create_product(val, float(val[4]), amount, 2)
                    elif not val[4]:
                        # lấy đơn giá rồi gán vào val[4]
                        product_id_import_standard = self.env['product.product'].search(
                            [('default_code', '=', val[0])]).product_tmpl_id.id
                        standard_price = self.env['product.template'].search(
                            [('id', '=', product_id_import_standard)]
                        ).standard_price
                        self.create_product(val, standard_price, amount, 2)
                    else:
                        print('test5')
                        self.create_product(val, float(val[4]), amount, 2)

            elif len(arr_line_error_not_exist_database) != 0 and len(arr_line_error_dvt) == 0 and len(
                    arr_line_error_slsp) == 0:
                raise ValidationError(
                    _('Sản phẩm không tồn tại trong hệ thống, dòng (%s)') % str(listToStr_line_not_exist_database))
            elif len(arr_line_error_not_exist_database) != 0 and len(arr_line_error_dvt) != 0 and len(
                    arr_line_error_slsp) == 0:
                raise ValidationError(
                    _('Mã sản phẩm không tồn tại trong hệ thống, dòng (%s)\n'
                      'Đơn vị tính của sản phẩm phải cùng nhóm đơn vị tính đã khai báo, dòng (%s)') % (str(
                        listToStr_line_not_exist_database), str(
                        listToStr_line_dvt)))
            elif len(arr_line_error_not_exist_database) != 0 and len(arr_line_error_dvt) != 0 and len(
                    arr_line_error_slsp) != 0:
                raise ValidationError(
                    _('Mã sản phẩm không tồn tại trong hệ thống, dòng (%s)\n'
                      'Đơn vị tính của sản phẩm phải cùng nhóm đơn vị tính đã khai báo, dòng (%s)\n'
                      'Số lượng sản phẩm phải lớn hơn 0 hoặc không để trống, dòng (%s)')
                    % (str(listToStr_line_not_exist_database),
                       str(listToStr_line_dvt),
                       str(listToStr_line_slsp)))
            elif len(arr_line_error_not_exist_database) == 0 and len(arr_line_error_dvt) != 0 and len(
                    arr_line_error_slsp) == 0:
                raise ValidationError(
                    _('Đơn vị tính của sản phẩm phải cùng nhóm đơn vị tính đã khai báo, dòng (%s)') % str(
                        listToStr_line_dvt))
            elif len(arr_line_error_not_exist_database) == 0 and len(arr_line_error_dvt) == 0 and len(
                    arr_line_error_slsp) != 0:
                raise ValidationError(
                    _('Số lượng sản phẩm phải lớn hơn 0 hoặc không để trống, dòng (%s)') % str(listToStr_line_slsp))
            elif len(arr_line_error_not_exist_database) == 0 and len(arr_line_error_dvt) != 0 and len(
                    arr_line_error_slsp) != 0:
                raise ValidationError(
                    _(
                        'Số lượng sản phẩm phải lớn hơn 0 hoặc không để trống, dòng (%s)\n'
                        'Đơn vị tính của sản phẩm phải cùng nhóm đơn vị tính đã khai báo, dòng (%s)') % (str(
                        listToStr_line_slsp), str(listToStr_line_dvt)))
            elif len(arr_line_error_not_exist_database) != 0 and len(arr_line_error_dvt) == 0 and len(
                    arr_line_error_slsp) != 0:
                raise ValidationError(
                    _('Mã sản phẩm không tồn tại trong hệ thống, dòng (%s)\n'
                      'Số lượng sản phẩm phải lớn hơn 0 hoặc không để trống, dòng (%s)')
                    % (str(listToStr_line_not_exist_database),
                       str(listToStr_line_slsp)))
