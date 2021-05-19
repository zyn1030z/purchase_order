import base64

import xlrd

from odoo import models, fields, _
from odoo.exceptions import ValidationError


class ImportXLS(models.TransientModel):
    _name = 'import.xls.wizard'
    # your file will be stored here:
    xls_file = fields.Binary(string='File Excel', required=True)

    def import_xls(self):
        amount = self.env.context.get('current_id')
        try:
            wb = xlrd.open_workbook(file_contents=base64.decodestring(self.xls_file))
        except:
            raise ValidationError(
                'File import phải là file excel')
        # try:
        #     product_id_in_datas = self.env['purchase.order.line'].search(
        #         [('order_request_id', '=', self.id)]).product_id  # product_id trong database
        # except:
        #     raise ValidationError(
        #         'Lỗi')
        # mã sản phẩm trong data base
        exist_product_list = []
        # mã code trong file excel
        exist_code_list = []
        # for product_id_in_data in product_id_in_datas:
        #     exist_product_list.append(product_id_in_data.id)
        for sheet in wb.sheets():
            arr_line_error_slsp = []
            arr_line_error_not_exist_database = []
            values = []
            line_check_exist_data = 7
            line_check_slsp = 7

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
            for val in values[6:]:
                product_id_import = self.env['product.product'].search(
                    [('default_code', '=', val[0])]).id  # product_id trong file import
                if product_id_import is False:
                    arr_line_error_not_exist_database.append(line_check_exist_data)
                line_check_exist_data += 1

            # kiểm tra số lượng sản phẩm lớn hơn 0
            for val in values[6:]:
                if not val[3]:
                    arr_line_error_slsp.append(line_check_slsp)
                elif float(val[3]) < 0:
                    arr_line_error_slsp.append(line_check_slsp)
                line_check_slsp += 1

            # kiểm tra đơn vị tính
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
            listToStr_line_slsp = ' , '.join([str(elem) for elem in arr_line_error_slsp])
            listToStr_line_not_exist_database = ' , '.join([str(elem) for elem in arr_line_error_not_exist_database])
            listToStr_line_dvt = ' , '.join([str(elem) for elem in arr_line_error_dvt])
            if len(arr_line_error_not_exist_database) == 0 and len(arr_line_error_dvt) == 0 and len(
                    arr_line_error_slsp) == 0:
                exist_products_in_line = self.env['purchase.order.line'].search([('order_id', '=', amount)])
                exist_products_in_line_arr = []
                for pr_in_line in exist_products_in_line:
                    exist_products_in_line_arr.append(pr_in_line.product_id.default_code)
                arr = []
                for r in exist_products_in_line_arr:
                    if r not in arr:
                        arr.append(r)
                print('Sản phẩm tồn tại trong bảng chi tiết', exist_products_in_line_arr)
                print('Sản phẩm tồn tại ', arr)

                for val in values[6:]:
                    # lấy mã id sản phẩm muốn import
                    product_id_import = self.env['product.product'].search(
                        [('default_code', '=', val[0])]).id
                    if len(exist_products_in_line_arr) != 0:
                        # kiểm tra xem mã code trong file exel tồn tại trong bảng chi tiết không
                        if val[0] in arr:
                            for pr in arr:
                                # th1 : trùng mã code, không có giá trị đơn giá, đơn giá trên bảng chi tiết tạo tự động  ----> gộp
                                # if val[0] == pr:
                                #     # print(
                                #     #     'trùng mã code, không có giá trị đơn giá, đơn giá trên bảng chi tiết tạo tự động')
                                #     id_product_exist = self.env['product.product'].search(
                                #         [('default_code', '=', val[0])]).id
                                #     # số record bản ghi trùng nhau mã sản phẩm
                                #     rc_purchase_order_line_exist_list = self.env['purchase.order.line'].search(
                                #         [('product_id', '=', id_product_exist), ('order_id', '=', amount)])
                                #
                                #     for rc in rc_purchase_order_line_exist_list:
                                #         print(rc.id)
                                #
                                #     product_id_import_standard = self.env['product.product'].search(
                                #         [('default_code', '=', val[0])]).product_tmpl_id.id
                                #     standard_price = self.env['product.template'].search(
                                #         [('id', '=', product_id_import_standard)]
                                #     ).standard_price
                                #     print(rc_purchase_order_line_exist_list)
                                #     for rc_purchase_order_line_exist in rc_purchase_order_line_exist_list:
                                #         # không có đơn giá
                                #         if not val[4]:
                                #             # kiểm tra xem đơn giá trên bảng chi tiết có mặc định không, nếu không thì tạo mới bảng ghi
                                #             if rc_purchase_order_line_exist.price_unit == standard_price:
                                #                 print('test1')
                                #                 product_quanty = rc_purchase_order_line_exist.product_qty + float(
                                #                     val[3])
                                #                 rc_purchase_order_line_exist.write({'product_qty': product_quanty})
                                #             else:
                                #                 # th2 : trùng mã code, không có giá trị đơn giá, đơn giá trên bảng chi tiết chỉnh sửa  ---->  không gộp
                                #                 val[4] = standard_price
                                #                 print('test2')
                                #                 self.env['purchase.order.line'].create(
                                #                     {'price_unit': float(val[4]), 'product_qty': float(val[3]),
                                #                      'order_id': amount,
                                #                      'product_id': product_id_import})
                                #                 self.env.cr.commit()
                                #         elif float(val[4]) == rc_purchase_order_line_exist.price_unit:
                                #             print('test3')
                                #             product_quanty = rc_purchase_order_line_exist.product_qty + float(val[3])
                                #             rc_purchase_order_line_exist.write({'product_qty': product_quanty})
                                #         elif float(val[4]) != rc_purchase_order_line_exist.price_unit:
                                #             print('test4')
                                #             self.env['purchase.order.line'].create(
                                #                 {'price_unit': float(val[4]), 'product_qty': float(val[3]),
                                #                  'order_id': amount,
                                #                  'product_id': product_id_import})
                                #             self.env.cr.commit()
                                if val[0] == pr:
                                    id_product_exist = self.env['product.product'].search(
                                        [('default_code', '=', val[0])]).id
                                    rc_purchase_order_line_exist_list = self.env['purchase.order.line'].search(
                                        [('product_id', '=', id_product_exist), ('order_id', '=', amount)])
                                    product_id_import_standard = self.env['product.product'].search(
                                        [('default_code', '=', val[0])]).product_tmpl_id.id
                                    standard_price = self.env['product.template'].search(
                                        [('id', '=', product_id_import_standard)]
                                    ).standard_price
                                    print(rc_purchase_order_line_exist_list)
                                    print("=======")
                                    for rc_purchase_order_line_exist in rc_purchase_order_line_exist_list:
                                        print('Đơn giá của record', rc_purchase_order_line_exist.price_unit)
                                        print('Đơn giá trên file excel', val[4])
                                        print("---------")
                                            # tạo 1 mảng lưu đơn giá mã code giống nhau
                                            # if rc_purchase_order_line_exist.price_unit == standard_price:
                                            #     print('test1')
                                            #     product_quanty = rc_purchase_order_line_exist.product_qty + float(
                                            #         val[3])
                                            #     rc_purchase_order_line_exist.write({'product_qty': product_quanty})
                                            #     break
                                            # else:
                                            #     # th2 : trùng mã code, không có giá trị đơn giá, đơn giá trên bảng chi tiết chỉnh sửa  ---->  không gộp
                                            #     # val[4] = standard_price
                                            #     print('test2')
                                            #     self.env['purchase.order.line'].create(
                                            #         {'price_unit': standard_price, 'product_qty': float(val[3]),
                                            #          'order_id': amount,
                                            #          'product_id': product_id_import})
                                            #     self.env.cr.commit()
                                            #     break
                                    #     elif float(val[4]) == rc_purchase_order_line_exist.price_unit:
                                    #         print('write')
                                    #         product_quanty = rc_purchase_order_line_exist.product_qty + float(val[3])
                                    #         rc_purchase_order_line_exist.write({'product_qty': product_quanty})
                                    #         break
                                    # self.env['purchase.order.line'].create(
                                    #     {'price_unit': float(val[4]), 'product_qty': float(val[3]),
                                    #      'order_id': amount,
                                    #      'product_id': product_id_import})
                                    # print('write1')
                                    # self.env.cr.commit()
                        else:
                            if not val[4]:
                                # lấy đơn giá rồi gán vào val[4]
                                product_id_import_standard = self.env['product.product'].search(
                                    [('default_code', '=', val[0])]).product_tmpl_id.id
                                standard_price = self.env['product.template'].search(
                                    [('id', '=', product_id_import_standard)]
                                ).standard_price
                                val[4] = standard_price
                                self.env['purchase.order.line'].create(
                                    {'price_unit': float(val[4]), 'product_qty': float(val[3]), 'order_id': amount,
                                     'product_id': product_id_import})
                                self.env.cr.commit()
                            else:
                                print('test5')
                                self.env['purchase.order.line'].create(
                                    {'price_unit': float(val[4]), 'product_qty': float(val[3]), 'order_id': amount,
                                     'product_id': product_id_import})
                                self.env.cr.commit()
                    elif not val[4]:
                        # lấy đơn giá rồi gán vào val[4]
                        product_id_import_standard = self.env['product.product'].search(
                            [('default_code', '=', val[0])]).product_tmpl_id.id
                        standard_price = self.env['product.template'].search(
                            [('id', '=', product_id_import_standard)]
                        ).standard_price
                        val[4] = standard_price
                        self.env['purchase.order.line'].create(
                            {'price_unit': float(val[4]), 'product_qty': float(val[3]), 'order_id': amount,
                             'product_id': product_id_import})
                        self.env.cr.commit()
                    else:
                        print('test5')
                        self.env['purchase.order.line'].create(
                            {'price_unit': float(val[4]), 'product_qty': float(val[3]), 'order_id': amount,
                             'product_id': product_id_import})
                        self.env.cr.commit()
                    # th1 : trùng mã code, không có giá trị đơn giá, đơn giá trên bảng chi tiết tạo tự động  ----> gộp
                    # th2 : trùng mã code, không có giá trị đơn giá, đơn giá trên bảng chi tiết chỉnh sửa  ---->  không gộp
                    # th3 : trùng mã code, đơn giá khác nhau giữa file excel và trên bảng chi tiết ---> không gộp

                    # self.env['purchase.order.line'].create(
                    #     {'price_unit': float(val[4]), 'product_qty': float(val[3]), 'order_id': amount,
                    #      'product_id': product_id_import})
                    # self.env.cr.commit()

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
