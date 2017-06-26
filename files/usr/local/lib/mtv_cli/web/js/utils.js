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
  Ausgewählte Filme vormerken
*/

saveSelected=function() {
  var table = $('#film_liste').DataTable();
  var auswahl = table.rows({selected: true}).data();
  var ids, dates;

  // ID und Datum aus ausgewählten Zeilen extrahieren ...
  for (i=0; i< auswahl.length; ++i) {
    if (ids) {
      ids = ids + " " + auswahl[i]._ID;
    } else {
      ids = auswahl[i]._ID;
    }
    if (dates) {
      dates = dates + " " + auswahl[i].DATUM;
    } else {
      dates = auswahl[i].DATUM;
    }
  }

  // .. und posten
  $.ajax({
    type: "POST",
        data : {ids:ids, dates: dates},
    cache: false,
    url: "/vormerken",
    success: function(data){
        showMsg(data.msg,3000);
    }
  });
  return false;
};

/**
  Filmliste aktualisieren
*/

downloadFilme=function() {
  $.ajax({
    type: "GET",
    cache: false,
    url: "/download",
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

