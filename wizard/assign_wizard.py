from odoo import fields, models, api
from datetime import datetime
class AssignWizard(models.TransientModel):
    _name = "digital.task.assign.wizard"

    def get_digital_executives_domain(self):
        digital_execs = self.env.ref('logic_digital_tracker.group_digital_executive').users.ids
        if digital_execs:
            digital_execs.append(self.env.user.id)
            return [('id', 'in', digital_execs)]
        else:
            return [('id','in',[self.env.user.id])]
    assigned_execs = fields.Many2many('res.users',string="Assign to",domain=get_digital_executives_domain, required=True)
    date_deadline = fields.Date(string="Deadline", required=True)
    digital_task_id = fields.Many2one('digital.task',string="Digital Task",required=True, default = lambda self: self.env.context.get('active_id'))
    action_type = fields.Char()
    def action_assign_task(self):
        for exec in self.assigned_execs:
            self.digital_task_id.activity_schedule('logic_digital_tracker.mail_activity_type_digital_task', user_id=exec.id,
                date_deadline=self.date_deadline,
                summary=f'Digital Task from {self.digital_task_id.task_creator.name}',
                note=f"<b>Task:</b> {self.digital_task_id.name}<br/>\
                        <b>Type:</b> {self.digital_task_id.task_type.name}")
        exec_names = ', '.join([exec.name for exec in self.assigned_execs])
        self.digital_task_id.message_post(body=f"Task Assigned to: <b>{exec_names}</b>")

        self.digital_task_id.write(
            {
                'date_assigned': datetime.today(),
                'date_deadline': self.date_deadline,
                'assigned_execs': self.assigned_execs,
                'state': 'assigned',
                'is_assigned': True,
            }
        )

    def action_reassign_task(self):
        for activity_obj in self.digital_task_id.activity_ids:
            activity_obj.unlink()
        old_exec_names = ', '.join([exec.name for exec in self.digital_task_id.assigned_execs])
        new_exec_names = ', '.join([exec.name for exec in self.assigned_execs])
        self.digital_task_id.write(
            {
                'date_assigned': datetime.today(),
                'date_deadline': self.date_deadline,
                'assigned_execs': self.assigned_execs,
                'state': 'assigned',
                'is_assigned': True,
            }
        )
        self.digital_task_id.message_post(body=f"Task Re-assigned from: <b>{old_exec_names}</b>  to: <b>{new_exec_names}</b>")
        for exec in self.assigned_execs:
            self.digital_task_id.activity_schedule('logic_digital_tracker.mail_activity_type_digital_task', user_id=exec.id,
                date_deadline=self.date_deadline,
                summary=f'Digital Task from {self.digital_task_id.task_creator.name}')
