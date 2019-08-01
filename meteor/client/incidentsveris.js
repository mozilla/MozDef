 /*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation
 */
import { Meteor } from 'meteor/meteor'
import { Template } from 'meteor/templating';
import { moment} from 'meteor/momentjs:moment';
import d3 from 'd3';
import 'jquery-ui/ui/data';
import 'jquery-ui/ui/widget';
import 'jquery-ui/ui/scroll-parent';
import 'jquery-ui/ui/widgets/mouse';
import 'jquery-ui/ui/widgets/sortable';
import pivotUI from 'pivottable';

import 'pivottable/dist/pivot.css';

if (Meteor.isClient) {
    var verisstatsResult = new Object;

    Template.incidentsveris.rendered = function () {
        var container=document.getElementById('veris-wrapper')
        container.style.cursor='wait'
        Meteor.apply('verisstats',
            [],
            onResultReceived = function(err,result){
                //debugLog(err,result);
                if (typeof err == 'undefined') {
                    verisstatsResult.status='completed';
                    verisstatsResult.result = result;
                    verisstatsResult.content=result.content;
                    verisstatsResult.data=result.data;
                    container.style.cursor='auto';
                    result.data.forEach(function(d){
                        if ( d.dateOpened && d.dateOpened['$date'] ){
                            //grab just the year from the python datetime object
                            d.yearOpened=moment(d.dateOpened['$date']).format("YYYY");
                            //reformat dateOpened from a python datetime object to month date
                            d.dateOpened=moment(d.dateOpened['$date']).format("MMMM YYYY");
                        }
                    });
                    startPivotTable(result.data);
               } else {
                    //debugLog(err,result);
                    verisstatsResult.status='error';
                    verisstatsResult.error=err;
               }
           });

        container.style.cursor='auto';
        function startPivotTable(tableData){
            $("#veris-wrapper").pivotUI(
                tableData,
                {
                    cols: ["phase"],
                    rows: ["tags"],
                    menuLimit: 500
                });
        }
    };

    Template.incidentsveris.destroyed = function () {
        debugLog('destroyed');
    };
}
