 /*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
Anthony Verez averez@mozilla.com
 */

if (Meteor.isClient) {
    var note = null;
    var theory = null;
    var mitigation = null;
    var lesson = null;
    var timestamp = null;
    

    Template.veristags.veris=function(){
        return veris.find({tag:{$regex:'.*' +Session.get('verisfilter') + '.*',$options:'i'}},{limit:50});
    };

    Template.veristags.events({
        'dragstart .tag': function(e){
            e.originalEvent.dataTransfer.setData("text/plain",this.tag);
        },
        'load': function(e, template){
            template.find("#tagfilter").value=Session.get('verisfilter');
        },
        'click li': function(e,template){
            Session.set('verisfilter',e.target.textContent);
            template.find("#tagfilter").value=e.target.textContent;
        }
    });
    

    //return all incidents
    Template.incidents.incident = function () {
        return incidents.find({},{
                              sort: {dateOpened: -1}
                            });
    };

    //select an incident for editing
    Template.incidents.events({
        "click .incidentedit": function(e,t){
            if (this._id != undefined){
                //Session.set('displayMessage','Starting edit for incident._id: ' + this._id);
                Router.go('/incident/' + this._id + '/edit');
            }
        },

        "click .incidentdelete": function(e){
            incidents.remove(this._id);
        },

        "mouseenter .info-row": function(e,t){
            //toggle the bootstrap tooltip
            $('[data-toggle="tooltip"]').tooltip({
                'placement': 'top'
            });
        }
    });

    Template.incidents.rendered = function(){
        Deps.autorun(function() {
            Meteor.subscribe("incidents-summary");
        });
        
    };

    //edit events
    Template.editincidentform.events({
        "dragover .tags": function(e){
            e.preventDefault();   //allow the drag  
        },
        "keyup .tagfilter":function(e,template){
            //var letter_pressed = String.fromCharCode(e.keyCode);
            //console.log(template.find("#tagfilter").value);
            Session.set('verisfilter',template.find("#tagfilter").value);
            
        },
        "drop .tags": function(e){
            e.preventDefault();
            tagtext = e.originalEvent.dataTransfer.getData("text/plain");
            //e.target.textContent=droptag
            //console.log(tagtext)
            incidents.update(Session.get('incidentID'), {
                $addToSet: {tags:tagtext}
            });
        },
        
        "click .tagdelete": function(e){
            tagtext = e.target.parentNode.firstChild.wholeText;
            incidents.update(Session.get('incidentID'), {
                $pull: {tags:tagtext}
            });
        },

        "keypress .description, keypress .summary": function (e,t){
            e.stopImmediatePropagation();
            incidentSaveTimer.run(e, t);
        },

        "blur .description, blur .summary": function(e, t) {
            e.stopImmediatePropagation();
            saveIncident(e,t);
        },

        "blur .calendarfield": function(e, t) {
            saveIncident(e,t);
        },

        "change #phase": function(e, t) {
            saveIncident(e,t);
         },

        "click #saveIncident": function(e, template) {
            saveIncident(e,template);
            e.preventDefault();
            e.stopPropagation();
        },

        "click .tabnav": function (e,template){
            //set the tab and tab content to active to display
            //and hide the non active ones.
            $(e.currentTarget).addClass('active').siblings().removeClass('active');
            $(e.target.hash).hide();
            $(e.target.hash).addClass('active').siblings().removeClass('active');
            $(e.target.hash).fadeIn(400);
        },

        "click #saveReference": function(e,template){
            tValue=$('#newReference').val();
            if ( tValue.length > 0 ) {
                incidents.update(Session.get('incidentID'), {
                    $addToSet: {references:tValue}
                });                
            }
            $('#newReference').val('');
        },

        "click .referencedelete": function(e){
            //wholeText if it's not a url,
            //text if it's a url
            if (e.target.parentNode.firstChild.wholeText){
                reftext = e.target.parentNode.firstChild.wholeText
            }else{
                reftext = e.target.parentNode.firstChild.text;
            }
            incidents.update(Session.get('incidentID'), {
                $pull: {references:reftext}
            });
        },
        
        "click #saveTheory": function(e,template){
            if (! theory) {
                theory=models.theory();
                theory.creator=Meteor.user().profile.email;
            }

            theory.summary=$('#theorySummary').val();
            theory.description=$('#theoryDescription').val();
            theory.status=$('#theoryStatus').val();
            theory.lastModifier=Meteor.user().profile.email;

            if ( theory.summary && theory.description ) {
                //limited support for modify a set, so pull/add
                incidents.update(Session.get('incidentID'), {
                    $pull: {theories: {"_id": theory._id}}
                });

                incidents.update(Session.get('incidentID'), {
                    $addToSet: {theories:theory}
                });

                $('#theorySummary').val('');
                $('#theoryDescription').val('');
                $('#theoryStatus').val('');
                theory=null;
                e.preventDefault();
            }

        },

        "click .theoryedit": function(e){
            theory=models.theory();
            theory._id= $(e.target).attr('data-theoryid');
            //elemMatch not available on client side..iterate the items for a match.
            theories=incidents.findOne({'_id':Session.get('incidentID')},
                                  {theories:{$elemMatch:{'_id': theory._id}}},
                                  { "theories.$": 1 }
                                  ).theories;
            theory=_.findWhere(theories, {'_id': theory._id});
            if (theory != undefined) {
                $('#theorySummary').val(theory.summary);
                $('#theoryDescription').val(theory.description);
                $('#theoryStatus').val(theory.status);
            }
            e.preventDefault();
        },        

        "click .theorydelete": function(e){
            id = $(e.target).attr('data-theoryid');
            incidents.update(Session.get('incidentID'), {
                $pull: {theories: {"_id": id}}
            });
            e.preventDefault();
        },

        "click #saveTimestamp": function(e,template){
            if (! timestamp){
                timestamp=models.timestamp();
                timestamp.creator=Meteor.user().profile.email;
            }

            timestamp.timestamp=dateOrNull($('#timestampText').val());
            timestamp.description=$('#timestampDescription').val();
            timestamp.lastModifier=Meteor.user().profile.email;

            if ( timestamp.timestamp && timestamp.description ) {
                //limited support for modify a set, so pull/add
                incidents.update(Session.get('incidentID'), {
                    $pull: {timestamps: {"_id": timestamp._id}}
                });

                incidents.update(Session.get('incidentID'), {
                    $addToSet: {timestamps:timestamp}
                });

                $('#timestampText').val('');
                $('#timestampDescription').val('');
                timestamp=null;
                e.preventDefault();
            }
            
        },

        "click .timestampedit": function(e){
            timestamp=models.timestamp();
            timestamp._id= $(e.target).attr('data-timestampid');
            //elemMatch not available on client side..iterate the items for a match.
            timestamps=incidents.findOne({'_id':Session.get('incidentID')},
                                  {timestamps:{$elemMatch:{'_id': timestamp._id}}},
                                  { "timestamps.$": 1 }
                                  ).timestamps;
            timestamp=_.findWhere(timestamps, {'_id': timestamp._id});
            timestamp._id= $(e.target).attr('data-timestampid');
            if (timestamp != undefined) {
                $('#timestampText').val(timestamp.timestamp);
                $('#timestampDescription').val(timestamp.description);
            }
            e.preventDefault();
        }, 

        "click .timestampdelete": function(e){
            id = $(e.target).attr('data-timestampid');
            incidents.update(Session.get('incidentID'), {
                $pull: {timestamps: {"_id": id}}
            });
            e.preventDefault();
        },

        "click #saveMitigation": function(e,template){
            if (! mitigation ){
                mitigation=models.mitigation();
                mitigation.creator=Meteor.user().profile.email;
            }
            mitigation.summary=$('#mitigationSummary').val();
            mitigation.description=$('#mitigationDescription').val();
            mitigation.status=$('#mitigationStatus').val();
            mitigation.temporary=$('#mitigationTemporary').is(':checked');
            mitigation.lastModifier=Meteor.user().profile.email;

            if ( mitigation.summary && mitigation.description ) {
                //limited support for modify a set, so pull/add
                incidents.update(Session.get('incidentID'), {
                    $pull: {mitigations: {"_id": mitigation._id}}
                });
                incidents.update(Session.get('incidentID'), {
                    $addToSet: {mitigations:mitigation}
                });
                $('#mitigationSummary').val('');
                $('#mitigationDescription').val('');
                $('#mitigationStatus').val('');
                $('#mitigationTemporary').prop('checked', false);
                mitigation=null;
                e.preventDefault();
            }

        },

        "click .mitigationedit": function(e){
            mitigation=models.mitigation();
            mitigation._id= $(e.target).attr('data-mitigationid');
            //elemMatch not available on client side..iterate the items for a match.
            mitigations=incidents.findOne({'_id':Session.get('incidentID')},
                                  {mitigations:{$elemMatch:{'_id': mitigation._id}}},
                                  { "mitigations.$": 1 }
                                  ).mitigations;
            mitigation=_.findWhere(mitigations, {'_id': mitigation._id});
            if (mitigation != undefined) {
                $('#mitigationSummary').val(mitigation.summary);
                $('#mitigationDescription').val(mitigation.description);
                $('#mitigationStatus').val(mitigation.status);
                $('#mitigationTemporary').prop('checked', mitigation.temporary);
            }
            e.preventDefault();
        },         

        "click .mitigationdelete": function(e){
            id = $(e.target).attr('data-mitigationid');
            incidents.update(Session.get('incidentID'), {
                $pull: {mitigations: {"_id": id}}
            });
            e.preventDefault();
        },

        "click #saveLesson": function(e,template){
            if ( ! lesson ){
                lesson=models.lesson();
                lesson.creator=Meteor.user().profile.email;
            }
            lesson.summary=$('#lessonSummary').val();
            lesson.description=$('#lessonDescription').val();
            lesson.lastModifier=Meteor.user().profile.email;

            if ( lesson.summary && lesson.description ) {
                //limited support for modify a set, so pull/add
                incidents.update(Session.get('incidentID'), {
                    $pull: {lessons: {"_id": lesson._id}}
                });
                incidents.update(Session.get('incidentID'), {
                    $addToSet: {lessons:lesson}
                });
                $('#lessonSummary').val('');
                $('#lessonDescription').val('');
                lesson=null;
                e.preventDefault();
            }

        },

        "click .lessonedit": function(e){
            lesson=models.lesson();
            lesson._id= $(e.target).attr('data-lessonid');
            //elemMatch not available on client side..iterate the theories for a match.
            lessons=incidents.findOne({'_id':Session.get('incidentID')},
                                  {lessons:{$elemMatch:{'_id': lesson._id}}},
                                  { "lessons.$": 1 }
                                  ).lessons;
            lesson=_.findWhere(lessons, {'_id': lesson._id});
            if (lesson != undefined) {
                $('#lessonSummary').val(lesson.summary);
                $('#lessonDescription').val(lesson.description);
            }
            e.preventDefault();
        },
        "click .lessondelete": function(e){
            id = $(e.target).attr('data-lessonid');
            incidents.update(Session.get('incidentID'), {
                $pull: {lessons: {"_id": id}}
            });
            e.preventDefault();
        },

        "click #saveNote": function(e,template){
            if (! note){
                note=models.note();
                note.creator=Meteor.user().profile.email;
            }
            note.summary=$('#noteSummary').val();
            note.description=$('#noteDescription').val();
            note.lastModifier=Meteor.user().profile.email;

            if ( note.summary && note.description ) {
                //limited support for modify a set, so pull/add
                incidents.update(Session.get('incidentID'), {
                    $pull: {notes: {"_id": note._id}}
                });                
                incidents.update(Session.get('incidentID'), {
                    $addToSet: {notes:note}
                });
                $('#noteSummary').val('');
                $('#noteDescription').val('');
                note=null;
                e.preventDefault();
            }

        },

        "click .noteedit": function(e){
            note=models.note();
            note._id= $(e.target).attr('data-noteid');
            //elemMatch not available on client side..iterate the theories for a match.
            notes=incidents.findOne({'_id':Session.get('incidentID')},
                                  {notes:{$elemMatch:{'_id': note._id}}},
                                  { "notes.$": 1 }
                                  ).notes;
            note=_.findWhere(notes, {'_id': note._id});
            if (note != undefined) {
                $('#noteSummary').val(note.summary);
                $('#noteDescription').val(note.description);
            }
            e.preventDefault();
        },

        "click .notedelete": function(e){
            id = $(e.target).attr('data-noteid');
            incidents.update(Session.get('incidentID'), {
                $pull: {notes: {"_id": id}}
            });
            e.preventDefault();
        },

        "readystatechange":function(e){
            if (typeof console !== 'undefined') {
              console.log('readystatechange')
              console.log(e)
            }
            
        },
        "mouseenter .info-row": function(e,t){
            //toggle the bootstrap tooltip
            $('[data-toggle="tooltip"]').tooltip({
                'placement': 'top'
            });
        }
    });

    Template.editincidentform.rendered = function() {        
        initDatePickers=function(){
            //init the date pickers.
            $('#dateClosed').daterangepicker({
                                                singleDatePicker: true,
                                                timePicker:true,
                                                timePickerIncrement:1,
                                                format: 'MM/DD/YYYY hh:mm:ss A',
                                                startDate: dateOrNull($('#dateClosed').val() ) || moment()
                                                });
            $('#dateOpened').daterangepicker({
                                                singleDatePicker: true,
                                                timePicker:true,
                                                timePickerIncrement:1,
                                                format: 'MM/DD/YYYY hh:mm:ss A',
                                                startDate: dateOrNull($('#dateOpened').val() ) || moment()
                                                });
            $('#dateReported').daterangepicker({
                                                singleDatePicker: true,
                                                timePicker:true,
                                                timePickerIncrement:1,
                                                format: 'MM/DD/YYYY hh:mm:ss A',
                                                startDate: dateOrNull($('#dateReported').val() ) || moment()
                                                });
            $('#dateVerified').daterangepicker({
                                                singleDatePicker: true,
                                                timePicker:true,
                                                timePickerIncrement:1,
                                                format: 'MM/DD/YYYY hh:mm:ss A',
                                                startDate: dateOrNull($('#dateVerified').val() ) || moment()
                                                });
            $('#dateMitigated').daterangepicker({
                                                singleDatePicker: true,
                                                timePicker:true,
                                                timePickerIncrement:1,
                                                format: 'MM/DD/YYYY hh:mm:ss A',
                                                startDate: dateOrNull($('#dateMitigated').val() ) || moment()
                                                });
            $('#dateContained').daterangepicker({
                                                singleDatePicker: true,
                                                timePicker:true,
                                                timePickerIncrement:1,
                                                format: 'MM/DD/YYYY hh:mm:ss A',
                                                startDate: dateOrNull($('#dateContained').val() ) || moment()
                                                });
        };

        //log the user entering the template
        activity=models.userAction();
        activity.path='incident';
        activity.itemId=Session.get('incidentID');
        Template.instance.uaId=userActivity.insert(activity);
        
        
        //set up reactive data 
        Deps.autorun(function() {
            Meteor.subscribe("incident-details",Session.get('incidentID'), onReady=function(){
                initDatePickers();
            });
            
            Meteor.subscribe("userActivity",onReady=function(){
            //register a callback for new user activity
            //to show a notify when someone enters
            //screens the user is on
            //only run onReady to avoid initialization 'add' messages.
            cursorUserActivity=userActivity.find({path:'incident',
                                                 itemId:Session.get('incidentID'),
                                                 userId: {$ne: Meteor.user().profile.email}
                                                 },
                                        {
                                        reactive:true})
                                        .observeChanges(
                                                {added: function(id,fields){
                                                    console.log(fields);
                                                    Session.set('displayMessage',fields.userId + '& is viewing this incident')
                                                }
                                        }); 
            });
            
        }); //end deps.autorun

        //code to save the main tab data
        saveIncident=function(e,template){
            var incidentobj = {
              summary: template.find("#summary").value,
              description: template.find("#description").value,
              dateOpened: dateOrNull(template.find("#dateOpened").value),
              dateClosed: dateOrNull(template.find("#dateClosed").value),
              phase: template.find("#phase").value,
              dateReported: dateOrNull(template.find("#dateReported").value),
              dateVerified: dateOrNull(template.find("#dateVerified").value),
              dateMitigated: dateOrNull(template.find("#dateMitigated").value),
              dateContained: dateOrNull(template.find("#dateContained").value)
            }
            
            incidents.update(
                Session.get('incidentID'),
                {$set: incidentobj},
                {},
                function(error, nobj) {
                  if (!error && nobj === 1) {
                    $('#saveMessage').text('Changes Saved');
                  }else{
                    $('#saveMessage').text('Changes Not Saved');
                    console.log(error);
                  }
                }
            );
            //clear the info message after a bit
            Meteor.setTimeout(function() {
                    $('#saveMessage').text('');
                },3000);

        };

        incidentSaveTimer = function() {
          var timer;
    
          this.set = function(saveFormCB) {
            timer = Meteor.setTimeout(function() {
              saveFormCB();
            }, 3000);
          };
    
          this.clear = function() {
            if ( timer != undefined ){
                Meteor.clearTimeout(timer);
            }
          };
    
          this.run = function(e, t) {
            // Save user input after X seconds of not typing
            this.clear();
     
            this.set(function() {
              saveIncident(e, t);
            });
          };
    
          return this;    
        }();
    };
    
    Template.editincidentform.destroyed = function () {
        //remove the record of the user entering the template
        userActivity.remove(Template.instance.uaId);
    }

    Template.addincidentform.rendered = function() {
        $('#dateOpened').daterangepicker({
                                            singleDatePicker: true,
                                            timePicker:true,
                                            timePickerIncrement:1,
                                            format: 'MM/DD/YYYY hh:mm:ss A',
                                            startDate: moment()
                                            });        
    };

    //add incident events
    Template.addincidentform.events({
        "submit form": function(event, template) {
            event.preventDefault();
            newIncident=models.incident();
            newIncident.summary= template.find("#summary").value,
            newIncident.dateOpened=dateOrNull(template.find("#dateOpened").value),
            newIncident.phase=template.find("#phase").value            
            newid=incidents.insert(newIncident);
            //reroute to full blown edit form after this minimal input is complete
            Router.go('/incident/' + newid + '/edit');
        }

    });
}