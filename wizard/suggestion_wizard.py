from odoo import models,fields,api

class SuggestionWizard(models.TransientModel):
    _name = "digital.suggestion.wizard"
    suggestion = fields.Html(string="Suggestion")
    digital_task_id = fields.Many2one('digital.task',string="Digital Task",required=True, default = lambda self: self.env.context.get('active_id'))

    def action_suggest(self):
        self.digital_task_id.message_post(body=f"Suggestions by {self.env.user.name}: {self.suggestion}")
        self.digital_task_id.activity_schedule('logic_digital_tracker.mail_activity_type_digital_task', user_id=self.digital_task_id.task_head.id,
            # date_deadline=self.date_deadline,
            summary=f'I have some suggestions for improving {self.digital_task_id.name}. Please review them accordingly')