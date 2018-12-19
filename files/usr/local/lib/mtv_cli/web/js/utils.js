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
           "#content_liste",
           "#content_dateien",
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
  Downloads suchen
*/

sucheDownloads=function() {
  $.ajax({
    type: "POST",
    cache: false,
    url: "/downloads",
    success: function(data){
      showPart("#content_liste");
      var table = $('#vormerk_liste').DataTable();
      table.clear();
      table.rows.add(data).draw();
    }
  });
   return false;
};

/**
  Dateiliste anzeigen
*/

showDateien=function() {
  $.ajax({
    type: "POST",
    cache: false,
    url: "/dateien",
    success: function(data){
      showPart("#content_dateien");
      var table = $('#datei_liste').DataTable();
      table.clear();
      table.rows.add(data).draw();
    }
  });
   return false;
};

/**
  Datei auf dem Server löschen
*/

doDelDatei=function(name) {
  $.ajax({
    type: "POST",
        data : {name: name},
    cache: false,
    url: "/del_datei",
    success: function(data){
      showMsg(data.msg,3000);
      var table = $('#datei_liste').DataTable();
      // Zeile entfernen table.rows.add(data).draw();
    },
    error: function(data){
      showMsg(data.msg,3000);
  },
  });
};

/**
  Datei vom Server herunterladen
*/

doGetDatei=function(name) {
  window.location="/get_datei?name="+name;
};

/**
  Filme sofort herunterladen
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
  Ausgewählte Einträge löschen
*/

deleteSelected=function() {
  var table = $('#vormerk_liste').DataTable();
  var auswahl = table.rows({selected: true}).data();
  var ids, dates;

  // ID aus ausgewählten Zeilen extrahieren ...
  for (i=0; i< auswahl.length; ++i) {
    if (ids) {
      ids = ids + " " + auswahl[i]._ID;
    } else {
      ids = auswahl[i]._ID;
    }
  }

  // .. und posten
  $.ajax({
    type: "POST",
        data : {ids:ids},
    cache: false,
    url: "/loeschen",
    success: function(data){
        showMsg(data.msg,3000);
        sucheDownloads();
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

