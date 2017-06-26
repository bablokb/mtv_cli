<!--
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile (Webinterface)
#
# Markup für Filme (Suchergebnis)
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
      $("#film_liste").DataTable( {
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
            { data: "SENDER", title: "Sender" },
            { data: "THEMA", title: "Thema" },
            { data: "DATUM", title: "Datum" },
            { data: "DAUER", title: "Dauer" },
            { data: "TITEL", title: "Titel" }
        ]
      });
  });
</script>


<div id="content_filme" class="content">

  <h2>Filmliste</h2>
  <div  style="margin-bottom: 50px;" class="pure-button-group" role="group" aria-label="Optionen">
    <button onClick="saveSelected()" class="pure-button  pure-button-primary
                   pure-button-active">Vormerken</button>
    <button onClick="showPart('#content_suche')" class="pure-button">Zurück</button>
  </div>

  <table id="film_liste" class="display compact nowrap"
         width="100%" cellspacing="0"></table>
</div>
