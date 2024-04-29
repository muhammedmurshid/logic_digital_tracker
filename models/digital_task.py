from odoo import models,fields,api
from odoo.exceptions import UserError
from datetime import datetime
import logging
class DigitalTask(models.Model):
    _name = "digital.task"
    # _rec_name = "name"
    _description = "Digital Task"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(string="Name",required=True)
    task_type = fields.Many2one('digital.task.type',string="Task Type",required=True)
    
    @api.depends('assigned_execs','name')
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
    
    def get_default_digital_head(self):
        head_users_ids = self.env.ref('logic_digital_tracker.group_digital_head').users.ids
        if head_users_ids:
            return head_users_ids[0]
        else:
            return False
    task_head = fields.Many2one('res.users',string="Digital Head", required=True,domain=lambda self:  [('id', 'in', self.env.ref('logic_digital_tracker.group_digital_head').users.ids)], default=get_default_digital_head)
    
    def get_digital_executives_domain(self):
        execs = []
        execs.extend(self.sudo().env.ref('logic_digital_tracker.group_digital_executive').users.ids)
        execs.extend(self.sudo().env.ref('logic_digital_tracker.group_digital_head').users.ids)
        return [('id', 'in', execs)]
    assigned_execs = fields.Many2many('res.users',string="Assigned To",domain=get_digital_executives_domain)
    
    @api.depends('assigned_execs')
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
    execs_display = fields.Char(string="Assigned Executives", compute="_compute_execs_display",store=True)
    
    is_dig_head = fields.Boolean(compute="_compute_is_dig_head")

    def _compute_is_dig_head(self):
        for record in self:
            if self.env.user.has_group('logic_digital_tracker.group_digital_head'):
                record.is_dig_head = True
            else:
                record.is_dig_head = False  
   
    task_creator = fields.Many2one('res.users',string="Task Creator", default= lambda self: self.env.user.id)
    description = fields.Text(string="Description")
    state = fields.Selection(string="Status", selection=[('1_draft','Draft'),('sent_to_approve','Sent to Approve'),('approved','Approved'),('assigned','Assigned'),('in_progress','In Progress'),('completed','Completed'),('to_post','To Post'),('posted','Posted'),('cancelled','Cancelled'),('rejected','Rejected')], default=False)
    tags_ids = fields.Many2many('project.tags', string='Tags')
    priority = fields.Selection([
        ('normal', 'Normal'), ('urgent', 'Urgent')
    ], string='Priority', default='normal')
    is_assigned = fields.Boolean()
    expected_date = fields.Date(string="Expected Date", required=True)
    expected_post_date = fields.Date(string="Expected Post Date")

    date_assigned = fields.Date(string="Task Assigned On",readonly=True)
    date_completed = fields.Date(string="Date of Completion")
    date_deadline = fields.Date(string="Deadline",readonly=True)
    social_manager = fields.Many2one('res.users',string="Social Media Manager", domain=lambda self: [('id', 'in', self.env.ref('logic_digital_tracker.group_social_manager').users.ids)])
    date_to_post = fields.Date(string="Date to Post",)
    date_posted = fields.Date(string="Posted On")
    fold = fields.Boolean(compute="_compute_fold")
    head_rating = fields.Selection(selection=[('0','No rating'),('1','Very Poor'),('2','Poor'),('3','Average'),('4','Good'),('5','Very Good')], string="Head Rating", default='0')
    creator_rating = fields.Selection(selection=[('0','No rating'),('1','Very Poor'),('2','Poor'),('3','Average'),('4','Good'),('5','Very Good')], string="Creator Rating", default='0')
    contributions = fields.One2many("digital.task.contribution","task_id",string="Contributions")
    def _compute_is_task_creator(self):
        for record in self:
            if self.env.user.id == self.task_creator.id:
                record.is_task_creator = True
            else:
                record.is_task_creator = False
    is_task_creator = fields.Boolean(compute="_compute_is_task_creator")

    reach = fields.Integer(string="Reach")


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
    
    def write(self,vals):
        if vals.get('head_rating'):
            if vals['head_rating']!=self.head_rating:
                if self.env.user.id != self.task_head.id:
                    raise UserError("Only the Digital Head can modify the head rating!")
        if vals.get('creator_rating'):
            if vals['creator_rating']!=self.creator_rating:
                if self.env.user.id != self.task_creator.id:
                    raise UserError("Only the Task Creator can modify the creator rating!")
        if vals.get('reach'):
            if vals['reach']!=self.reach:
                if self.env.user.id not in [self.task_head.id,self.social_manager.id]:
                    raise UserError("Only the Digital Head or Social Media manager can update reach!")
        return super(DigitalTask, self).write(vals)

    def action_confirm(self):
        if self.activity_ids:
            self.activity_ids.unlink()
        current_status = dict(self._fields['state']._description_selection(self.env))[self.state]

        self.message_post(body=f"Status Changed: {current_status} -> Sent to Approve")
        self.activity_schedule('logic_digital_tracker.mail_activity_type_digital_task', user_id=self.task_head.id,
                               res_id = self.id,
                               summary=f'To Approve: Digital Task from {self.task_creator.name}')
        self.state = 'sent_to_approve'
    
    def action_cancel(self):
        # activity_obj = self.env['mail.activity'].search([('res_id','=',self.id)])
        if self.activity_ids:
            self.activity_ids.unlink()
        current_status = dict(self._fields['state']._description_selection(self.env))[self.state]
        self.message_post(body=f"Task cancelled by {self.env.user.name}")
        self.message_post(body=f"Status Changed: {current_status} -> Cancelled")
        self.state = 'cancelled'

    def action_approve(self):
        self.activity_ids.unlink()
        self.message_post(body=f"Task Approved by {self.task_head.name}")
        current_status = dict(self._fields['state']._description_selection(self.env))[self.state]
        self.message_post(body=f"Status Changed: {current_status} -> Approved")

        self.state = 'approved'

    def action_suggest(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Suggest Changes',
            'res_model': 'digital.suggestion.wizard',
            'view_mode': 'form',
            'target': 'new',
            # 'context': {'default_action_type':'assign'}
        }

    def action_reject(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Task',
            'res_model': 'digital.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            # 'context': {'default_action_type':'assign'}
        }
    
    def action_assign(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Task',
            'res_model': 'digital.task.assign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_action_type':'assign'}
        }
    
    def action_reassign(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Task',
            'res_model': 'digital.task.assign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_action_type':'reassign'}
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

        # activity_objs = self.env['mail.activity'].search([('res_id','=',self.id)])
        for activity_obj in self.activity_ids:
            activity_obj.unlink()
        self.message_post(body=f"Status Changed: In Progress -> Completed")
        self.state = 'completed'
        self.date_completed = datetime.today()
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Task Completed',
                'type': 'rainbow_man',
            }
        }

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
        # activity_obj = self.env['mail.activity'].search([('res_id','=',self.id)])
        self.activity_ids.unlink()
        self.message_post(body="Posted in Social Media")
        self.write({
            'state': 'posted',
            'date_posted': datetime.today(),
        })

    def action_repost(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ask to Repost',
            'res_model': 'digital.repost.wizard',
            'view_mode': 'form',
            'target': 'new',
            # 'context': {'}
        }
    
