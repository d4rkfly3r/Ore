angular.module('ore')
    .config(function ($locationProvider) {
        $locationProvider.html5Mode(true);
    })
    .config(function ($stateProvider, $urlRouterProvider) {

        $stateProvider
            .state('home', {
                url: '/',
                templateUrl: 'home.html',
                controller: 'HomeController'
            })
            .state('login', {
                url: '/login',
                templateUrl: 'login.html',
                controller: 'LoginController'
            });

    });
