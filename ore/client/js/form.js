angular.module('ore.app')
    .directive('errors', function () {
        return {
            restrict: 'A',
            require:  '^form',
            link: function (scope, el, attrs, formCtrl) {
                var inputEl = angular.element(el[0].querySelector("[name]"));
                var inputName = inputEl.attr('name');

                inputEl.bind('blur', function() {
                    el.toggleClass('has-error', formCtrl[inputName].$invalid);
                })
            }
        }
    });
