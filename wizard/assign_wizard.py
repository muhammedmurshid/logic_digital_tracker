from odoo import fields, models, api
from datetime import datetime
class AssignWizard(models.TransientModel):
    _name = "digital.task.assign.wizard"
    assigned_execs = fields.Many2many('res.users',string="Assign to",domain=lambda self: [('id', 'in', self.env.ref('logic_digital_tracker.group_digital_executive').users.ids)], required=True)
    date_deadline = fields.Date(string="Deadline", required=True)
    digital_task_id = fields.Many2one('digital.task',string="Digital Task",required=True, default = lambda self: self.env.context.get('active_id'))

    def action_assign_task(self):
        for exec in self.assigned_execs:
            self.digital_task_id.activity_schedule('logic_digital_tracker.mail_activity_type_digital_task', user_id=exec.id,
                date_deadline=self.date_deadline,
                summary=f'Digital Task from {self.digital_task_id.task_creator.name}')
        self.digital_task_id.write(
            {
                'date_assigned': datetime.today(),
                'date_deadline': self.date_deadline,
                'assigned_execs': self.assigned_execs,
                'state': 'assigned',
                'is_assigned': True,
            }
        )
