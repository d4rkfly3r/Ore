(function () {
  // taken from https://docs.djangoproject.com/en/dev/ref/csrf/#ajax

  var csrfSafeMethod = function (method) {
      // these HTTP methods do not require CSRF protection
      return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  };

  var csrftoken = "{{ csrf_token }}";

  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrftoken);
          }
      }
  });

})();


jQuery(function ($) {
  var toggled;

  var drop = function () {
    if(toggled) {
      var $toggled = $(toggled);
      $toggled
        .removeClass('dropped')
        .find('.dropdown')
          .css('display', 'none');
    }
  };

  var show = function () {
    if(toggled) {
      var $toggled = $(toggled);
      $toggled
        .addClass('dropped')
        .find('.dropdown')
          .css('display', 'block');
    }
  };

  $('.dropdown-menu')
    .on('click', function (e) {
      e.stopPropagation();
      if (toggled === this) {
        drop();
        toggled = null;
      } else {
        drop();
        toggled = this;
        show();
      }
    })
    .on('click', function () {
      if(toggled && toggled !== this) {
        drop();
        toggled = this;
        show();
      }
    });

  $('html').on('click', function () {
    drop();
    toggled = null;
  })

  /**
   * This provides a "lockable" form, which disables button(s) until a
   * certain input is provided. It looks for elements with the class
   * js-lock-form, and expects to find the following properties:
   *
   *  - data-confirm should be the string you want the user to verify.
   *  - data-input should be the input box to "watch" for verification.
   *  - data-locks should be elements which are disabled until the
   *               input value matches the confirmation.
   *
   */
  $('.js-lock-form').each(function () {
    var $form = $(this);
    var $input = $form.find($form.data('input'));
    var $locks = $form.find($form.data('locks'));
    var confirm = $form.data('confirm');

    function checkLock () {
      $locks.prop('disabled', $input.val() !== confirm);
    }

    $input.on('input', checkLock);
    checkLock();
  });

  $(function () {
    $('[data-toggle="tooltip"]').tooltip({
      container: 'body'
    })
  });

  /**
   * This provides a "croppable" form, where a modal dialog
   * is displayed if the image provided is not of a certain aspect ratio.
   * It looks for elements with the class js-crop-field, and expects
   * to find the following:
   *
   *  - data-width-field should be selector of the crop-width input
   *  - data-height-field should be selector of the crop-height input
   *  - data-x-field should be selector of the crop-x input
   *  - data-y-field should be selector of the crop-x input
   *  - data-aspect-ratio should be width/height
   *  - data-max-width should be max width
   *  - data-max-height should be max height
   *
   * Note that the actual cropping itself is performed server-side - no
   * cropping is actually done on the client, and the entire image is still
   * transferred (at the moment).
   */
   $('.js-crop-field').each(function () {
    var $avatar = $(this);
    var $form = $avatar.closest('form');
    var $inputs = {
      width: $form.find($avatar.data('width-field')),
      height: $form.find($avatar.data('height-field')),
      x: $form.find($avatar.data('x-field')),
      y: $form.find($avatar.data('y-field')),
    };
    var $formGroup = $avatar.closest('.form-group');
    var $err = null;
    var $cropperDiv = null;
    var avatarImg = null;
    var desiredAspectRatio = (+$avatar.data('aspect-ratio')) || 1;
    var maxWidth = ~~$avatar.data('max-width') || null;
    var maxHeight = ~~$avatar.data('max-height') || null;

    $avatar.change(function() {
      var avatarFile, avatarImg;
      if (!(avatarFile = $avatar.get()[0].files[0])) {
        // blergh
        return;
      }

      if ($err) {
        $err.detach();
        $err = null;
      }
      if ($formGroup.hasClass('has-error')) {
        $formGroup.removeClass('has-error');
      }

      if (avatarImg) {
        $(avatarImg).cropper('destroy');
        avatarImg = null;
      }

      if (!$cropperDiv) {
        $cropperDiv = $('<div></div>');
        $avatar.after($cropperDiv);
      } else {
        $cropperDiv.empty();
      }

      avatarImg = new Image();
      avatarImg.onload = function() {
        if ((maxWidth && avatarImg.width > maxWidth) || (maxHeight && avatarImg.height > maxHeight)) {
          var err = 'This image is too large - images can be at most 800x800 pixels.';
          $cropperDiv.empty();
          $formGroup.addClass('has-error');
          $err = $('<span class="help-block"><strong>' + err + '</strong></span>');
          $avatar.after($err);
          avatarImg = null;
          return;
        }

        $cropperDiv.append(avatarImg);
        $(avatarImg).cropper({
          aspectRatio: desiredAspectRatio,
          movable: false,
          scalable: false,
          zoomable: false,
          rotatable: false,
          viewMode: 1,
          crop: function(ev) {
            $inputs.width.val(Math.round(ev.width));
            $inputs.height.val(Math.round(ev.height));
            $inputs.x.val(Math.round(ev.x));
            $inputs.y.val(Math.round(ev.y));
          }
        });
      };
      avatarImg.src = window.URL.createObjectURL(avatarFile);

    });
   });

  var toShowModals = $('[data-show-modal-immediately="true"]');
  if (toShowModals.length > 1) {
    console.error("Multiple modals with data-show-modal-immediately attribute detected!");
    toShowModals = toShowModals.first();
  }
  toShowModals.removeClass('fade').on('shown.bs.modal', function() {
    toShowModals.addClass('fade');
  }).modal('show');

  if ($('.colour-selector').length) {
    (function() {
      function parseColor(color) {
        // thanks, http://stackoverflow.com/a/19366217/1189905
        color = color.trim().toLowerCase();
        var hex3 = color.match(/^#([0-9a-f]{3})$/i);
        if (hex3) {
          hex3 = hex3[1];
          return [
            parseInt(hex3.charAt(0),16)*0x11,
            parseInt(hex3.charAt(1),16)*0x11,
            parseInt(hex3.charAt(2),16)*0x11, 1
          ];
        }
        var hex6 = color.match(/^#([0-9a-f]{6})$/i);
        if (hex6) {
          hex6 = hex6[1];
          return [
            parseInt(hex6.substr(0,2),16),
            parseInt(hex6.substr(2,2),16),
            parseInt(hex6.substr(4,2),16), 1
          ];
        }
        var rgba = color.match(/^rgba\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+.*\d*)\s*\)$/i) || color.match(/^rgba\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/i);
        if( rgba ) {
          return [rgba[1],rgba[2],rgba[3], rgba[4]===undefined?1:rgba[4]];
        }
        var rgb = color.match(/^rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/i);
        if( rgb ) {
          return [rgb[1],rgb[2],rgb[3],1];
        }
      }

      var calculateLuminance = function(color) {
        var color = parseColor(color).map(function(v) { return v / 255; });
        return perceptiveLuminance = (0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]);
      }

      var isLight = function(color) {
        return calculateLuminance(color) > 0.5;
      }

      var updateSelection = function(colour) {
        var textColor = '#fff';
        if (isLight(colour)) {
          textColor = '#000';
        }
        $('#id_name').css({
          backgroundColor: colour,
          color: textColor,
        });
      };

      var $select = $('.colour-selector');
      $select.addClass('hide');
      if ($select.find('option').length == 0) {
        $select.after($('<div>There are no colours left. You used them all. How could you possibly need that many channels?!?</div>'))
      } else {
        var $prettySelect = $('<div></div>');
        $select.after($prettySelect);
        $select.find('option').each(function() {
          var $option = $(this);
          var $prettyOption =
            $('<div></div>')
              .attr({
                class: 'colour-selector-dot' + ($select.val() == $option.val() ? ' colour-selector-dot-active' : '') + (isLight('#' + $option.val()) ? ' colour-selector-dot-light' : ' colour-selector-dot-dark')
              })
              .css({
                backgroundColor: '#' + $option.val(),
              })
              .click(function() {
                $select.val($option.val());
                $prettySelect.find('.colour-selector-dot-active').removeClass('colour-selector-dot-active');
                $prettyOption.addClass('colour-selector-dot-active');
                updateSelection('#' + $option.val());
              })
              .appendTo($prettySelect);
        });
        updateSelection('#' + $select.val());
      }
    })();
  }



  $('.oredown').each(function() {
    var $this = $(this);
    $this.wrap('<div class="oredown-container row"></div>');
    var $outer = $this.parent('.oredown-container');
    $this.wrap('<div class="oredown-textarea-container col-md-6"></div>');
    var $preview = $('<div class="oredown-preview col-md-6"></div>');
    $outer.append($preview);

    var scrollPreview = function() {
      $preview.scrollTop($this.scrollTop());
    };

    var updatePreview = function() {
      var content = $this.val();
      $preview.html(window.markdown(content));
      scrollPreview();
    };
    updatePreview();

    $this.change(updatePreview).blur(updatePreview).keydown(updatePreview).keyup(updatePreview);
    $this.scroll(scrollPreview);
  });
});
