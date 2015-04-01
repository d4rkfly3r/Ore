angular.module('ore', ['ngRoute', 'templates'])
    .config(['$routeProvider', '$locationProvider', function ($routeProvider, $locationProvider) {
        $routeProvider.
            when('/', {
                templateUrl: 'greeting.html',
                controller: 'GreetingCtrl'
            });
        $locationProvider.html5Mode(true)
    }])
    .controller('GreetingCtrl', ['$scope', function ($scope) {
        $scope.greetMe = 'World';
    }]);
