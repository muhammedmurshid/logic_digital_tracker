from odoo import fields, models, api

class MailActivityInherit(models.Model):
    _inherit="mail.activity"
    # digital_task_id = fields.Many2one('digital.task',string="Digital Task")
    is_digital_assigned_activity = fields.Boolean()