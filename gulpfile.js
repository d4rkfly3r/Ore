var gulp = require('gulp');
var uglify = require('gulp-uglify');
var babel = require('gulp-babel');
var concat = require('gulp-concat');
var templateCache = require('gulp-angular-templatecache');

var mergeStream = require('merge-stream');

gulp.task('build', function () {

    var js = gulp.src('ore/client/js/**/*.js')
        .pipe(babel());
    var templates = gulp.src('ore/client/templates/**/*.html')
        .pipe(templateCache());

    return mergeStream(js, templates)
        .pipe(concat('app.js'))
        .pipe(gulp.dest('ore/static/js/'));
});
