angular.module('ore.user', []);

angular.module('ore.namespace', []);

angular.module('ore.app', []);

angular.module('ore', ['ore.user', 'ore.app', 'ui.router', 'restangular', 'templates']);
