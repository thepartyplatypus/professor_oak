angular.module('chemicalInventory')

    .controller('addContainer', ['$scope', '$resource', 'toaster', function($scope, $resource, toaster) {
	var Chemical;
	// Get the list of currently existing chemicals the user can choose from
	Chemical = $resource('/chemical_inventory/api/chemicals/');
	$scope.existing_chemicals = Chemical.query();
	$scope.existing_chemicals.$promise.then(function(chemicalList) {
	    var chemical;
	    // Set an additional display attribute
	    for (var i=0; i < chemicalList.length; i++) {
		chemical = chemicalList[i];
		chemical.$displayName = chemical.name;
	    }
	    // Add a dummy entry for creating a new chemical
	    var dummyChemical = {
		id: 0,
		name: '[New chemical]',
		health: '',
		flammability: '',
		instability: '',
		special_hazards: '',
		gloves: [],
		$displayName: '[New chemical]',
	    };
	    chemicalList.splice(0, 0, dummyChemical);
	});
	// Automatically set default for opened and expiration dates
	var today = new Date();
	// var date_opened = today.toISOString().split('T')[0];
	var expiration_date = new Date();
	expiration_date.setFullYear(1+expiration_date.getFullYear());
	// expiration_date = expiration_date.toISOString().split('T')[0];
	// Helper function resets the container form to an empty pristine state
	function resetContainer() {
	    $scope.container = {
		date_opened: today,
		expiration_date: expiration_date,
		quantity: 100,
		unit_of_measure: 'g',
	    };
	    if (typeof $scope.container_form != 'undefined' ) {
		console.log('form pristine');
		$scope.container_form.$setPristine();
	    }
	}
	resetContainer();
	// Save the entered form data
	function save_container(container) {
	    var Container = $resource('/chemical_inventory/api/containers/');
	    var newContainer = Container.save(container);
	    newContainer.$promise.then(function(container) {
		// Display visual feedback of success
		var message = "Added " +
		    container.quantity + container.unit_of_measure +
		    " of " + $scope.chemical.name +
		    " to inventory. It's super effective!";
		toaster.success('Success!', message);
		resetContainer();
	    }).catch(function(reason) {
		// Display visual feedback of error
		var message = "Chemical not added. Please contact your administrator";
		toaster.pop({
		    type: 'error',
		    title: 'Error!',
		    body: message,
		    timeout: 0,
		    showCloseButton: true
		});
		console.log(reason);
	    });
	}
	$scope.save = function() {
	    // Check if a new chemical is being saved
	    if ($scope.chemical.id > 0) {
		// Existing chemical -> save container directly
		$scope.container.chemical = $scope.chemical.id;
		save_container($scope.container);
	    } else {
		// New chemical -> send the new chemical to the server first
		var newChemical = Chemical.save($scope.chemical);
		newChemical.$promise.then(function(chemical) {
		    // On completion, save the container
		    $scope.container.chemical = chemical.id;
		    save_container($scope.container);
		});
	    }
	};
    }])

// Controller handles the list of containers for a given chemical,
// eg. allowing the user to set the .is_empty attribute via a checkbox
    .controller('chemicalList', ['$scope', '$resource', '$http', 'djangoUrl', function($scope, $resource, $http, djangoUrl) {
	// Handler for changing empty status
	$scope.updateStatus = function() {
	    var containerUrl, Container, container;
	    // Get the container object from the API
	    containerUrl = djangoUrl.reverse('api:container-detail',
					     {pk: $scope.chemicalId});
	    var payload = {is_empty: $scope.isEmpty};
	    $http.patch(containerUrl, {is_empty: $scope.isEmpty});
	};
    }])
