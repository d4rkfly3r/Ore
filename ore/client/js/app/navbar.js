angular.module('ore.app')
    .controller('NavbarController', function (User, $scope) {
        $scope.user = User.current();
        $scope.anonymous = User.isAnonymous();
    });
