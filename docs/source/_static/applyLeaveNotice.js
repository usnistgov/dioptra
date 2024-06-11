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
(function ($) {
  $(document).ready(function () {
    // Mark external (non-nist.gov) A tags with class "external"
    // If the address starts with https and ends with nist.gov
    var re_nist = new RegExp('^https?:\/\/((^\/)*\.)*nist\\.gov(\/|$)');
    // Regex to find address that start with https
    var re_absolute_address = new RegExp('^((https?:)?\/\/)');
    $("a").each(function () {
      var url = $(this).attr('href');
      if (re_nist.test(url) || !re_absolute_address.test(url)) {
        $(this).addClass('local');
      } else {
        //This a href appears to be external, so tag it
        $(this).addClass('external');
      }
    });
    // Add leaveNotice to external A elements
    $('a.external').leaveNotice({
      siteName: "Dioptra Documentation"
    });
  });
})(jQuery);
