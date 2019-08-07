/*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
 */
import { Template } from 'meteor/templating';
import crossfilter from 'crossfilter2';
import dc from 'dc';
import 'dc/dc.css';
import { tooltip } from 'meteor/twbs:bootstrap';

if ( Meteor.isClient ) {

    //elastic search cluster template functions
    //return es health items
    Template.mozdefhealth.helpers( {

        esclusterhealthitems: function() {
            return healthescluster.find();
        },
        frontendhealthitems: function() {
            return healthfrontend.find( {},
                {
                    fields: {},
                    sort: { hostname: 1 }
                } );
        },
        sqsstatsitems: function() {
            return sqsstats.find( {},
                {
                    fields: {},
                    sort: { hostname: 1 }
                } );
        },
        esnodeshealthitems: function() {
            return healthesnodes.find( {},
                {
                    fields: {},
                    sort: { hostname: 1 }
                } );
        },

        eshotthreadshealthitems: function() {
            return healtheshotthreads.find();
        }
    } );

    Template.mozdefhealth.rendered = function() {
        var ringChartEPS = dc.pieChart( "#ringChart-EPS" );
        var totalEPS = dc.numberDisplay( "#total-EPS" );
        var ringChartLoadAverage = dc.pieChart( "#ringChart-LoadAverage" );

        refreshChartData = function() {
            var frontEndData = healthfrontend.find( {} ).fetch();
            var ndx = crossfilter( frontEndData );

            if ( frontEndData.length === 0 && ndx.size() > 0 ) {
                debugLog( 'clearing ndx/dc.js' );
                dc.filterAll();
                ndx.remove();
                dc.redrawAll();
            } else {
                ndx = crossfilter( frontEndData );
            }
            if ( ndx.size() > 0 ) {
                var hostDim = ndx.dimension( function( d ) { return d.hostname; } );
                var hostEPS = hostDim.group().reduceSum( function( d ) { return d.details.total_deliver_eps.toFixed( 2 ); } );
                var hostLoadAverage = hostDim.group().reduceSum( function( d ) { return d.details.loadaverage[0]; } );
                var epsTotal = ndx.groupAll().reduceSum( function( d ) { return d.details.total_deliver_eps; } );

                totalEPS
                    .valueAccessor( function( d ) { return d; } )
                    .group( epsTotal );

                ringChartEPS
                    .width( 150 ).height( 150 )
                    .dimension( hostDim )
                    .group( hostEPS )
                    .label( function( d ) { return d.value || ''; } )
                    .innerRadius( 30 )
                    .filter = function() { };

                ringChartLoadAverage
                    .width( 150 ).height( 150 )
                    .dimension( hostDim )
                    .group( hostLoadAverage )
                    .label( function( d ) { return d.value || ''; } )
                    .innerRadius( 30 )
                    .filter = function() { };

                dc.renderAll();
            }
        }

        Deps.autorun( function() {
            Meteor.subscribe( "healthfrontend", onReady = function() {
                refreshChartData();
            } );
            Meteor.subscribe( "sqsstats" );
            Meteor.subscribe( "healthescluster" );
            Meteor.subscribe( "healthesnodes" );
            Meteor.subscribe( "healtheshotthreads" );
            //using dc.js doesn't trigger the reactive update
            //so update a UI object and refresh dc.js so both get data when it updates.
            var obj = healthfrontend.findOne();
            if ( obj ) {
                $( '.lastupdate' ).text( 'Last Update: ' + obj.utctimestamp );
                refreshChartData();
            }
        } ); //end deps.autorun

        this.$( '[data-toggle="tooltip"]' ).tooltip( {
            'placement': 'top'
        } );
    };

    Template.mozdefhealth.destroyed = function() {
        dc.deregisterAllCharts();
    };
}