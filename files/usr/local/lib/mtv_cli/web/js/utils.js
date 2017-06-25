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
  Sichtbarkeit der Abschnitte steuern.
 */
showPart=function(id) {
  parts = [
           "#content_suche",
           "#content_filme",
           "#content_status"
           ];
  parts.forEach(function(part) {
      if (part == id) {
        $(part).show();
      } else {
        $(part).hide();
      }
    });
}

/**
  Filme suchen
*/

sucheFilme=function() {
  $.ajax({
    type: "POST",
    data : $("#form_suche").serialize(),
    cache: false,
    url: "/suche",
    success: function(data){
      showPart("#content_filme");
      var table = $('#film_liste').DataTable();
      table.clear();
      table.rows.add(data).draw();
    }
  });
   return false;
};

/**
  Filmliste aktualisieren
*/

updateListe=function() {
  $.ajax({
    type: "GET",
    cache: false,
    url: "/aktualisieren",
    success: function(data){
        showMsg(data.msg,3000);
    }
  });
   return false;
};

/**
  Status anzeigen
*/

showStatus=function() {
    $.getJSON("/status", function( data ) {
        showPart("#content_status");
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

