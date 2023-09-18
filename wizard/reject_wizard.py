from odoo import models,fields,api

class RejectWizard(models.TransientModel):
    _name = "digital.reject.wizard"
    reject_reason = fields.Text(string="Reason")
    digital_task_id = fields.Many2one('digital.task',string="Digital Task",required=True, default = lambda self: self.env.context.get('active_id'))

    def action_reject(self):
        self.digital_task_id.message_post(body=f"Task Rejected by {self.digital_task_id.task_head.name}. Reason: {self.reject_reason}")
        self.digital_task_id.activity_ids.unlink()
        self.digital_task_id.activity_schedule('logic_digital_tracker.mail_activity_type_digital_task', user_id=self.digital_task_id.task_creator.id,
            # date_deadline=self.date_deadline,
            summary=f'Task Rejected by {self.digital_task_id.task_head.name}. Please review the task details after checking the reason for rejection')
        self.digital_task_id.write({
            'state':'rejected'
        })