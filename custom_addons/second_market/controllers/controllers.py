# -*- coding: utf-8 -*-
# from odoo import http


# class SecondMarket(http.Controller):
#     @http.route('/second_market/second_market', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/second_market/second_market/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('second_market.listing', {
#             'root': '/second_market/second_market',
#             'objects': http.request.env['second_market.second_market'].search([]),
#         })

#     @http.route('/second_market/second_market/objects/<model("second_market.second_market"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('second_market.object', {
#             'object': obj
#         })

