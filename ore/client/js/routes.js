angular.module('ore')
    .config(function ($locationProvider) {
        $locationProvider.html5Mode(true);
    })
    .config(function ($stateProvider, $urlRouterProvider) {

        $stateProvider
            .state('app', {
                abstract: true,
                templateUrl: 'base.html',
                controller: 'BaseController'
            })
            .state('app.home', {
                url: '/',
                templateUrl: 'home.html'
            });

        var x = y => y;

    });
