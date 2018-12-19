<!--
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile (Webinterface)
#
# Markup für Dateiliste (Aufnahmen)
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------
-->

<script  type="text/javascript">
  getDelButton = function(name) {
    var head =  '<img class = "w3-border" src="images/trash.png" alt="delete" onClick="doDelDatei(\'';
    var end  =  '\')">';
    return head + name + end;
  };

  getDldButton = function(name) {
    var head =  '<img class = "w3-border" src="images/download.png" alt="download" onClick="doGetDatei(\'';
    var end  =  '\')">';
    return head + name + end;
  };

  $(document).ready(function() {
      $("#datei_liste").DataTable( {
        select: {style: 'multi'},
        createdRow: function ( row, data, index ) {
            $("td:nth-child(3)", row).attr("title", "Erstellt: " + data.DATUMDATEI);
            $("td:nth-child(6)", row).attr("title", data.BESCHREIBUNG);
        },
        language: {
          "sEmptyTable":      "Keine Daten in der Tabelle vorhanden",
          "sInfo":            "_START_ bis _END_ von _TOTAL_ Einträgen",
          "sInfoEmpty":       "0 bis 0 von 0 Einträgen",
          "sInfoFiltered":    "(gefiltert von _MAX_ Einträgen)",
          "sInfoPostFix":     "",
          "sInfoThousands":   ".",
          "sLengthMenu":      "_MENU_ Einträge anzeigen",
          "sLoadingRecords":  "Wird geladen...",
          "sProcessing":      "Bitte warten...",
          "sSearch":          "Suchen",
          "sZeroRecords":     "Keine Einträge vorhanden.",
          "oPaginate": {
              "sFirst":       "Erste",
              "sPrevious":    "Zurück",
              "sNext":        "Nächste",
              "sLast":        "Letzte"
          },
          "oAria": {
              "sSortAscending":  ": aktivieren, um Spalte aufsteigend zu sortieren",
              "sSortDescending": ": aktivieren, um Spalte absteigend zu sortieren"
          }
        },
        columns: [
            { data: null,    title: "",
              className: "dt-right",
              render: function(data,type,raw,meta) {
                   return getDelButton(data.DATEINAME);
              }
             },
            { data: null,    title: "",
              className: "dt-right",
              render: function(data,type,raw,meta) {
                   return getDldButton(data.DATEINAME);
              }
             },
            { data: "DATEI",  title: "Dateiname" },
            { data: "SENDER", title: "Sender" },
            { data: "DATUMFILM", title: "Datum" },
            { data: "TITEL", title: "Titel" }
        ]
      });
  });
</script>


<div id="content_dateien" class="content">

  <h2>Dateien</h2>
  <div  style="margin-bottom: 50px;" class="pure-button-group" role="group" aria-label="Optionen">
    <button onClick="showPart('#content_suche')" class="pure-button">Zurück</button>
  </div>

  <table id="datei_liste" class="display compact nowrap"
         width="100%" cellspacing="0"></table>
</div>
