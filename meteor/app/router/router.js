Router.map(function () {
    this.route('home', {
        path: '/',
        template: 'hello',
        layoutTemplate: 'layout'
    });

    this.route('about', {
        path: '/about',
        template: 'about',
        layoutTemplate: 'layout'
    });

    this.route('events', {
        path: '/events/*',
        template: 'hello',
        layoutTemplate: 'layout'
    });

    this.route('incidents', {
        path: '/incidents',
        template: 'incidents',
        layoutTemplate: 'layout'
    });


    this.route('incidentnew', {
        path: '/incidents/new',
        template: 'addincidentform',
        layoutTemplate: 'layout'
    });

    this.route('incidentedit', {
        path: '/incidents/edit',
        template: 'editincidentform',
        layoutTemplate: 'layout'
    });
    
    this.route('logincounts', {
        path: '/logincounts',
        template: 'logincounts',
        layoutTemplate: 'layout'
    });

    this.route('alertssummary', {
        path: '/alerts',
        template: 'alertssummary',
        layoutTemplate: 'layout'
    });
    
    this.route('veris',{
       path: '/veris',
       template:'veristags',
       layoutTemplate: 'layout'
    });
    
    

});


