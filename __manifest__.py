{
    'name': "Digital Requirements",
    'author': 'Rizwaan',
    'version': "14.0.1.0",
    'sequence': "0",
    'depends': ['base','mail','logic_base','faculty'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/digital_task_views.xml',
        'wizard/wizard_views.xml',
        'data/activity.xml',

    ],
    'demo': [],
    'summary': "Digital Requirements",
    'description': "",
    'installable': True,
    'auto_install': False,
    'license': "LGPL-3",
    'application': True
}