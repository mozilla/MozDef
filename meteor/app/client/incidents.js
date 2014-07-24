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
        return incidents.find();
    };

    //select an incident for editing
    Template.incidents.events({
        "click": function(e,t){
            if (this._id != undefined){
                Session.set('displayMessage','Starting edit for incident._id: ' + this._id);
                Router.go('/incident/' + this._id + '/edit');
            }
        }
    });

    
    Template.incidents.rendered = function(){
       Meteor.subscribe("incidents-summary");  
    };

    //edit helpers
    Template.editincidentform.helpers({
        incident: function() {
            return incidents.findOne(Session.get('incidentID'));
        },
        eachSort: function(context,options){
            var ret = "";
          
            for(var i=0, j=context.length; i<j; i++) {
              ret = ret + options.fn(context.sort()[i]);
            }
          
            return ret; 
        }
    });

    var incidentRevision = function() {
      this.save = function(e, template) {
        // Stop the timer if it was running
        incidentSaveTimer.clear();

        // tags are saved in real realtime (without timer)

        var incidentobj = {
          summary: template.find("#summary").value,
          description: template.find("#description").value,
          dateOpened: template.find("#dateOpened").value,
          dateClosed: template.find("#dateClosed").value,
          phase: template.find("#phase").value,
          dateReported: template.find("#dateReported").value,
          dateVerified: template.find("#dateVerified").value,
          dateMitigated: template.find("#dateMitigated").value,
          dateContained: template.find("#dateContained").value
        }

        incidents.update(Session.get('incidentID'),
        {$set: incidentobj},
        {},
        function(error, nobj) {
          if (!error && nobj === 1) {
            $('#saving').text('Changes Saved');
          }
        });

        var revisionsundo = Session.get('revisionsundo');
        revisionsundo.push(incidentobj);
        Session.set('revisionsundo', revisionsundo);
      }

      this.undo = function(e, template) {
        if (Session.get('revisionsundo').length >= 1 && Session.get('revisionsundo')[0] != null) {
          var revisionsundo = Session.get('revisionsundo');
          if (revisionsundo.length > 1) {
            var incident = revisionsundo.splice(revisionsundo.length-1, 1)[0];
            var revisionsredo = Session.get('revisionsredo');
            revisionsredo.unshift(incident);
            Session.set('revisionsredo', revisionsredo);
          }
          else {
            var incident = revisionsundo[0];
          }
          Session.set('revisionsundo', revisionsundo);

          template.find("#summary").value = incident.summary;
          template.find("#description").value = incident.description;
          template.find("#dateOpened").value = incident.dateOpened;
          template.find("#dateClosed").value = incident.dateClosed;
          template.find("#phase").value = incident.phase;
          template.find("#dateReported").value = incident.dateReported;
          template.find("#dateVerified").value = incident.dateVerified;
          template.find("#dateMitigated").value = incident.dateMitigated;
          template.find("#dateContained").value = incident.dateContained;
        }
      }

      this.redo = function(e, template) {
        if (Session.get('revisionsredo').length >= 1) {
          var revisionsredo = Session.get('revisionsredo');
          var incident = revisionsredo.splice(0, 1)[0];
          var revisionsundo = Session.get('revisionsundo');
          revisionsundo.push(incident);
          Session.set('revisionsundo', revisionsundo);
          Session.set('revisionsredo', revisionsredo);

          template.find("#summary").value = incident.summary;
          template.find("#description").value = incident.description;
          template.find("#dateOpened").value = incident.dateOpened;
          template.find("#dateClosed").value = incident.dateClosed;
          template.find("#phase").value = incident.phase;
          template.find("#dateReported").value = incident.dateReported;
          template.find("#dateVerified").value = incident.dateVerified;
          template.find("#dateMitigated").value = incident.dateMitigated;
          template.find("#dateContained").value = incident.dateContained;
        }
      }

      return this;
    }();

    var incidentSaveTimer = function() {
      var timer;

      this.set = function(saveFormCB) {
        $('#saving').text('');
        timer = Meteor.setTimeout(function() {
          saveFormCB();
          Meteor.setTimeout(function() {
            $('#saving').text('');
          }, 3000);
        }, 3000);
      };

      this.clear = function() {
        Meteor.clearInterval(timer);
      };

      this.run = function(e, t) {
        // Save user input after 3 seconds of not typing
        this.clear();
 
        this.set(function() {
          // We should update our document.
          $('#saving').text('Saving...');
          // If update is successful, then
          incidentRevision.save(e, t);
        });
      };

      return this;    
    }();

    //edit events
    Template.editincidentform.events({
        "dragover .tags": function(e){
          e.preventDefault();   //allow the drag  
        },
        "keyup .tagfilter":function(e,template){
            //console.log(e);
            //var letter_pressed = String.fromCharCode(e.keyCode);
            //console.log(template.find("#tagfilter").value);
            Session.set('verisfilter',template.find("#tagfilter").value);
            
        },
        "drop .tags": function(e){
          e.preventDefault();
          //console.log(e)
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
        "keyup": function(e, t) {
           // Save user input after 3 seconds of not typing
           incidentSaveTimer.run(e, t);
        },

        "blur .calendarfield": function(e, t) {
           // Save user input after 3 seconds of not typing
           incidentSaveTimer.run(e, t);
        },

        "change #phase": function(e, t) {
           // Save user input after 3 seconds of not typing
           incidentSaveTimer.run(e, t);
         },

        "click #saveChanges": function(e, template) {
          incidentRevision.save(e, template);
        },
        
        "click #undo": function(e, template) {
          incidentRevision.undo(e, template);
        },

        "click #redo": function(e, template) {
          incidentRevision.redo(e, template);
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
            reftext = e.target.parentNode.firstChild.wholeText;
            incidents.update(Session.get('incidentID'), {
                $pull: {references:reftext}
            });
        },
        
        "click #saveTheory": function(e,template){
            newTheory=models.theory();
            newTheory.summary=$('#newTheorySummary').val();
            newTheory.description=$('#newTheoryDescription').val();
            newTheory.creator=Meteor.user().profile.email;
            newTheory.lastModifier=Meteor.user().profile.email;
            if ( newTheory.summary && newTheory.description ) {
                incidents.update(Session.get('incidentID'), {
                    $addToSet: {theories:newTheory}
                });
                $('#newTheorySummary').val('');
                $('#newTheoryDescription').val('');
                e.preventDefault();
            }

        },
        "click .theorydelete": function(e){
            id = $(e.target).attr('data-theoryid');
            incidents.update(Session.get('incidentID'), {
                $pull: {theories: {"_id": id}}
            });
            e.preventDefault();
        },        

        "click #saveMitigation": function(e,template){
            newMitigation=models.mitigation();
            newMitigation.summary=$('#newMitigationSummary').val();
            newMitigation.description=$('#newMitigationDescription').val();
            newMitigation.temporary=$('#newMitigationTemporary').is(':checked');
            newMitigation.creator=Meteor.user().profile.email;
            newMitigation.lastModifier=Meteor.user().profile.email;
            if ( newMitigation.summary && newMitigation.description ) {
                incidents.update(Session.get('incidentID'), {
                    $addToSet: {mitigations:newMitigation}
                });
                $('#newMitigationSummary').val('');
                $('#newMitigationDescription').val('');
                $('#newMitigationTemporary').attr('checked', false);
                e.preventDefault();
            }

        },
        "click .mitigationdelete": function(e){
            id = $(e.target).attr('data-mitigationid');
            incidents.update(Session.get('incidentID'), {
                $pull: {mitigations: {"_id": id}}
            });
            e.preventDefault();
        },

        "click #saveLesson": function(e,template){
            newLesson=models.lesson();
            newLesson.summary=$('#newLessonSummary').val();
            newLesson.description=$('#newLessonDescription').val();
            newLesson.creator=Meteor.user().profile.email;
            newLesson.lastModifier=Meteor.user().profile.email;
            if ( newLesson.summary && newLesson.description ) {
                incidents.update(Session.get('incidentID'), {
                    $addToSet: {lessons:newLesson}
                });
                $('#newLessonSummary').val('');
                $('#newLessonDescription').val('');
                e.preventDefault();
            }

        },
        "click .lessondelete": function(e){
            id = $(e.target).attr('data-lessonid');
            incidents.update(Session.get('incidentID'), {
                $pull: {lessons: {"_id": id}}
            });
            e.preventDefault();
        },

        "click #saveNote": function(e,template){
            newNote=models.note();
            newNote.summary=$('#newNoteSummary').val();
            newNote.description=$('#newNoteDescription').val();
            newNote.creator=Meteor.user().profile.email;
            newNote.lastModifier=Meteor.user().profile.email;
            if ( newNote.summary && newNote.description ) {
                incidents.update(Session.get('incidentID'), {
                    $addToSet: {notes:newNote}
                });
                $('#newNoteSummary').val('');
                $('#newNoteDescription').val('');
                e.preventDefault();
            }

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
            
        }
    });

    Template.editincidentform.rendered = function() {
        if (typeof console !== 'undefined') {
          console.log('load edit incident form ' + Session.get('incidentID'));
        }
        //init the date pickers.
        $('#dateClosed').daterangepicker({
                                            singleDatePicker: true,
                                            timePicker:true,
                                            timePickerIncrement:1,
                                            format: 'MM/DD/YYYY hh:mm:ss A',
                                            startDate: moment()
                                            });
        $('#dateOpened').daterangepicker({
                                            singleDatePicker: true,
                                            timePicker:true,
                                            timePickerIncrement:1,
                                            format: 'MM/DD/YYYY hh:mm:ss A',
                                            startDate: moment()
                                            });
        $('#dateReported').daterangepicker({
                                            singleDatePicker: true,
                                            timePicker:true,
                                            timePickerIncrement:1,
                                            format: 'MM/DD/YYYY hh:mm:ss A',
                                            startDate: moment()
                                            });
        $('#dateVerified').daterangepicker({
                                            singleDatePicker: true,
                                            timePicker:true,
                                            timePickerIncrement:1,
                                            format: 'MM/DD/YYYY hh:mm:ss A',
                                            startDate: moment()
                                            });
        $('#dateMitigated').daterangepicker({
                                            singleDatePicker: true,
                                            timePicker:true,
                                            timePickerIncrement:1,
                                            format: 'MM/DD/YYYY hh:mm:ss A',
                                            startDate: moment()
                                            });
        $('#dateContained').daterangepicker({
                                            singleDatePicker: true,
                                            timePicker:true,
                                            timePickerIncrement:1,
                                            format: 'MM/DD/YYYY hh:mm:ss A',
                                            startDate: moment()
                                            });
        //set up reactive data 
        Deps.autorun(function() {
            Meteor.subscribe("incidents-details",Session.get('incidentID'));
        }); //end deps.autorun
    };

    //add incident events
    Template.addincidentform.events({
        "submit form": function(event, template) {
            event.preventDefault();
            incidents.insert({
                summary: template.find("#summary").value,
                dateOpened: template.find("#dateOpened").value,
                phase: template.find("#phase").value
            });
            //TODO; reroute to full blown edit form after this minimal input is complete
            Router.go('/incidents/')
        }

    });
}