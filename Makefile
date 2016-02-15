all: ore/core/static/ore/js/markdown.built.js

node_modules/.bin/browserify:
	npm install browserify

ore/core/static/ore/js/markdown.built.js: node_modules/.bin/browserify ore/core/static/ore/js/markdown.js
	node_modules/.bin/browserify ore/core/static/ore/js/markdown.js -o ore/core/static/ore/js/markdown.built.js

clean:
	rm -rf ore/core/static/ore/js/markdown.built.js
