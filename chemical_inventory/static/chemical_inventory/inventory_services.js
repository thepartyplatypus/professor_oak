angular.module('chemicalInventory')

    .service('Chemical', ['$resource', '$http', 'djangoUrl', function ($resource, $http, djangoUrl) {
	// A $resource for sending and receiving an abstract chemical from the database
	var chemicalUrl = djangoUrl.reverse('api:chemical-list');
	var Chemical = 	$resource(chemicalUrl);
	Chemical.save = function(chemicalData) {
	    // Make a new form with the given data (including the file if necessary)
	    var fd = new FormData();
	    if (chemicalData.safety_data_sheet) {
		fd.append('safety_data_sheet', chemicalData.safety_data_sheet);
	    }
	    for ( var key in chemicalData ) {
		// Make sure this is actually a field
		if (chemicalData.hasOwnProperty(key) &&
		    key[0] != '$' && chemicalData[key] != undefined)
	    	fd.append(key, chemicalData[key]);
	    }
	    return $http.post(chemicalUrl, fd, {
		transformRequest: angular.identity,
		withCredentials: false,
		headers: {'Content-Type': undefined}
	    });
	};
	return Chemical
    }])

    .service('fileUpload', ['$http', function ($http) {
	// Service for sending uploaded files to the server
	// https://uncorkedstudios.com/blog/multipartformdata-file-upload-with-angularjs
	this.uploadFileToUrl = function(file, uploadUrl){
	    var fd = new FormData();
	    fd.append('file', file);
	    $http.post(uploadUrl, fd, {
		transformRequest: angular.identity,
		headers: {'Content-Type': undefined}
	    })
	        .success(function(){
		})
	        .error(function(){
		});
	}
    }])

    .factory('redirect', [function() {
	// Utility funciton for moving to a new page
	return function(url) {
	    window.location.href = url;
	};
    }]);
