import os

global pyes_on
pyes_off = os.environ.get('DSL')

# We're gonna short circuit and turn off pyes
pyes_off = 'True'
if pyes_off == 'True':
    pyes_on = False
    print "\nUsing Elasticsearch DSL\n"
else:
    pyes_on = True
    print "\nUsing PYES\n"