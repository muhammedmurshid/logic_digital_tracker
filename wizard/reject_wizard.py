from odoo import models,fields,api
from odoo.exceptions import UserError

class RejectWizard(models.TransientModel):
    _name = "digital.reject.wizard"
    reject_reason = fields.Html(string="Reason")
    digital_task_id = fields.Many2one('digital.task',string="Digital Task",required=True, default = lambda self: self.env.context.get('active_id'))

    def action_reject(self):
        reject_reason = self.reject_reason
        reject_reason = reject_reason[0:2]+' style="color:red;" ' + reject_reason[2:]
        # raise UserError(reject_reason)
        self.reject_reason = reject_reason
        self.digital_task_id.message_post(body=f"Task Rejected by {self.digital_task_id.task_head.name}. <br/>Reason: {self.reject_reason}")
        
        self.digital_task_id.activity_ids.unlink()
        self.digital_task_id.activity_schedule('logic_digital_tracker.mail_activity_type_digital_task', user_id=self.digital_task_id.task_creator.id,
            # date_deadline=self.date_deadline,
            summary=f'Task Rejected by {self.digital_task_id.task_head.name}. Please review the task details after checking the reason for rejection')
        self.digital_task_id.write({
            'state':'rejected'
        })