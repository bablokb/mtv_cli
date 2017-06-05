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
  <table id="film_liste" class="display" width="100%"></table>
</div>