class DigitalTaskContribution(models.Model):
    _name = "digital.task.contribution"
    task_id = fields.Many2one("digital.task",string="Digital Task")

    def get_digital_executives_domain(self):
        task = self.env['digital.task'].browse(self.env.context.get('active_id'))
        digital_execs = task.assigned_execs
        execs_domain = []
        logger = logging.getLogger("Debugger: ")
        logger.error("Execs: "+str(task.contributions.mapped('executive')))
        if digital_execs:
            for exec in digital_execs:
                execs_domain.append(exec.id)

        return [('id', 'in', execs_domain),('id','not in',task.contributions.mapped('executive.id'))]
    
    def get_total_percentage(self,records):
        return sum(records.mapped('contribution'))

    @api.onchange("contribution")
    def on_contrib_change(self):
        self.contribution = self.contribution%101
        if self._origin:
            other_contrs = self.env['digital.task.contribution'].search([('task_id','=',self._origin.task_id.id),('id','!=',self._origin.id)])
            total_percs_cur_recs = self.get_total_percentage(other_contrs)
            if (total_percs_cur_recs+self.contribution)>100:
                equal_part = round( (100-self.contribution)/len(other_contrs),2)
                for task_contr in other_contrs:
                    task_contr.write({
                        'contribution':equal_part,
                    })

      

    executive = fields.Many2one('res.users',string="Executive",required=True)
    contribution = fields.Float(string="Contribution (%)")
