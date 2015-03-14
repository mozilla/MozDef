 /*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
Copyright (c) 2014 Mozilla Corporation

Contributors:
Jeff Bryner jbryner@mozilla.com
 */

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
                        //grab just the year from the python datetime object
                        d.yearOpened=moment(d.dateOpened['$date']).format("YYYY");
                        //reformat dateOpened from a python datetime object to month date
                        d.dateOpened=moment(d.dateOpened['$date']).format("MMMM YYYY");
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
                            rows: ["tags"]
                        }
                    );
        }
    };

    Template.incidentsveris.destroyed = function () {
        debugLog('destroyed');
    };   
}