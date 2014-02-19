//data models
//and creation functions

var today=new Date();

models={

    incident: function() {
        return {
            summary:"",
            dateOpened: today,
            dateClosed:"",
            theories:[],
            notes:[],
            tags:['tag here'],
            phase:"Identification",
            discovery:"",
            verification:"",
            accessibility:"",
            confidence:"",
            
            actor:"",
            motive:"",
            timeline: {reported:"",
                        verified:"",
                        mitigationAvailable:"",
                        contained:"",
                        disclosed:"",
                        timeToCompromise:"",
                        timeToDiscovery:"",
                        timeToContainment:"",
                        timeToExfiltration:""
                      },
            action:"",
            asset:"",
            attribute:"",
            impact:""
        };
    },

    note: function() {
        return {
            'title': '',
            'content': '',
            'lastModifier': ''
        };
    },

    credential: function() {
        return {
            'username': '',
            'password': '',
            'hash': ''
        };
    }	

};
