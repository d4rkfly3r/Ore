(function() {
    var markdownIt = require('markdown-it')('commonmark');
    var markdownItEmoji = require('markdown-it-emoji');
    var sanitizeHtml = require('sanitize-html');

    markdownIt.use(markdownItEmoji);

    markdownIt.renderer.rules.emoji = function(token, idx) {
        var m = token[idx].markup;
        return '<img src="//cdn.spongepowered.org/images/emoji/emoji_one/'+m+'.png?v=1" title=":'+m+':" class="emoji" alt=":'+m+':">';
    };

    var renderMarkdown = function renderMarkdown(txt, options) {
        var output = markdownIt.render(txt, options);

        output = sanitizeHtml(output, {
            allowedTags: ['pre', 'code', 'ul', 'ol', 'li', 'p', 'blockquote', 'hr', 'em', 'strong', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'img', 'br', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'caption', 'strike', 'b', 'u', 'i'],
            allowedAttributes: {
                a: ['href', 'name', 'target'],
                img: ['src', 'title', 'alt', 'class'],
            },
            transformTags: {
                'img': function(tagName, attribs) {
                    var newAttribs = {};

                    var allowedAttribs = ['src', 'title', 'alt'];
                    for (var i = 0; i < allowedAttribs.length; i++) {
                        var allowedAttrib = allowedAttribs[i];
                        if (!attribs.hasOwnProperty(allowedAttrib)) {
                            continue;
                        }

                        newAttribs[allowedAttrib] = attribs[allowedAttrib];
                    }

                    if (attribs.class && attribs.class === 'emoji') {
                        newAttribs.class = 'emoji';
                    }

                    return {
                        tagName: 'img',
                        attribs: newAttribs
                    };
                }
            }
        });

        return output;
    };

    if (typeof window !== 'undefined') {
        window.markdown = renderMarkdown;
    }

    return renderMarkdown;
})();