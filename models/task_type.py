from odoo import models,fields,api

class TaskType(models.Model):
    _name="digital.task.type"
    name = fields.Char(string="Name")
    score = fields.Integer(string="Score")