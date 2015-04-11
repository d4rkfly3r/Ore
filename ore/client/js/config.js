angular.module('ore')
    .config(function (RestangularProvider) {
        RestangularProvider.setRequestSuffix('/');
    })
    .config(function($httpProvider) {
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    });
