angular.module('ore.app')
    .controller('BaseController', function (User, $scope) {
        $scope.user = User.current();
        $scope.anonymous = User.isAnonymous();
    });
