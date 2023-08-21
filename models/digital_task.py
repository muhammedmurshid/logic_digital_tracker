from odoo import models,fields,api
from odoo.exceptions import UserError
from datetime import datetime
class DigitalTask(models.Model):
    _name = "digital.task"
    # _rec_name = "name"
    _description = "Digital Task"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(string="Name")
    task_type = fields.Many2one('digital.task.type',string="Task Type",required=True)
    
    def _compute_display_name(self):
        for record in self:
            if record.assigned_execs:
                name = record.name + ": "
                for exec in record.assigned_execs:
                    name+= exec.name+", "
                name = name[0:len(name)-2]
                record.display_name = name
            else:
                record.display_name = record.name
    display_name = fields.Char(compute="_compute_display_name")
    
    task_head = fields.Many2one('res.users',string="Digital Head", required=True,domain=lambda self:  [('id', 'in', self.env.ref('logic_digital_tracker.group_digital_head').users.ids)])
    assigned_execs = fields.Many2many('res.users',string="Assigned To",domain=lambda self: [('id', 'in', self.env.ref('logic_digital_tracker.group_digital_executive').users.ids)])
    
    def _compute_execs_display(self):
        for record in self:
            if not record.assigned_execs:
                record.execs_display = ''
            else:
                name=""
                for exec in record.assigned_execs:
                    name+= exec.name + ", "
                name = name[0:len(name)-2]
                record.execs_display = name
    execs_display = fields.Char(compute="_compute_execs_display")
    
    task_creator = fields.Many2one('res.users',string="Task Creator", default= lambda self: self.env.user.id)
    description = fields.Text(string="Description")
    state = fields.Selection(string="Status", selection=[('1_draft','Draft'),('sent_to_approve','Sent to Approve'),('approved','Approved'),('assigned','Assigned'),('in_progress','In Progress'),('completed','Completed'),('to_post','To Post'),('posted','Posted'),('cancelled','Cancelled')], default=False)
    tags_ids = fields.Many2many('project.tags', string='Tags')
    priority = fields.Selection([
        ('normal', 'Normal'), ('urgent', 'Urgent')
    ], string='Priority', default='normal')
    is_assigned = fields.Boolean()
    expected_date = fields.Date(string="Expected Date", required=True)
    date_assigned = fields.Date(string="Task Assigned On",readonly=True)
    date_completed = fields.Date(string="Date of Completion")
    date_deadline = fields.Date(string="Deadline",readonly=True)
    social_manager = fields.Many2one('res.users',string="Social Media Manager", domain=lambda self: [('id', 'in', self.env.ref('logic_digital_tracker.group_social_manager').users.ids)])
    date_to_post = fields.Date(string="Date to Post",)
    date_posted = fields.Date(string="Posted On")
    fold = fields.Boolean(compute="_compute_fold")

    def _compute_fold(self):
        for record in self:
            if record.state in ('cancelled','posted'):
                record.fold = True
            else:
                record.fold = False

    @api.model
    def create(self,vals):
        vals['state'] = '1_draft'
        return super(DigitalTask,self).create(vals)
    
    def action_confirm(self):
        self.message_post(body=f"Status Changed: Draft -> Sent to Approve")
        self.activity_schedule('logic_digital_tracker.mail_activity_type_digital_task', user_id=self.task_head.id,
                               summary=f'To Approve: Digital Task from {self.task_creator.name}')
        self.state = 'sent_to_approve'
    
    def action_cancel(self):
        activity_obj = self.env['mail.activity'].search([('res_id','=',self.id)])
        if activity_obj:
            activity_obj.action_feedback(feedback=f"Task Cancelled")
        current_status = dict(self._fields['state']._description_selection(self.env))[self.state]
        self.message_post(body=f"Status Changed: {current_status} -> Cancelled")
        self.state = 'cancelled'

    def action_approve(self):
        activity_obj = self.env['mail.activity'].search([('res_id','=',self.id)])
        activity_obj.action_feedback(feedback=f"Task Approved")
        self.state = 'approved'
    
    def action_assign(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Task',
            'res_model': 'digital.task.assign.wizard',
            'view_mode': 'form',
            'target': 'new',
            # 'context': {'}
        }
    
        # if len(self.assigned_execs)>0:
        #     for exec in self.assigned_execs:
        #         self.activity_schedule('logic_digital_tracker.mail_activity_type_digital_task', user_id=exec.id,
        #             summary=f'Digital Task from {self.task_creator.name}')
        #     self.state = 'assigned'
        #     self.is_assigned = True
        # else:
        #     raise UserError("You have to assign atleast one Executive")
        
    def action_in_progress(self):
        self.message_post(body=f"Status Changed: Assigned -> In Progress")

        self.state  = 'in_progress'

    def action_complete(self):
        activity_objs = self.env['mail.activity'].search([('res_id','=',self.id)])
        for activity_obj in activity_objs:
            activity_obj.action_feedback(feedback=f"Task Completed")

        self.message_post(body=f"Status Changed: In Progress -> Completed")
        self.state = 'completed'
        self.date_completed = datetime.today()

    def action_revert_to_in_progress(self):
        self.message_post(body=f"Status Changed: Completed -> In Progress")
        for exec in self.assigned_execs:
            self.activity_schedule('logic_digital_tracker.mail_activity_type_digital_task', user_id=exec.id,
                date_deadline=self.date_deadline,
                summary=f'Digital Task from {self.task_creator.name}')

        self.state = 'in_progress'
        self.date_completed = False


    def action_send_to_post(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Send to Post',
            'res_model': 'digital.post.wizard',
            'view_mode': 'form',
            'target': 'new',
            # 'context': {'}
        }

    def action_social_post(self):
        activity_obj = self.env['mail.activity'].search([('res_id','=',self.id)])
        activity_obj.action_feedback(feedback=f'Posted')
        self.write({
            'state': 'posted',
            'date_posted': datetime.today(),
        })