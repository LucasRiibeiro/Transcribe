var axios = require('axios');
var FormData = require('form-data');
var fs = require('fs');
var data = new FormData();
data.append('audio', fs.createReadStream('@/C:/tmp/Teste.ogg'));

var config = {
    method: 'post',
    maxBodyLength: Infinity,
    url: 'http://127.0.0.1:5000/transcrever',
    headers: { 
        ...data.getHeaders()
    },
    data : data
};

axios(config)
    .then(function (response) {
        console.log(JSON.stringify(response.data));
    })
    .catch(function (error) {
        console.log(error);
    });