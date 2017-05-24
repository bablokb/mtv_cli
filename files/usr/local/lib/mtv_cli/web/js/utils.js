// ---------------------------------------------------------------------------
// JS support functions.
//
// Author: Bernhard Bablok
// License: GPL3
//
// Website: https://github.com/bablokb/pi-imgtank
//
// ---------------------------------------------------------------------------

/**
  Status abfragen
*/

getStatus=function() {
    $.getJSON("/status", function( data ) {
        console.error("data: ",data);
      $("#status_akt").text(data._akt);
      $("#status_anzahl").text(data._anzahl);
    });
};

/**
  Show message in message-area
*/

showMsg=function(text,time) {
  $("#msgarea").html("<div class='msg_info'>"+text+"</div><br>");
  setTimeout(function() {
               $("#msgarea").empty();
             }, time);
};

/**
  Handle action shutdown
*/

handleShutdown=function() {
  $.post("php/shutdown.php");
  showMsg("Shutting the system down...",2000);
};

/**
  Handle action reboot
*/

handleReboot=function() {
  $.post("php/reboot.php");
  showMsg("Rebooting the system down...",2000);
};

/**
 * Handle author info.
 */

function onAuthorClicked() {
  showMsg("Copyright Bernhard Bablok, bablokb@gmx.de",3000);
}

/**
 * Handle license info.
 */

function onLicenseClicked() {
  showMsg("Unless otherwise noted, the code of this project is realeased under the GPL3",3000);
}

