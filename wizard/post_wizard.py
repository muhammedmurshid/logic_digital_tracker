from odoo import fields, models, api

class PostWizard(models.Model):
    _name="digital.post.wizard"
    social_manager = fields.Many2many('res.users',string="Social Manager",domain=lambda self: [('id', 'in', self.env.ref('logic_digital_tracker.group_social_manager').users.ids)], required=True)
    date_to_post = fields.Date(string="Date to Post", required=True)
    digital_task_id = fields.Many2one('digital.task',string="Digital Task",required=True, default = lambda self: self.env.context.get('active_id'))

    def action_send_post(self):
        self.digital_task_id.write({
            'social_manager': self.social_manager.id,
            'date_to_post': self.date_to_post,
            'state': 'to_post',

        })