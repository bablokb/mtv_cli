<!--
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile (Webinterface)
#
# Markup für Vormerkliste
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------
-->

<script  type="text/javascript">
  $(document).ready(function() {
      $("#vormerk_liste").DataTable( {
        select: true,
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
            { data: "STATUS", title: "Status" },
            { data: "DATUMSTATUS", title: "S-Datum" },
            { data: "SENDER", title: "Sender" },
            { data: "THEMA", title: "Thema" },
            { data: "DATUM", title: "Datum" },
            { data: "DAUER", title: "Dauer" },
            { data: "TITEL", title: "Titel" }
        ]
      });
  });
</script>


<div id="content_liste" class="content">

  <h2>Vormerkliste</h2>
  <div  style="margin-bottom: 50px;" class="pure-button-group" role="group" aria-label="Optionen">
    <button onClick="deleteSelected()" class="pure-button  pure-button-primary
                   pure-button-active">Eintrag löschen</button>
    <button onClick="showPart('#content_status')" class="pure-button">Zurück</button>
  </div>

  <table id="vormerk_liste" class="display compact nowrap"
         width="100%" cellspacing="0"></table>
</div>
