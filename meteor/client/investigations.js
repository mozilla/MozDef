/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
*/
import { Meteor } from 'meteor/meteor'
import { Template } from 'meteor/templating';
import { Session } from 'meteor/session';
import { Tracker } from 'meteor/tracker';
import { moment } from 'meteor/momentjs:moment';
import { tooltip } from 'meteor/twbs:bootstrap';
import { daterangepicker } from 'meteor/dangrossman:bootstrap-daterangepicker';
import '/client/verisTags.html';

if ( Meteor.isClient ) {
    var note = null;
    var theory = null;
    var mitigation = null;
    var lesson = null;
    var indicator = null;
    var evidence = null;
    var timestamp = null;

    Template.investigations.helpers( {
        isReady: function() {
            return Template.instance().pagination.ready();
        },

        templatePagination: function() {
            return Template.instance().pagination;
        },

        documents: function() {
            return Template.instance().pagination.getPage();
        },

        query() {
            return Template.instance().searchQuery.get();
        }
    } );

    //select an investigation for editing
    Template.investigations.events( {
        "click .investigationadd": function( e, t ) {
            Router.go( '/investigation/new' );
        },

        "click .investigationedit": function( e, t ) {
            if ( this._id != undefined ) {
                //Session.set('displayMessage','Starting edit for investigation._id: ' + this._id);
                Router.go( '/investigation/' + this._id + '/edit' );
            }
        },

        "click .investigationdelete": function( e ) {
            investigations.remove( this._id );
        },

        "mouseenter .info-row": function( e, t ) {
            //toggle the bootstrap tooltip
            $( '[data-toggle="tooltip"]' ).tooltip( {
                'placement': 'top',
                container: ".tooltip-wrapper"
            } );
        },

        "keyup #search"( event, template ) {
            let value = event.target.value.trim();

            if ( value !== '' && event.keyCode === 13 ) {
                template.searchQuery.set( value );
            }

            if ( value === '' || event.keyCode == 27 ) {
                template.searchQuery.set( '' );
                event.target.value = '';
            }
        }
    } );

    Template.investigations.onCreated( function() {
        this.pagination = new Meteor.Pagination( investigations, {
            fields: {
                _id: 1,
                summary: 1,
                description: 1,
                phase: 1,
                dateOpened: 1,
                dateClosed: 1,
                creator: 1
            },
            sort: {
                dateOpened: -1
            },
            perPage: prefs().pageSize,
        } );

        Template.instance().searchQuery = new ReactiveVar();

        Tracker.autorun( () => {
            const filter_Text = this.searchQuery.get();

            if ( filter_Text && filter_Text.length > 0 ) {
                this.pagination.filters( { $text: { $search: filter_Text } } );
            } else {
                this.pagination.filters( {} );
            }
        } );
    } );

    Template.investigations.rendered = function() {
        this.$( '#search' ).focus();
    };


    //edit events
    Template.editinvestigationform.events( {
        "dragover .tags": function( e ) {
            e.preventDefault();   //allow the drag
        },

        "keyup .tagfilter": function( e, template ) {
            //var letter_pressed = String.fromCharCode(e.keyCode);
            //console.log(template.find("#tagfilter").value);
            Session.set( 'verisfilter', template.find( "#tagfilter" ).value );

        },

        "drop .tags": function( e ) {
            e.preventDefault();
            tagtext = e.originalEvent.dataTransfer.getData( "text/plain" );
            //e.target.textContent=droptag
            //console.log(tagtext)
            investigations.update( Session.get( 'investigationID' ), {
                $addToSet: { tags: tagtext }
            } );
        },

        "click .tagdelete": function( e ) {
            tagtext = e.target.parentNode.firstChild.wholeText;
            investigations.update( Session.get( 'investigationID' ), {
                $pull: { tags: tagtext }
            } );
        },

        'input #editinvestigationform': _.debounce( function( e, t ) {
            saveInvestigation( e, t );
        }, 500 ),

        "blur .calendarfield": _.debounce( function( e, t ) {
            saveInvestigation( e, t );
        }, 500 ),

        "click #saveInvestigation": function( e, template ) {
            saveInvestigation( e, template );
            e.preventDefault();
            e.stopPropagation();
        },

        "click .tabnav": function( e, template ) {
            //set the tab and tab content to active to display
            //and hide the non active ones.
            $( e.currentTarget ).addClass( 'active' ).siblings().removeClass( 'active' );
            $( e.target.hash ).hide();
            $( e.target.hash ).addClass( 'active' ).siblings().removeClass( 'active' );
            $( e.target.hash ).fadeIn( 400 );
        },

        "click #saveReference": function( e, template ) {
            tValue = $( '#newReference' ).val();
            if ( tValue.length > 0 ) {
                investigations.update( Session.get( 'investigationID' ), {
                    $addToSet: { references: tValue }
                } );
            }
            $( '#newReference' ).val( '' );
        },

        "click .referencedelete": function( e ) {
            //wholeText if it's not a url,
            //text if it's a url
            if ( e.target.parentNode.firstChild.wholeText ) {
                reftext = e.target.parentNode.firstChild.wholeText
            } else {
                reftext = e.target.parentNode.firstChild.text;
            }
            investigations.update( Session.get( 'investigationID' ), {
                $pull: { references: reftext }
            } );
        },

        "click #saveTheory": function( e, template ) {
            if ( !theory ) {
                theory = models.theory();
                theory.creator = Meteor.user().profile.email;
            }

            theory.summary = $( '#theorySummary' ).val();
            theory.description = $( '#theoryDescription' ).val();
            theory.status = $( '#theoryStatus' ).val();
            theory.lastModifier = Meteor.user().profile.email;

            if ( theory.summary && theory.description ) {
                //limited support for modify a set, so pull/add
                investigations.update( Session.get( 'investigationID' ), {
                    $pull: { theories: { "_id": theory._id } }
                } );

                investigations.update( Session.get( 'investigationID' ), {
                    $addToSet: { theories: theory }
                } );

                $( '#theorySummary' ).val( '' );
                $( '#theoryDescription' ).val( '' );
                $( '#theoryStatus' ).val( '' );
                theory = null;
                e.preventDefault();
            }

        },

        "click .theoryedit": function( e ) {
            theory = models.theory();
            theory._id = $( e.target ).attr( 'data-theoryid' );
            //elemMatch not available on client side..iterate the items for a match.
            theories = investigations.findOne( { '_id': Session.get( 'investigationID' ) },
                { theories: { $elemMatch: { '_id': theory._id } } },
                { "theories.$": 1 }
            ).theories;
            theory = _.findWhere( theories, { '_id': theory._id } );
            if ( theory != undefined ) {
                $( '#theorySummary' ).val( theory.summary );
                $( '#theoryDescription' ).val( theory.description );
                $( '#theoryStatus' ).val( theory.status );
            }
            e.preventDefault();
        },

        "click .theorydelete": function( e ) {
            id = $( e.target ).attr( 'data-theoryid' );
            investigations.update( Session.get( 'investigationID' ), {
                $pull: { theories: { "_id": id } }
            } );
            e.preventDefault();
        },

        "click #saveTimestamp": function( e, template ) {
            if ( !timestamp ) {
                timestamp = models.timestamp();
                timestamp.creator = Meteor.user().profile.email;
            }

            timestamp.timestamp = dateOrNull( $( '#timestampText' ).val() );
            timestamp.description = $( '#timestampDescription' ).val();
            timestamp.lastModifier = Meteor.user().profile.email;

            if ( timestamp.timestamp && timestamp.description ) {
                //limited support for modify a set, so pull/add
                investigations.update( Session.get( 'investigationID' ), {
                    $pull: { timestamps: { "_id": timestamp._id } }
                } );

                investigations.update( Session.get( 'investigationID' ), {
                    $addToSet: { timestamps: timestamp }
                } );

                $( '#timestampText' ).val( '' );
                $( '#timestampDescription' ).val( '' );
                timestamp = null;
                e.preventDefault();
            }

        },

        "click .timestampedit": function( e ) {
            timestamp = models.timestamp();
            timestamp._id = $( e.target ).attr( 'data-timestampid' );
            //elemMatch not available on client side..iterate the items for a match.
            timestamps = investigations.findOne( { '_id': Session.get( 'investigationID' ) },
                { timestamps: { $elemMatch: { '_id': timestamp._id } } },
                { "timestamps.$": 1 }
            ).timestamps;
            timestamp = _.findWhere( timestamps, { '_id': timestamp._id } );
            if ( timestamp != undefined ) {
                $( '#timestampText' ).val( timestamp.timestamp );
                $( '#timestampDescription' ).val( timestamp.description );
            }
            e.preventDefault();
        },

        "click .timestampdelete": function( e ) {
            id = $( e.target ).attr( 'data-timestampid' );
            investigations.update( Session.get( 'investigationID' ), {
                $pull: { timestamps: { "_id": id } }
            } );
            e.preventDefault();
        },

        "click #saveMitigation": function( e, template ) {
            if ( !mitigation ) {
                mitigation = models.mitigation();
                mitigation.creator = Meteor.user().profile.email;
            }
            mitigation.summary = $( '#mitigationSummary' ).val();
            mitigation.description = $( '#mitigationDescription' ).val();
            mitigation.status = $( '#mitigationStatus' ).val();
            mitigation.temporary = $( '#mitigationTemporary' ).is( ':checked' );
            mitigation.lastModifier = Meteor.user().profile.email;

            if ( mitigation.summary && mitigation.description ) {
                //limited support for modify a set, so pull/add
                investigations.update( Session.get( 'investigationID' ), {
                    $pull: { mitigations: { "_id": mitigation._id } }
                } );
                investigations.update( Session.get( 'investigationID' ), {
                    $addToSet: { mitigations: mitigation }
                } );
                $( '#mitigationSummary' ).val( '' );
                $( '#mitigationDescription' ).val( '' );
                $( '#mitigationStatus' ).val( '' );
                $( '#mitigationTemporary' ).prop( 'checked', false );
                mitigation = null;
                e.preventDefault();
            }

        },

        "click .mitigationedit": function( e ) {
            mitigation = models.mitigation();
            mitigation._id = $( e.target ).attr( 'data-mitigationid' );
            //elemMatch not available on client side..iterate the items for a match.
            mitigations = investigations.findOne( { '_id': Session.get( 'investigationID' ) },
                { mitigations: { $elemMatch: { '_id': mitigation._id } } },
                { "mitigations.$": 1 }
            ).mitigations;
            mitigation = _.findWhere( mitigations, { '_id': mitigation._id } );
            if ( mitigation != undefined ) {
                $( '#mitigationSummary' ).val( mitigation.summary );
                $( '#mitigationDescription' ).val( mitigation.description );
                $( '#mitigationStatus' ).val( mitigation.status );
                $( '#mitigationTemporary' ).prop( 'checked', mitigation.temporary );
            }
            e.preventDefault();
        },

        "click .mitigationdelete": function( e ) {
            id = $( e.target ).attr( 'data-mitigationid' );
            investigations.update( Session.get( 'investigationID' ), {
                $pull: { mitigations: { "_id": id } }
            } );
            e.preventDefault();
        },

        "click #saveLesson": function( e, template ) {
            if ( !lesson ) {
                lesson = models.lesson();
                lesson.creator = Meteor.user().profile.email;
            }
            lesson.summary = $( '#lessonSummary' ).val();
            lesson.description = $( '#lessonDescription' ).val();
            lesson.lastModifier = Meteor.user().profile.email;

            if ( lesson.summary && lesson.description ) {
                //limited support for modify a set, so pull/add
                investigations.update( Session.get( 'investigationID' ), {
                    $pull: { lessons: { "_id": lesson._id } }
                } );
                investigations.update( Session.get( 'investigationID' ), {
                    $addToSet: { lessons: lesson }
                } );
                $( '#lessonSummary' ).val( '' );
                $( '#lessonDescription' ).val( '' );
                lesson = null;
                e.preventDefault();
            }

        },

        "click .lessonedit": function( e ) {
            lesson = models.lesson();
            lesson._id = $( e.target ).attr( 'data-lessonid' );
            //elemMatch not available on client side..iterate the theories for a match.
            lessons = investigations.findOne( { '_id': Session.get( 'investigationID' ) },
                { lessons: { $elemMatch: { '_id': lesson._id } } },
                { "lessons.$": 1 }
            ).lessons;
            lesson = _.findWhere( lessons, { '_id': lesson._id } );
            if ( lesson != undefined ) {
                $( '#lessonSummary' ).val( lesson.summary );
                $( '#lessonDescription' ).val( lesson.description );
            }
            e.preventDefault();
        },

        "click .lessondelete": function( e ) {
            id = $( e.target ).attr( 'data-lessonid' );
            investigations.update( Session.get( 'investigationID' ), {
                $pull: { lessons: { "_id": id } }
            } );
            e.preventDefault();
        },

        "click #saveNote": function( e, template ) {
            if ( !note ) {
                note = models.note();
                note.creator = Meteor.user().profile.email;
            }
            note.summary = $( '#noteSummary' ).val();
            note.description = $( '#noteDescription' ).val();
            note.lastModifier = Meteor.user().profile.email;

            if ( note.summary && note.description ) {
                //limited support for modify a set, so pull/add
                investigations.update( Session.get( 'investigationID' ), {
                    $pull: { notes: { "_id": note._id } }
                } );
                investigations.update( Session.get( 'investigationID' ), {
                    $addToSet: { notes: note }
                } );
                $( '#noteSummary' ).val( '' );
                $( '#noteDescription' ).val( '' );
                note = null;
                e.preventDefault();
            }

        },

        "click .noteedit": function( e ) {
            note = models.note();
            note._id = $( e.target ).attr( 'data-noteid' );
            //elemMatch not available on client side..iterate the theories for a match.
            notes = investigations.findOne( { '_id': Session.get( 'investigationID' ) },
                { notes: { $elemMatch: { '_id': note._id } } },
                { "notes.$": 1 }
            ).notes;
            note = _.findWhere( notes, { '_id': note._id } );
            if ( note != undefined ) {
                $( '#noteSummary' ).val( note.summary );
                $( '#noteDescription' ).val( note.description );
            }
            e.preventDefault();
        },

        "click .notedelete": function( e ) {
            id = $( e.target ).attr( 'data-noteid' );
            investigations.update( Session.get( 'investigationID' ), {
                $pull: { notes: { "_id": id } }
            } );
            e.preventDefault();
        },

        "click #saveIndicator": function( e, template ) {
            if ( !indicator ) {
                indicator = models.indicator();
                indicator.creator = Meteor.user().profile.email;
            }
            indicator.summary = $( '#indicatorSummary' ).val();
            indicator.description = $( '#indicatorDescription' ).val();
            indicator.lastModifier = Meteor.user().profile.email;

            if ( indicator.summary && indicator.description ) {
                //limited support for modify a set, so pull/add
                investigations.update( Session.get( 'investigationID' ), {
                    $pull: { indicators: { "_id": indicator._id } }
                } );
                investigations.update( Session.get( 'investigationID' ), {
                    $addToSet: { indicators: indicator }
                } );
                $( '#indicatorSummary' ).val( '' );
                $( '#indicatorDescription' ).val( '' );
                indicator = null;
                e.preventDefault();
            }

        },

        "click .indicatoredit": function( e ) {
            indicator = models.indicator();
            indicator._id = $( e.target ).attr( 'data-indicatorid' );
            //elemMatch not available on client side..iterate the theories for a match.
            indicators = investigations.findOne( { '_id': Session.get( 'investigationID' ) },
                { indicators: { $elemMatch: { '_id': indicator._id } } },
                { "indicators.$": 1 }
            ).indicators;
            indicator = _.findWhere( indicators, { '_id': indicator._id } );
            if ( indicator != undefined ) {
                $( '#indicatorSummary' ).val( indicator.summary );
                $( '#indicatorDescription' ).val( indicator.description );
            }
            e.preventDefault();
        },

        "click .indicatordelete": function( e ) {
            id = $( e.target ).attr( 'data-indicatorid' );
            investigations.update( Session.get( 'investigationID' ), {
                $pull: { indicators: { "_id": id } }
            } );
            e.preventDefault();
        },

        "click #saveEvidence": function( e, template ) {
            if ( !evidence ) {
                evidence = models.evidence();
                evidence.creator = Meteor.user().profile.email;
            }
            evidence.summary = $( '#evidenceSummary' ).val();
            evidence.description = $( '#evidenceDescription' ).val();
            evidence.lastModifier = Meteor.user().profile.email;

            if ( evidence.summary && evidence.description ) {
                //limited support for modify a set, so pull/add
                investigations.update( Session.get( 'investigationID' ), {
                    $pull: { evidence: { "_id": evidence._id } }
                } );
                investigations.update( Session.get( 'investigationID' ), {
                    $addToSet: { evidence: evidence }
                } );
                $( '#evidenceSummary' ).val( '' );
                $( '#evidenceDescription' ).val( '' );
                evidence = null;
                e.preventDefault();
            }

        },

        "click .evidenceedit": function( e ) {
            evidence = models.evidence();
            evidence._id = $( e.target ).attr( 'data-evidenceid' );
            //elemMatch not available on client side..iterate the theories for a match.
            evidenceItems = investigations.findOne( { '_id': Session.get( 'investigationID' ) },
                { evidence: { $elemMatch: { '_id': evidence._id } } },
                { "evidence.$": 1 }
            ).evidence;
            evidence = _.findWhere( evidenceItems, { '_id': evidence._id } );
            if ( evidence != undefined ) {
                $( '#evidenceSummary' ).val( evidence.summary );
                $( '#evidenceDescription' ).val( evidence.description );
            }
            e.preventDefault();
        },

        "click .evidencedelete": function( e ) {
            id = $( e.target ).attr( 'data-evidenceid' );
            investigations.update( Session.get( 'investigationID' ), {
                $pull: { evidence: { "_id": id } }
            } );
            e.preventDefault();
        },

        "readystatechange": function( e ) {
            if ( typeof console !== 'undefined' ) {
                console.log( 'readystatechange' )
                console.log( e )
            }
        },
        "mouseenter .info-row": function( e, t ) {
            //toggle the bootstrap tooltip
            $( '[data-toggle="tooltip"]' ).tooltip( {
                'placement': 'top'
            } );
        },
        "click .makeincident": function( event, template ) {
            event.preventDefault();
            // make an incident from this investigation
            newIncident = investigations.findOne( { _id: Session.get( 'investigationID' ) } );
            delete newIncident._id;
            newid = incidents.insert( newIncident );
            // add a link to this in the incident references
            incidents.update( newid, {
                $addToSet: { references: template.firstNode.baseURI }
            } );
            //reroute to full blown edit form after this minimal input is complete
            Router.go( '/incident/' + newid + '/edit' );
        }
    } );

    Template.editinvestigationform.rendered = function() {
        initDatePickers = function() {
            //init the date pickers.
            $( '#dateClosed' ).daterangepicker( {
                singleDatePicker: true,
                timePicker: true,
                timePickerIncrement: 1,
                autoUpdateInput: false,
                locale: {
                    format: 'MM/DD/YYYY hh:mm:ss A',
                },
                startDate: dateOrNull( $( '#dateClosed' ).val() ) || moment()
            } );
            $( '#dateClosed' ).on( 'apply.daterangepicker', function( ev, picker ) {
                $( this ).val( picker.startDate.format( 'MM/DD/YYYY hh:mm:ss A' ) );
            } );
            $( '#dateOpened' ).daterangepicker( {
                singleDatePicker: true,
                timePicker: true,
                timePickerIncrement: 1,
                autoUpdateInput: false,
                locale: {
                    format: 'MM/DD/YYYY hh:mm:ss A',
                },
                startDate: dateOrNull( $( '#dateOpened' ).val() ) || moment()
            } );
            $( '#dateOpened' ).on( 'apply.daterangepicker', function( ev, picker ) {
                $( this ).val( picker.startDate.format( 'MM/DD/YYYY hh:mm:ss A' ) );
            } );

            $( '#dateBegin' ).daterangepicker( {
                singleDatePicker: true,
                timePicker: true,
                timePickerIncrement: 1,
                autoUpdateInput: false,
                locale: {
                    format: 'MM/DD/YYYY hh:mm:ss A',
                },
                startDate: dateOrNull( $( '#dateBegin' ).val() ) || moment()
            } );
            $( '#dateBegin' ).on( 'apply.daterangepicker', function( ev, picker ) {
                $( this ).val( picker.startDate.format( 'MM/DD/YYYY hh:mm:ss A' ) );
            } );
            $( '#dateEnd' ).daterangepicker( {
                singleDatePicker: true,
                timePicker: true,
                timePickerIncrement: 1,
                autoUpdateInput: false,
                locale: {
                    format: 'MM/DD/YYYY hh:mm:ss A',
                },
                startDate: dateOrNull( $( '#dateEnd' ).val() ) || moment()
            } );
            $( '#dateEnd' ).on( 'apply.daterangepicker', function( ev, picker ) {
                $( this ).val( picker.startDate.format( 'MM/DD/YYYY hh:mm:ss A' ) );
            } );

            $( '#timestampText' ).daterangepicker( {
                singleDatePicker: true,
                timePicker: true,
                timePickerIncrement: 1,
                autoUpdateInput: false,
                locale: {
                    format: 'MM/DD/YYYY hh:mm:ss A',
                },
                startDate: dateOrNull( $( '#timestampText' ).val() ) || moment()
            } );
            $( '#timestampText' ).on( 'apply.daterangepicker', function( ev, picker ) {
                $( this ).val( picker.startDate.format( 'MM/DD/YYYY hh:mm:ss A' ) );
            } );
        };

        this.$( '[data-toggle="tooltip"]' ).tooltip( {
            'placement': 'top'
        } );

        //log the user entering the template
        activity = models.userAction();
        activity.path = 'investigation';
        activity.itemId = Session.get( 'investigationID' );
        Template.instance.uaId = userActivity.insert( activity );

        //set up reactive data
        Deps.autorun( function() {
            Meteor.subscribe( "investigation-details", Session.get( 'investigationID' ), onReady = function() {
                initDatePickers();
            } );
            Meteor.subscribe( "userActivity", onReady = function() {
                //register a callback for new user activity
                //to show a notify when someone enters
                //screens the user is on
                //only run onReady to avoid initialization 'add' messages.
                cursorUserActivity = userActivity.find( {
                    path: 'investigation',
                    itemId: Session.get( 'investigationID' ),
                    userId: { $ne: Meteor.user().profile.email }
                },
                    {
                        reactive: true
                    } )
                    .observeChanges(
                        {
                            added: function( id, fields ) {
                                //console.log(fields);
                                Session.set( 'displayMessage', fields.userId + '& is viewing this investigation' )
                            }
                        } );
            } );
        } ); //end deps.autorun

        saveInvestigation = function( e, template ) {

            // tags are saved in real realtime
            // other tabs are saved as they are changed
            // this is only for the main tab

            var investigationobj = {
                summary: template.find( "#summary" ).value,
                description: template.find( "#description" ).value,
                contact: template.find( "#contact" ).value,
                dateOpened: dateOrNull( template.find( "#dateOpened" ).value ),
                dateClosed: dateOrNull( template.find( "#dateClosed" ).value ),
                phase: template.find( "#phase" ).value,
                dateBegin: dateOrNull( template.find( "#dateBegin" ).value ),
                dateEnd: dateOrNull( template.find( "#dateEnd" ).value )
            }

            investigations.update( Session.get( 'investigationID' ),
                { $set: investigationobj },
                {},
                function( error, nobj ) {
                    if ( !error && nobj === 1 ) {
                        $( '#saveMessage' ).text( 'Changes Saved' );
                    } else {
                        $( '#saveMessage' ).text( 'Changes Not Saved' );
                        console.log( error );
                    }
                }
            );

            //clear the info message after a bit
            Meteor.setTimeout( function() {
                $( '#saveMessage' ).text( '' );
            }, 3000 );
        }

    };

    Template.editinvestigationform.destroyed = function() {
        //remove the record of the user entering the template
        userActivity.remove( Template.instance.uaId );
    }

    Template.addinvestigationform.rendered = function() {
        $( '#dateOpened' ).daterangepicker( {
            singleDatePicker: true,
            timePicker: true,
            timePickerIncrement: 1,
            autoUpdateInput: false,
            locale: {
                format: 'MM/DD/YYYY hh:mm:ss A',
            },
            startDate: moment()
        } );
        $( '#dateOpened' ).on( 'apply.daterangepicker', function( ev, picker ) {
            $( this ).val( picker.startDate.format( 'MM/DD/YYYY hh:mm:ss A' ) );
        } );
    };

    //add investigation events
    Template.addinvestigationform.events( {
        "submit form": function( event, template ) {
            event.preventDefault();
            newinvestigation = models.investigation();
            newinvestigation.summary = template.find( "#summary" ).value,
                newinvestigation.dateOpened = dateOrNull( template.find( "#dateOpened" ).value ),
                newinvestigation.phase = template.find( "#phase" ).value
            newid = investigations.insert( newinvestigation );
            //reroute to full blown edit form after this minimal input is complete
            Router.go( '/investigation/' + newid + '/edit' );
        }

    } );
}
