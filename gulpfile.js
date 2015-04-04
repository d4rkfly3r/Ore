var gulp = require('gulp');
var uglify = require('gulp-uglify');
var minifyCss = require('gulp-minify-css');
var babel = require('gulp-babel');
var concat = require('gulp-concat');
var filter = require('gulp-filter');
var urlAdjust = require('gulp-css-url-adjuster');
var templateCache = require('gulp-angular-templatecache');
var ngAnnotate = require('gulp-ng-annotate');

var mergeStream = require('merge-stream');
var mainBowerFiles = require('main-bower-files');
var del = require('del');

gulp.task('clean', function (cb) {
    del([
        'ore/static/**/*'
    ], cb)
});

gulp.task('vendor:js', function () {
    return gulp.src(mainBowerFiles('**/*.js'))
        .pipe(concat('vendor.js'))
        .pipe(gulp.dest('ore/static/js/'));
});

gulp.task('vendor:css', function () {

    var entypo = filter(['entypo.*']);

    return gulp.src(mainBowerFiles('**/*.css'))
        .pipe(entypo)
        .pipe(urlAdjust({
            prepend: '../fonts/'
        }))
        .pipe(entypo.restore())
        .pipe(concat('vendor.css'))
        .pipe(gulp.dest('ore/static/css/'));
});

gulp.task('vendor:fonts', function () {
    return gulp.src(mainBowerFiles(['**/*.svg', '**/*.eot', '**/*.ttf', '**/*.woff', '**/*.woff2']))
        .pipe(gulp.dest('ore/static/fonts/'));
});

gulp.task('vendor', ['vendor:js', 'vendor:css', 'vendor:fonts']);

gulp.task('app:js', function () {

    var js = gulp.src(['ore/client/js/ore.js', 'ore/client/js/**/*.js'])
        .pipe(ngAnnotate());

    var templates = gulp.src('ore/client/templates/**/*.html')
        .pipe(templateCache({
            standalone: true
        }));

    return mergeStream(templates, js)
        .pipe(concat('app.js'))
        .pipe(babel())
        .pipe(gulp.dest('ore/static/js/'));
});

gulp.task('app:css', function () {

});

gulp.task('app', ['app:js', 'app:css']);

gulp.task('build', ['vendor', 'app']);

gulp.task('dist:js', ['vendor:js', 'app:js'], function () {
    return gulp.src('ore/static/js/*.js')
        .pipe(uglify())
        .pipe(gulp.dest('ore/static/js'));
});

gulp.task('dist:css', ['vendor:css', 'app:css'], function () {
    return gulp.src('ore/static/css/*.css')
        .pipe(minifyCss())
        .pipe(gulp.dest('ore/static/css'));
});

gulp.task('dist', ['build', 'dist:js', 'dist:css']);

gulp.task('dev', ['build'], function () {
    gulp.watch('bower_components/**/*', ['vendor:js', 'vendor:css']);
    gulp.watch('ore/client/**/*', ['app:js', 'app:css']);
});

gulp.task('default', ['dev']);
