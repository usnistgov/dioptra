// This Software (Dioptra) is being made available as a public service by the
// National Institute of Standards and Technology (NIST), an Agency of the United
// States Department of Commerce. This software was developed in part by employees of
// NIST and in part by NIST contractors. Copyright in portions of this software that
// were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
// to Title 17 United States Code Section 105, works of NIST employees are not
// subject to copyright protection in the United States. However, NIST may hold
// international copyright in software created by its employees and domestic
// copyright (or licensing rights) in portions of software that were assigned or
// licensed to NIST. To the extent that NIST holds copyright in this software, it is
// being made available under the Creative Commons Attribution 4.0 International
// license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
// of the software developed or licensed by NIST.

// ACCESS THE FULL CC BY 4.0 LICENSE HERE:
// https://creativecommons.org/licenses/by/4.0/legalcode

// This software is a fork of https://github.com/usnistgov/leaveNotice that has been
// edited to be compatible with jQuery 3.0.
(function ($) {
  $.fn.leaveNotice = function (opt) {
    var defaults = {
      siteName: "NIST",
      exitMessage: "<h2><strong>Thank you for visiting {SITENAME}.</strong></h2><p>We hope your visit was informative.</p><p>We have provided this link to a non-NIST site because it has information that may be of interest to our users. NIST does not necessarily endorse the views expressed or the facts presented on this site. Further, NIST does not endorse any commercial products that may be advertised or available on this site.</p>",
      preLinkMessage: "<div class='setoff'><p>You will now be directed to:<br/>{URL}</p></div>",
      linkString: "",
      newWindow: false,
      timeOut: 1e4,
      overlayId: "ln-blackout",
      messageBoxId: "ln-messageBox",
      messageHolderId: "ln-messageHolder",
      linkId: "ln-link",
      displayUrlLength: 50,
      overlayAlpha: .3
    };
    var options = $.extend(defaults, opt);
    return this.each(function () {
      el = $(this);
      var url = el.attr("href");
      var ulen = options.displayUrlLength;
      if (url.length >= ulen) {
        var suffix = "..."
      } else {
        var suffix = ""
      }
      var shortUrl = url.substr(0, ulen) + suffix;
      var title = el.attr("title");
      if (title === undefined || title == "") {
        var linkText = shortUrl
      } else {
        var linkText = title
      }
      options.timeOut = options.newWindow ? 0 : options.timeOut;
      el.click(function () {
        $("body").append('<div id="' + options.overlayId + '"></div>');
        $("body").append('<div id="' + options.messageHolderId + '"><div id="' + options.messageBoxId + '"></div></div>');
        if (options.overlayAlpha !== false) {
          $("#" + options.overlayId).css("opacity", options.overlayAlpha)
        }
        preFilteredContent = options.exitMessage + options.preLinkMessage;
        msgContent = preFilteredContent.replace(/\{URL\}/g, '<a id="' + options.linkId + '" href="' + url + '" title="' + url + '"' + options.linkString + ">" + linkText + "</a>");
        msgContent = msgContent.replace(/\{SITENAME\}/g, options.siteName);
        if (options.timeOut > 0) {
          msgContent += '<p id="ln-cancelMessage"><a href="#close" id="ln-cancelLink">Cancel</a> or press the ESC key.</p>'
        } else {
          msgContent += '<p id="ln-cancelMessage">Click the link above to continue or <a href="#close" id="ln-cancelLink">Cancel</a></p>'
        }
        $("#" + options.messageBoxId).append(msgContent);
        if (options.timeOut > 0) {
          leaveIn = setTimeout(function () {
            $("#ln-cancelMessage").html("<em>Loading...</em>");
            window.location.href = url
          }, options.timeOut)
        } else {
          leaveIn = false
        }
        if (options.newWindow) {
          $("a#" + options.linkId).attr("target", "_blank").click(function () {
            closeDialog(options, leaveIn)
          })
        }
        $("#ln-cancelLink").click(function () {
          closeDialog(options, leaveIn);
          return false
        });
        $(document).bind("keyup", function (e) {
          if (e.which == 27) {
            closeDialog(options, leaveIn)
          }
        });
        $(window).on("unload", function () {
          closeDialog(options, leaveIn)
        });
        return false
      })
    })
  };

  function closeDialog(options, timer) {
    if (options.timeOut > 0) {
      clearTimeout(timer)
    }
    $("#" + options.overlayId + ", #" + options.messageHolderId).fadeOut("fast", function () {
      $("#" + options.overlayId + ", #" + options.messageHolderId).remove()
    });
    $(document).unbind("keyup")
  }
})(jQuery);
