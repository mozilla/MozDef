import os

global pyes_on
pyes_on = os.environ.get('PYES')

if pyes_on == 'True':
    pyes_on = True
    print "\nUsing PYES\n"
else:
    pyes_on = False
    print "\nUsing Elasticsearch DSL\n"
