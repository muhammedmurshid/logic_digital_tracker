from odoo import fields, models, api
from datetime import datetime


class CurrentMonthBirthdays(models.Model):
    _name = 'current.month.birthdays'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'display_name'

    date_of_birth = fields.Date(string="Date of Birth")
    month_of_birth = fields.Char(string="Month of Birth")
    employee_id = fields.Many2one('hr.employee', string="Employee")

    def daily_checking_employees_birthday(self):
        today = datetime.today()
        this_month = today.month
        print(this_month, 'this month')

        partners = self.env['hr.employee'].sudo().search([])
        for partner in partners:
            if partner.birthday:
                if partner.birthday.month == this_month:
                    print(partner.birthday.month, partner.name, 'this month')
                    record = self.env['current.month.birthdays'].search(
                        [('employee_id', '=', partner.id)])

                    if not record:
                        self.env['current.month.birthdays'].create(
                            {'employee_id': partner.id, 'date_of_birth': partner.birthday,
                             'month_of_birth': partner.birthday.month})
        rec = self.env['current.month.birthdays'].search([])
        for recs in rec:
            print(recs.date_of_birth.month, 'birth month')
            if recs.date_of_birth.month != this_month:
                recs.unlink()

                # partner.message_post(body="This partner's birth month is this month!"
                # partner.message_post(body="This partner's birth month is this month!")

    def _compute_display_name(self):
        for i in self:
            if i.employee_id:
                i.display_name = i.employee_id.name + ' - ' + 'Birthday'



class HrLeave(models.Model):
    _inherit = 'hr.leave'

    resource_off_reason = fields.Char(string="Resource Off Reason")
