angular.module('ore')
    .config(function (RestangularProvider) {
        RestangularProvider.setRequestSuffix('/');
    })
