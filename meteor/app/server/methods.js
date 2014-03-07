//public functions
Meteor.methods({
    'saySomething':saySomething,
    'refreshESStatus':refreshESStatus
});


    function saySomething(){
        console.log("something is said")
    }

    function refreshESStatus(){
        console.log('Refreshing elastic search cluster stats for: ' + elasticsearch.address);
    	esHealthRequest=HTTP.get(elasticsearch.address + elasticsearch.healthurl)
    	if (esHealthRequest.statusCode==200 && esHealthRequest.data) {

            //get doc count and add it to the health request data
            esDocStatsRequest=HTTP.get(elasticsearch.address + elasticsearch.docstatsurl)
            if (esDocStatsRequest.statusCode==200 && esDocStatsRequest.data ) {
              //set the current doc stats
              if (esDocStatsRequest["data"]["_all"]["total"]["docs"]) {
                esHealthRequest["data"]["total_docs"]=esDocStatsRequest["data"]["_all"]["total"]["docs"].count
              }
              else {
                esHealthRequest["data"]["total_docs"] = 0
              }
              console.log('Total Docs: '+ esHealthRequest["data"]["total_docs"])
            }

            //set current status of the elastic search cluster
            console.log("Updating elastic search cluster health")
            eshealth.remove({})
            eshealth.insert(esHealthRequest["data"])
            console.log(esHealthRequest["data"])
    	}else{
            //note the error
            console.log("Could not retrieve elastic search cluster health..check settings")
            console.log(elasticsearch.address + elasticsearch.healthurl)
            console.log("returned a " + esHealthRequest.statusCode)
            console.log(esHealthRequest["data"])
        }
    }
