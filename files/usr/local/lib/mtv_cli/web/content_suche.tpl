<!--
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile (Webinterface)
#
# Markup für Filmsuche
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------
-->

<div id="content_suche" class="content">

<form class="pure-form pure-form-aligned">
    <fieldset>
        <div class="pure-control-group">
            <label for="global">Global</label>
            <input id="global" type="text" placeholder="Globale Suche">
        </div>

        <div class="pure-control-group">
            <label for="sender">Sender</label>
            <input id="sender" type="text" placeholder="Sender">
        </div>

        <div class="pure-control-group">
            <label for="thema">Thema</label>
            <input id="thema" type="text" placeholder="Thema">
        </div>

        <div class="pure-control-group">
            <label for="datum">Datum</label>
            <input id="datum" type="text" placeholder="Datum">
        </div>

        <div class="pure-control-group">
            <label for="titel">Titel</label>
            <input id="titel" type="text" placeholder="Titel">
        </div>

        <div class="pure-control-group">
            <label for="beschreibung">Beschreibung</label>
            <input id="beschreibung" type="text" placeholder="Beschreibung">
        </div>

         <div class="pure-controls">
            <button type="submit" 
                class="pure-button pure-button-primary">Suchen</button>
            </div>
         </div>
    </fieldset>
</form>

</div>
