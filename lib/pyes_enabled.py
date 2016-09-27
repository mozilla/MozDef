import os

global pyes_on
pyes_off = os.environ.get('DSL')

if pyes_off == 'True':
    pyes_on = False
    print "\nUsing Elasticsearch DSL\n"
else:
    pyes_on = True
    print "\nUsing PYES\n"